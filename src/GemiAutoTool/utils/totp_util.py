# GemiAutoTool/utils/totp_util.py

import pyotp


class TOTPUtil:
    """
    处理 2FA (TOTP) 身份验证码的工具类
    """

    @staticmethod
    def generate_code(secret_key: str) -> str:
        """
        根据 2FA 密钥生成实时的 6 位数验证码

        :param secret_key: 账号的 2FA 密钥
        :return: 6 位数的验证码字符串，如果出错则返回空字符串
        """
        if not secret_key:
            return ""

        try:
            # 去除密钥中可能带有的空格，并转换为大写（pyotp 标准要求）
            clean_secret = secret_key.replace(" ", "").upper()

            # 实例化 TOTP 对象
            totp = pyotp.TOTP(clean_secret)

            # 获取当前的动态验证码
            return totp.now()

        except Exception as e:
            print(f"⚠️ 生成 2FA 验证码时发生错误: {e}")
            return ""
