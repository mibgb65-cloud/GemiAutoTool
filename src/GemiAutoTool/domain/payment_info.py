# GemiAutoTool/domain/payment_info.py

from dataclasses import dataclass

@dataclass
class PaymentInfo:
    """
    支付信息实体类 (DTO)
    用于封装从本地读取的信用卡、随机姓名和随机邮编
    """
    pan: str         # 信用卡号 (例如: 2387273629387612)
    cvv: str         # 安全码 (例如: 023)
    exp_month: str   # 过期月份 (例如: 10)
    exp_year: str    # 过期年份 (例如: 30)
    name: str        # 随机读取的持卡人姓名
    zip_code: str    # 随机读取的邮政编码