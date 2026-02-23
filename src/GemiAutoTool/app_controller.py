"""Reusable automation orchestration for CLI and GUI entrypoints."""

import concurrent.futures
import logging
import random
import string
import threading
import time
from collections.abc import Callable
from typing import Any

from GemiAutoTool.config import INPUT_DIR, MAX_CONCURRENT_WINDOWS, OUTPUT_DIR
from GemiAutoTool.exceptions import GemiAutoToolBaseException
from GemiAutoTool.services import (
    AccountService,
    InputService,
    PaymentDataService,
    SubscriptionOutputService,
    force_close_all_active_browsers,
)
from GemiAutoTool.tasks import run_browser_task

logger = logging.getLogger(__name__)

ControllerEventCallback = Callable[[str, dict[str, Any]], None]


class AutomationController:
    """Coordinates the end-to-end automation workflow."""

    def __init__(
        self,
        event_callback: ControllerEventCallback | None = None,
        input_dir: str | None = None,
        output_dir: str | None = None,
    ):
        self._event_callback = event_callback
        self._stop_event = threading.Event()
        self._is_running = False
        self._input_dir = input_dir or INPUT_DIR
        self._output_dir = output_dir or OUTPUT_DIR

    @property
    def is_running(self) -> bool:
        return self._is_running

    def stop(self) -> None:
        """Hard stop: stop scheduling new tasks and force-close active browser windows."""
        self._stop_event.set()
        closed = force_close_all_active_browsers()
        logger.warning("收到硬停止请求：停止创建新任务，并强制关闭活动浏览器窗口（已关闭 %s 个）。", closed)
        self._emit("stop_requested", hard=True, force_closed_browsers=closed)

    def set_paths(self, *, input_dir: str | None = None, output_dir: str | None = None) -> None:
        if input_dir:
            self._input_dir = input_dir
        if output_dir:
            self._output_dir = output_dir

    def run(
        self,
        max_concurrent_windows: int | None = None,
        launch_delay_seconds: float = 0.5,
        browser_window_mode: str = "headless",
        retry_emails: list[str] | set[str] | None = None,
    ) -> bool:
        if self._is_running:
            logger.warning("控制器正在运行，忽略重复启动请求。")
            return False

        self._is_running = True
        self._stop_event.clear()
        success = False
        run_finished_emitted = False

        try:
            logger.info("=== GemiAutoTool 自动化系统启动 ===")

            try:
                raw_accounts_text = InputService.read_accounts_text(input_dir=self._input_dir)
            except GemiAutoToolBaseException as e:
                logger.error("启动失败: %s", e)
                self._emit("run_error", message=str(e))
                return False

            if not raw_accounts_text.strip():
                logger.warning("没有读取到账号内容，程序退出。")
                self._emit("run_error", message="没有读取到账号内容")
                return False

            accounts = AccountService.parse_accounts_from_text(raw_accounts_text)
            if not accounts:
                logger.warning("没有可用的账号，程序退出。")
                self._emit("run_error", message="没有可用账号")
                return False

            retry_email_set: set[str] | None = None
            if retry_emails:
                retry_email_set = {str(email).strip().lower() for email in retry_emails if str(email).strip()}
                if retry_email_set:
                    accounts = [acc for acc in accounts if acc.email.strip().lower() in retry_email_set]
                    logger.info("重试模式：筛选后剩余 %s 个账号（请求重试 %s 个邮箱）", len(accounts), len(retry_email_set))
                if not accounts:
                    logger.warning("重试模式下没有匹配到可重试账号。")
                    self._emit("run_error", message="没有匹配到可重试账号（失败任务可能已清空或账号文件已变更）")
                    return False

            output_service = SubscriptionOutputService(output_dir=self._output_dir)
            try:
                payment_data_service = PaymentDataService(input_dir=self._input_dir)
            except GemiAutoToolBaseException as e:
                logger.error("初始化支付数据失败: %s", e)
                self._emit("run_error", message=f"初始化支付数据失败: {e}")
                return False

            max_workers = max(1, int(max_concurrent_windows or MAX_CONCURRENT_WINDOWS))
            planned_task_count = len(accounts)
            logger.info("成功加载 %s 个账号，准备以 %s 并发执行...", planned_task_count, max_workers)
            browser_window_mode = str(browser_window_mode or "headless").strip().lower() or "headless"
            self._emit(
                "run_started",
                total_accounts=len(accounts),
                scheduled_tasks=planned_task_count,
                max_concurrent=max_workers,
                input_dir=self._input_dir,
                output_dir=self._output_dir,
                browser_window_mode=browser_window_mode,
                retry_mode=bool(retry_email_set),
                retry_candidates=len(retry_email_set or []),
            )

            launched_tasks = 0
            next_account_index = 0
            stop_schedule_logged = False
            in_flight: dict[concurrent.futures.Future[None], tuple[int, str, str]] = {}

            def schedule_one(account_index: int, executor: concurrent.futures.ThreadPoolExecutor) -> None:
                nonlocal launched_tasks
                account = accounts[account_index]
                task_name = f"Task_{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}"
                self._emit(
                    "task_scheduled",
                    task_name=task_name,
                    email=account.email,
                    index=account_index,
                )
                future = executor.submit(
                    self._task_runner_wrapper,
                    account,
                    task_name,
                    output_service,
                    payment_data_service,
                    browser_window_mode,
                )
                in_flight[future] = (account_index, task_name, account.email)
                launched_tasks += 1
                if launch_delay_seconds > 0:
                    time.sleep(launch_delay_seconds)

            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                while next_account_index < len(accounts) and len(in_flight) < max_workers and not self._stop_event.is_set():
                    schedule_one(next_account_index, executor)
                    next_account_index += 1

                while in_flight:
                    done, _ = concurrent.futures.wait(
                        in_flight.keys(),
                        timeout=0.2,
                        return_when=concurrent.futures.FIRST_COMPLETED,
                    )

                    for future in done:
                        _, task_name, email = in_flight.pop(future)
                        try:
                            future.result()
                        except Exception as e:  # Defensive: _task_runner_wrapper should catch task errors.
                            logger.exception("任务 Future 出现未捕获异常 [%s/%s]: %s", task_name, email, e)

                    if self._stop_event.is_set() and next_account_index < len(accounts) and not stop_schedule_logged:
                        logger.warning(
                            "检测到停止请求，停止继续创建任务（剩余 %s 个账号未启动）。",
                            len(accounts) - next_account_index,
                        )
                        stop_schedule_logged = True

                    while (
                        next_account_index < len(accounts)
                        and len(in_flight) < max_workers
                        and not self._stop_event.is_set()
                    ):
                        schedule_one(next_account_index, executor)
                        next_account_index += 1

            logger.info("=== 所有自动化任务已全部结束 ===")
            self._emit(
                "run_finished",
                launched_tasks=launched_tasks,
                stopped=self._stop_event.is_set(),
            )
            run_finished_emitted = True
            success = True
            return True
        finally:
            self._is_running = False
            self._stop_event.clear()
            if not run_finished_emitted:
                self._emit("run_finished", launched_tasks=0, stopped=False)

    def _task_runner_wrapper(self, account, task_name, output_service, payment_data_service, browser_window_mode: str) -> None:
        self._emit("task_started", task_name=task_name, email=account.email)
        business_result: dict[str, Any] | None = None

        def on_task_event(event_type: str, payload: dict[str, Any]) -> None:
            nonlocal business_result
            if event_type == "progress":
                self._emit(
                    "task_progress",
                    task_name=task_name,
                    email=account.email,
                    stage=payload.get("stage", ""),
                    detail=payload.get("detail", ""),
                )
            elif event_type == "business_result":
                business_result = dict(payload)
                self._emit(
                    "task_business_result",
                    task_name=task_name,
                    email=account.email,
                    **payload,
                )

        try:
            result_summary = run_browser_task(
                account,
                task_name,
                output_service,
                payment_data_service,
                browser_window_mode=browser_window_mode,
                event_callback=on_task_event,
            )
            if business_result is None and isinstance(result_summary, dict):
                business_result = result_summary
                self._emit(
                    "task_business_result",
                    task_name=task_name,
                    email=account.email,
                    **result_summary,
                )
            self._emit(
                "task_finished",
                task_name=task_name,
                email=account.email,
                status="finished",
                result_kind=(business_result or {}).get("result_kind", "unknown"),
                business_status=(business_result or {}).get("business_status", ""),
                detail=(business_result or {}).get("detail", ""),
            )
        except Exception as e:  # Defensive: task function already catches most exceptions.
            logger.exception("任务线程出现未捕获异常: %s", e)
            self._emit(
                "task_finished",
                task_name=task_name,
                email=account.email,
                status="crashed",
                error=str(e),
                result_kind="crashed",
                business_status="线程崩溃",
                detail=str(e),
            )

    def _emit(self, event_type: str, **payload: Any) -> None:
        if not self._event_callback:
            return
        try:
            self._event_callback(event_type, payload)
        except Exception as e:
            logger.debug("事件回调处理失败(event=%s): %s", event_type, e)


__all__ = [
    "AutomationController",
]
