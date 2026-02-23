# GemiAutoTool/services/payment_data_service.py

import os
import random
import threading
from GemiAutoTool.config import INPUT_DIR
from GemiAutoTool.domain.payment_info import PaymentInfo


class PaymentDataService:
    def __init__(self):
        self.lock = threading.Lock()
        self.cards = []
        self.names = []
        self.zip_codes = []
        self.card_index = 0  # 用于记录当前取到了第几张卡

        self._load_all_data()

    def _load_all_data(self):
        """内部方法：在程序启动时一次性把三个 txt 的内容加载到内存中"""
        card_file = os.path.join(INPUT_DIR, "card.txt")
        name_file = os.path.join(INPUT_DIR, "name.txt")
        zip_file = os.path.join(INPUT_DIR, "zip_code.txt")

        # 1. 加载姓名
        if os.path.exists(name_file):
            with open(name_file, "r", encoding="utf-8") as f:
                self.names = [line.strip() for line in f if line.strip()]

        # 2. 加载邮编
        if os.path.exists(zip_file):
            with open(zip_file, "r", encoding="utf-8") as f:
                self.zip_codes = [line.strip() for line in f if line.strip()]

        # 3. 加载并解析信用卡信息
        if os.path.exists(card_file):
            with open(card_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # 匹配格式: [pan:2387..., cvv:023, exp_month:10/30]
                    if line.startswith("[") and line.endswith("]"):
                        content = line[1:-1]
                        parts = content.split(",")
                        card_dict = {}
                        for part in parts:
                            k, v = part.split(":")
                            card_dict[k.strip()] = v.strip()

                        if "pan" in card_dict and "cvv" in card_dict and "exp_month" in card_dict:
                            # 将 10/30 拆分成月份和年份
                            month, year = card_dict["exp_month"].split("/")
                            self.cards.append({
                                "pan": card_dict["pan"],
                                "cvv": card_dict["cvv"],
                                "exp_month": month,
                                "exp_year": year
                            })

        print(
            f"📦 [Data Service] 成功加载数据: 信用卡 {len(self.cards)} 张, 姓名 {len(self.names)} 个, 邮编 {len(self.zip_codes)} 个。")

    def get_next_payment_info(self) -> PaymentInfo:
        """
        供多线程安全调用的方法：
        顺序取出一张信用卡，并随机附加一个姓名和邮编，组合成 PaymentInfo 对象返回。
        """
        with self.lock:
            if not self.cards or not self.names or not self.zip_codes:
                raise ValueError(
                    "⚠️ 支付数据不完整！请检查 input 文件夹下的 card.txt / name.txt / zip_code.txt 是否有数据。")

            # 顺序获取信用卡 (如果卡片用完了，会自动从头再循环取)
            card = self.cards[self.card_index % len(self.cards)]
            self.card_index += 1

            # 随机获取姓名和邮编
            name = random.choice(self.names)
            zip_code = random.choice(self.zip_codes)

            return PaymentInfo(
                pan=card["pan"],
                cvv=card["cvv"],
                exp_month=card["exp_month"],
                exp_year=card["exp_year"],
                name=name,
                zip_code=zip_code
            )