"""Qt worker objects for running automation in background threads."""

import logging

from PySide6 import QtCore

from GemiAutoTool.app_controller import AutomationController
from GemiAutoTool.logging_config import setup_logging
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


__all__ = [
    "AutomationWorker",
]
