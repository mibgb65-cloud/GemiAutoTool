# GemiAutoTool/services/input_service.py

import os
from GemiAutoTool.config import INPUT_DIR
from GemiAutoTool.exceptions import InputFileNotFoundError, InputFileReadError

class InputService:
    @staticmethod
    def read_accounts_text() -> str:
        """
        从 input/account.txt 文件中读取账号原始文本
        """
        account_file = os.path.join(INPUT_DIR, "account.txt")

        # 检查文件是否存在
        if not os.path.exists(account_file):
            raise InputFileNotFoundError(
                f"找不到账号文件: {account_file}。请在 input 文件夹下创建 account.txt 并按照格式填入账号。"
            )

        try:
            with open(account_file, "r", encoding="utf-8") as f:
                content = f.read()
                print(f"📄 [Input Service] 成功读取账号文件: account.txt")
                return content
        except Exception as e:
            raise InputFileReadError(f"读取 account.txt 时发生错误: {e}") from e
