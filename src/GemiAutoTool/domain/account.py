from dataclasses import dataclass

@dataclass
class GoogleAccount:
    """
    Google 账号实体类 (DTO)
    仅用于封装和传递账号的基础数据，不包含任何业务处理逻辑
    """
    email: str            # 账号邮箱 (例如: SommerAhmad909@gmail.com)
    password: str         # 账号密码 (例如: aotngyswz)
    recovery_email: str   # 辅助/恢复邮箱 (例如: SommerAhmad90940105@neiar.xyz)
    two_fa_secret: str    # 2FA 身份验证器密钥 (例如: gt252i...m7me)