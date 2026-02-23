# 异常处理
# GemiAutoTool/exceptions.py

class GemiAutoToolBaseException(Exception):
    """项目基础异常类，所有自定义异常继承于此"""
    pass

class BrowserInitError(GemiAutoToolBaseException):
    """浏览器初始化/启动失败异常"""
    pass

class AccountLoginFailedError(GemiAutoToolBaseException):
    """账号登录失败异常 (例如密码错误、被风控等)"""
    pass

class TOTPGenerationError(GemiAutoToolBaseException):
    """2FA 验证码生成失败异常"""
    pass