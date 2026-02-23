"""Qt bridge for Python logging records."""

import logging
import time
from collections.abc import Callable
from typing import Any


class QtSignalLogHandler(logging.Handler):
    """Forward log records to a Qt signal callback."""

    def __init__(self, emit_callback: Callable[[dict[str, Any]], None]):
        super().__init__()
        self._emit_callback = emit_callback

    def emit(self, record: logging.LogRecord) -> None:
        try:
            payload = {
                "created": record.created,
                "time": time.strftime("%H:%M:%S", time.localtime(record.created)),
                "level": record.levelname,
                "logger": record.name,
                "thread": record.threadName,
                "task_name": getattr(record, "task_name", "-"),
                "message": record.getMessage(),
                "formatted": self.format(record),
            }
            self._emit_callback(payload)
        except Exception:
            self.handleError(record)


__all__ = [
    "QtSignalLogHandler",
]
