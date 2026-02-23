
from typing import List
from GemiAutoTool.domain.account import GoogleAccount


class AccountService:
    @staticmethod
    def parse_accounts_from_text(raw_text: str, separator: str = "----") -> List[GoogleAccount]:
        """
        将包含多行账号信息的文本解析为 GoogleAccount 对象列表
        """
        accounts = []
        # 按行分割，过滤掉空行
        lines = [line.strip() for line in raw_text.strip().split('\n') if line.strip()]

        for line in lines:
            parts = line.split(separator)
            if len(parts) == 4:
                account = GoogleAccount(
                    email=parts[0].strip(),
                    password=parts[1].strip(),
                    recovery_email=parts[2].strip(),
                    two_fa_secret=parts[3].strip()
                )
                accounts.append(account)
            else:
                print(f"⚠️ 忽略格式错误的账号行: {line}")

        return accounts