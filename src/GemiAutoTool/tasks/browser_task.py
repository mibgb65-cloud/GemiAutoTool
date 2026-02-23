# GemiAutoTool/tasks/browser_task.py

import logging
from collections.abc import Callable
from typing import Any

from GemiAutoTool.config import DEFAULT_LOGIN_URL
from GemiAutoTool.services import IsolatedBrowser, SubscriptionOutputService
from GemiAutoTool.domain import GoogleAccount, SubscriptionResult
from GemiAutoTool.actions import check_subscription, fill_payment_form, login_google
from GemiAutoTool.exceptions import (
    GemiAutoToolBaseException,
    PaymentDataError,
    PaymentProcessError,
    SubscriptionCheckError,
)
from GemiAutoTool.logging_config import reset_task_name, set_task_name

logger = logging.getLogger(__name__)

TaskEventCallback = Callable[[str, dict[str, Any]], None]


# [修改点] 这里接收了 payment_data_service 参数
def run_browser_task(
    account: GoogleAccount,
    task_name: str,
    output_service: SubscriptionOutputService,
    payment_data_service,
    browser_window_mode: str = "headless",
    event_callback: TaskEventCallback | None = None,
):
    """
    单个浏览器的核心业务执行流
    """
    def emit(event_type: str, **payload: Any) -> None:
        if not event_callback:
            return
        try:
            event_callback(event_type, payload)
        except Exception as e:
            logger.debug("任务事件回调失败(event=%s): %s", event_type, e)

    token = set_task_name(task_name)
    logger.info("开始处理账号: %s", account.email)
    emit("progress", stage="初始化浏览器", detail="开始处理账号")

    browser = IsolatedBrowser(task_name, window_mode=browser_window_mode)
    final_summary = {
        "result_kind": "unknown",
        "business_status": "未完成",
        "detail": "",
        "link": "",
        "login_success": False,
    }
    try:
        driver = browser.start_browser(DEFAULT_LOGIN_URL)
        emit("progress", stage="登录流程", detail="正在登录 Google")

        # 1. 尝试登录
        if login_google(driver, account, task_name):
            final_summary["login_success"] = True
            emit("progress", stage="订阅检测", detail="登录成功，开始检测订阅状态")

            # 2. 登录成功，去检测订阅状态
            try:
                status, link = check_subscription(driver, task_name)
            except SubscriptionCheckError as e:
                status, link = f"订阅检测失败 ({str(e)[:80]})", ""
                logger.warning("%s", e)
                emit("progress", stage="订阅检测", detail=str(e))
            logger.info("初始订阅检测 -> 状态: %s", status)
            emit("progress", stage="订阅检测", detail=f"检测结果: {status}")

            # 3. 支付逻辑分支
            if status == "已认证/未订阅":
                logger.info("需要进行支付验证，正在提取本地支付信息...")
                emit("progress", stage="支付流程", detail="准备支付数据并执行支付")

                try:
                    # 向 PaymentDataService 索取一条组合好的支付信息
                    payment_data = payment_data_service.get_next_payment_info()

                    # 传入数据进行自动填表操作
                    is_paid, pay_msg = fill_payment_form(driver, payment_data, task_name)

                    if is_paid:
                        status = "已订阅"
                    else:
                        status = f"支付失败 ({pay_msg})"
                except PaymentDataError as e:
                    status = "支付失败 (本地数据不完整)"
                    logger.warning("%s", e)
                    emit("progress", stage="支付流程", detail=str(e))
                except PaymentProcessError as e:
                    status = f"支付失败 ({str(e)[:100]})"
                    logger.warning("%s", e)
                    emit("progress", stage="支付流程", detail=str(e))

            # 4. 生成结果实体，写入到 output 文件夹中
            result = SubscriptionResult(email=account.email, status=status, link=link)
            output_service.save_result(result)
            final_summary["business_status"] = status
            final_summary["link"] = link
            if status == "已订阅":
                final_summary["result_kind"] = "success"
                final_summary["detail"] = "订阅成功"
            elif "失败" in status:
                final_summary["result_kind"] = "failed"
                final_summary["detail"] = status
            elif "需验证" in status:
                final_summary["result_kind"] = "needs_verify"
                final_summary["detail"] = status
            else:
                final_summary["result_kind"] = "other"
                final_summary["detail"] = status
            emit(
                "business_result",
                result_kind=final_summary["result_kind"],
                business_status=final_summary["business_status"],
                detail=final_summary["detail"],
                link=final_summary["link"],
            )

        else:
            logger.warning("登录流程失败或中断，跳过后续步骤。")
            final_summary["result_kind"] = "login_failed"
            final_summary["business_status"] = "登录失败"
            final_summary["detail"] = "登录流程失败或中断"
            emit("business_result", **final_summary)

    except GemiAutoToolBaseException as e:
        logger.warning("业务异常: %s", e)
        final_summary["result_kind"] = "failed"
        final_summary["business_status"] = "业务异常"
        final_summary["detail"] = str(e)
        emit("business_result", **final_summary)
    except Exception as e:
        logger.exception("发生全局崩溃性异常: %s", e)
        final_summary["result_kind"] = "crashed"
        final_summary["business_status"] = "线程崩溃"
        final_summary["detail"] = str(e)
        emit("business_result", **final_summary)
    finally:
        browser.close_browser()
        reset_task_name(token)
    return final_summary
