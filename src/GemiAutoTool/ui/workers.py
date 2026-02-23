"""Qt worker objects for running automation in background threads."""

import logging
import threading

from PySide6 import QtCore

from GemiAutoTool.app_controller import AutomationController
from GemiAutoTool.logging_config import setup_logging
from GemiAutoTool.services import SheerIDBotVerifyService
from GemiAutoTool.ui.log_handler import QtSignalLogHandler

logger = logging.getLogger(__name__)


class AutomationWorker(QtCore.QObject):
    """Runs the automation controller in a QThread."""

    log_record = QtCore.Signal(dict)
    controller_event = QtCore.Signal(dict)
    run_started = QtCore.Signal()
    run_finished = QtCore.Signal(dict)
    run_error = QtCore.Signal(str)

    def __init__(
        self,
        max_concurrent: int,
        input_dir: str | None = None,
        output_dir: str | None = None,
        browser_window_mode: str = "headless",
        retry_emails: list[str] | None = None,
        parent: QtCore.QObject | None = None,
    ):
        super().__init__(parent)
        self._max_concurrent = max_concurrent
        self._browser_window_mode = str(browser_window_mode or "headless")
        self._retry_emails = list(retry_emails or [])
        self._controller = AutomationController(
            event_callback=self._emit_controller_event,
            input_dir=input_dir,
            output_dir=output_dir,
        )

    @QtCore.Slot()
    def run(self) -> None:
        setup_logging()

        handler = QtSignalLogHandler(self.log_record.emit)
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(threadName)s | task=%(task_name)s | %(name)s | %(message)s",
                "%Y-%m-%d %H:%M:%S",
            )
        )

        root_logger = logging.getLogger()
        root_logger.addHandler(handler)

        try:
            self.run_started.emit()
            ok = self._controller.run(
                max_concurrent_windows=self._max_concurrent,
                browser_window_mode=self._browser_window_mode,
                retry_emails=self._retry_emails or None,
            )
            self.run_finished.emit({"ok": ok})
        except Exception as e:
            logger.exception("UI 后台任务执行失败: %s", e)
            self.run_error.emit(str(e))
            self.run_finished.emit({"ok": False, "error": str(e)})
        finally:
            root_logger.removeHandler(handler)

    @QtCore.Slot()
    def request_stop(self) -> None:
        self._controller.stop()

    def _emit_controller_event(self, event_type: str, payload: dict) -> None:
        data = {"type": event_type}
        data.update(payload)
        self.controller_event.emit(data)


class VerifyLinkWorker(QtCore.QObject):
    """Submit a SheerID link to SheerIDBot and poll progress in a background thread."""

    progress = QtCore.Signal(dict)
    finished = QtCore.Signal(dict)
    skipped = QtCore.Signal(dict)
    error = QtCore.Signal(str)

    def __init__(
        self,
        *,
        api_key: str,
        verify_url: str,
        parent: QtCore.QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._api_key = str(api_key or "").strip()
        self._verify_url = str(verify_url or "").strip()
        self._stop_event = threading.Event()

    @QtCore.Slot()
    def run(self) -> None:
        if not self._api_key:
            self.skipped.emit({"reason": "missing_api_key", "message": "未填写 API Key，已跳过验证。"})
            return
        if not self._verify_url:
            self.skipped.emit({"reason": "missing_url", "message": "当前未选择有效的认证链接。"})
            return

        try:
            service = SheerIDBotVerifyService(self._api_key)
            self.progress.emit(
                {
                    "phase": "submitting",
                    "status": "submitting",
                    "message": "正在提交验证任务...",
                    "url": self._verify_url,
                }
            )
            submit_data, final_data = service.submit_and_poll(
                self._verify_url,
                progress_callback=self._on_service_progress,
                should_stop=self._stop_event.is_set,
            )
            self.finished.emit(
                {
                    "submit": submit_data,
                    "final": final_data,
                    "job_id": str(final_data.get("job_id") or submit_data.get("job_id") or ""),
                    "status": str(final_data.get("status", "") or ""),
                }
            )
        except Exception as e:
            logger.exception("SheerIDBot 验证任务失败: %s", e)
            self.error.emit(str(e))

    @QtCore.Slot()
    def request_stop(self) -> None:
        self._stop_event.set()

    def _on_service_progress(self, event: dict) -> None:
        progress = event.get("progress") if isinstance(event.get("progress"), dict) else {}
        status = str(event.get("status", "") or "")
        message = str(progress.get("message", "") or "")
        stage = str(progress.get("stage", "") or "")
        stage_number = progress.get("stage_number")
        total_stages = progress.get("total_stages")
        percentage = progress.get("percentage")
        payload = {
            "phase": "polling",
            "event_type": str(event.get("event_type", "")),
            "job_id": str(event.get("job_id", "") or ""),
            "status": status,
            "message": message,
            "stage": stage,
            "stage_number": stage_number,
            "total_stages": total_stages,
            "percentage": percentage,
            "credits_charged": event.get("credits_charged"),
            "result": event.get("result"),
            "raw": event.get("raw"),
        }
        self.progress.emit(payload)


__all__ = [
    "AutomationWorker",
    "VerifyLinkWorker",
]
