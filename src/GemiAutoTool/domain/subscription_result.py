# GemiAutoTool/domain/subscription_result.py

from dataclasses import dataclass

@dataclass
class SubscriptionResult:
    """
    订阅检测结果实体类 (DTO)
    用于封装账号、订阅状态以及提取到的链接
    """
    email: str     # 账号邮箱
    status: str    # 订阅状态 (例如: "已订阅", "未订阅 (需验证)" 等)
    link: str      # 提取到的跳转链接