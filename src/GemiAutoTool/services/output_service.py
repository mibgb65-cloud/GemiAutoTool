# GemiAutoTool/services/output_service.py

import os
import threading
from datetime import datetime
from GemiAutoTool.config import OUTPUT_DIR
from GemiAutoTool.domain.subscription_result import SubscriptionResult


class SubscriptionOutputService:
    def __init__(self):
        # 创建线程锁，防止多个浏览器实例同时写入导致文本错乱
        self.lock = threading.Lock()
        self.file_path = None

    def _init_file(self):
        """内部方法：在获取到第一个结果时，以当前时间创建专属的 txt 文件"""
        if self.file_path is None:
            # 按照 年月日_时分秒 格式生成时间戳
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"subscription_results_{timestamp}.txt"
            self.file_path = os.path.join(OUTPUT_DIR, filename)
            print(f"\n📄 [Output Service] 成功创建本次运行的记录文件: {filename}\n")

    def save_result(self, result: SubscriptionResult):
        """
        保存检测结果到文件
        :param result: SubscriptionResult 实体对象
        """
        with self.lock:
            # 确保文件路径已被初始化（在第一次调用时触发）
            self._init_file()

            # 根据不同的状态处理输出逻辑
            line = ""
            if result.status == "已订阅":
                # 订阅成功的账号直接标记状态
                line = f"{result.email}----已订阅\n"
            elif result.link and "http" in result.link:
                # 提取到了有效链接的账号，按照 账号__链接 格式写入
                line = f"{result.email}__{result.link}\n"
            else:
                # 其他情况（如支付失败、各种异常状态）
                line = f"{result.email}----{result.status}\n"

            # 写入文件并打印日志
            if line:
                with open(self.file_path, "a", encoding="utf-8") as f:
                    f.write(line)
                print(f"📝 [Output Service] 结果已保存: {line.strip()}")