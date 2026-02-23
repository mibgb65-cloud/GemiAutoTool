# 异常处理
# GemiAutoTool/exceptions.py

class GemiAutoToolBaseException(Exception):
    """项目基础异常类，所有自定义异常继承于此"""
    pass

class InputDataError(GemiAutoToolBaseException):
    """输入数据相关异常"""
    pass


class InputFileNotFoundError(InputDataError):
    """输入文件不存在"""
    pass


class InputFileReadError(InputDataError):
    """输入文件读取失败"""
    pass


class AccountParseError(InputDataError):
    """账号文本解析失败"""
    pass


class BrowserError(GemiAutoToolBaseException):
    """浏览器相关异常"""
    pass


class BrowserInitError(BrowserError):
    """浏览器初始化/启动失败异常"""
    pass


class BrowserCleanupError(BrowserError):
    """浏览器关闭或清理失败异常"""
    pass

class AccountLoginFailedError(GemiAutoToolBaseException):
    """账号登录失败异常 (例如密码错误、被风控等)"""
    pass

class TOTPGenerationError(GemiAutoToolBaseException):
    """2FA 验证码生成失败异常"""
    pass


class PaymentDataError(GemiAutoToolBaseException):
    """支付数据相关异常"""
    pass


class PaymentDataIncompleteError(PaymentDataError):
    """支付数据缺失或数量不足"""
    pass


class PaymentDataParseError(PaymentDataError):
    """支付数据格式解析失败"""
    pass


class SubscriptionCheckError(GemiAutoToolBaseException):
    """订阅状态检测失败"""
    pass


class PaymentProcessError(GemiAutoToolBaseException):
    """支付流程执行失败"""
    pass


class OutputWriteError(GemiAutoToolBaseException):
    """结果文件写入失败"""
    pass


class OutputReadError(GemiAutoToolBaseException):
    """结果文件读取失败"""
    pass
