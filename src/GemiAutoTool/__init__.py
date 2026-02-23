"""GemiAutoTool package public exports.

顶层包保持轻量导出，避免在 `import GemiAutoTool` 时立即触发浏览器相关依赖加载。
"""

from .exceptions import (
    AccountLoginFailedError,
    AccountParseError,
    BrowserCleanupError,
    BrowserError,
    BrowserInitError,
    GemiAutoToolBaseException,
    InputDataError,
    InputFileNotFoundError,
    InputFileReadError,
    OutputReadError,
    OutputWriteError,
    PaymentDataError,
    PaymentDataIncompleteError,
    PaymentDataParseError,
    PaymentProcessError,
    SubscriptionCheckError,
    TOTPGenerationError,
)

__all__ = [
    "GemiAutoToolBaseException",
    "InputDataError",
    "InputFileNotFoundError",
    "InputFileReadError",
    "OutputReadError",
    "AccountParseError",
    "BrowserError",
    "BrowserInitError",
    "BrowserCleanupError",
    "AccountLoginFailedError",
    "TOTPGenerationError",
    "PaymentDataError",
    "PaymentDataIncompleteError",
    "PaymentDataParseError",
    "SubscriptionCheckError",
    "PaymentProcessError",
    "OutputWriteError",
]
