"""Unified logging configuration for GemiAutoTool."""

import contextvars
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from GemiAutoTool.config import PROJECT_ROOT

_task_name_var: contextvars.ContextVar[str] = contextvars.ContextVar("task_name", default="-")


class TaskContextFilter(logging.Filter):
    """Inject task_name into all log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.task_name = _task_name_var.get()
        return True


class ColorFormatter(logging.Formatter):
    """Colorize console log output by level."""

    RESET = "\033[0m"
    COLORS = {
        logging.DEBUG: "\033[36m",      # Cyan
        logging.INFO: "\033[32m",       # Green
        logging.WARNING: "\033[33m",    # Yellow
        logging.ERROR: "\033[31m",      # Red
        logging.CRITICAL: "\033[35;1m", # Bold magenta
    }

    def __init__(self, *args, enable_color: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self.enable_color = enable_color

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        if not self.enable_color:
            return message
        color = self.COLORS.get(record.levelno)
        if not color:
            return message
        return f"{color}{message}{self.RESET}"


def set_task_name(task_name: str) -> contextvars.Token[str]:
    return _task_name_var.set(task_name or "-")


def reset_task_name(token: contextvars.Token[str]) -> None:
    _task_name_var.reset(token)


def _parse_bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() not in {"0", "false", "no", "off"}


def _resolve_log_level(env_name: str, default: int) -> int:
    raw = os.getenv(env_name)
    if not raw:
        return default
    if raw.isdigit():
        return int(raw)
    return getattr(logging, raw.strip().upper(), default)


def setup_logging(level: int | str = logging.INFO) -> None:
    """Configure console and rotating file logging once."""
    root_logger = logging.getLogger()
    if getattr(root_logger, "_gemi_logging_configured", False):
        return

    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)

    log_dir = os.getenv("GEMI_LOG_DIR", os.path.join(PROJECT_ROOT, "logs"))
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.getenv("GEMI_LOG_FILE", os.path.join(log_dir, "runtime.log"))

    default_level = level
    if isinstance(default_level, str):
        default_level = getattr(logging, default_level.upper(), logging.INFO)

    console_level = _resolve_log_level("GEMI_LOG_LEVEL", int(default_level))
    file_level = _resolve_log_level("GEMI_LOG_FILE_LEVEL", console_level)
    enable_color = _parse_bool_env("GEMI_LOG_COLOR", sys.stdout.isatty()) and not _parse_bool_env("NO_COLOR", False)

    base_format = (
        "%(asctime)s | %(levelname)-8s | %(threadName)s | task=%(task_name)s | %(name)s | %(message)s"
    )
    file_formatter = logging.Formatter(
        fmt=base_format,
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_formatter = ColorFormatter(
        fmt=base_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        enable_color=enable_color,
    )
    context_filter = TaskContextFilter()

    # Use stdout instead of stderr so terminals/IDEs don't render all logs as "error/red".
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(context_filter)

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=int(os.getenv("GEMI_LOG_MAX_BYTES", str(2 * 1024 * 1024))),
        backupCount=int(os.getenv("GEMI_LOG_BACKUP_COUNT", "5")),
        encoding="utf-8",
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(file_formatter)
    file_handler.addFilter(context_filter)

    root_logger.setLevel(min(console_level, file_level))
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger._gemi_logging_configured = True  # type: ignore[attr-defined]


__all__ = [
    "setup_logging",
    "set_task_name",
    "reset_task_name",
]
