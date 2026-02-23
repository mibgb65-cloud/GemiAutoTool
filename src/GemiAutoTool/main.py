# GemiAutoTool/main.py

import logging
import threading
import time
import string
import random

from GemiAutoTool.config import MAX_CONCURRENT_WINDOWS
from GemiAutoTool.services import (
    AccountService,
    InputService,
    PaymentDataService,
    SubscriptionOutputService,
)
from GemiAutoTool.tasks import run_browser_task
from GemiAutoTool.exceptions import GemiAutoToolBaseException
from GemiAutoTool.logging_config import setup_logging

logger = logging.getLogger(__name__)

def main():
    setup_logging()
    logger.info("=== GemiAutoTool 自动化系统启动 ===")

    # 1. 获取账号数据 (改为从 input/account.txt 文件读取)
    try:
        raw_accounts_text = InputService.read_accounts_text()
    except GemiAutoToolBaseException as e:
        logger.error("启动失败: %s", e)
        return

    # 检查是否读取到了内容
    if not raw_accounts_text.strip():
        logger.warning("没有读取到账号内容，程序退出。")
        return

    # 解析账号
    accounts = AccountService.parse_accounts_from_text(raw_accounts_text)

    if not accounts:
        logger.warning("没有可用的账号，程序退出。")
        return

    output_service = SubscriptionOutputService()
    try:
        payment_data_service = PaymentDataService()
    except GemiAutoToolBaseException as e:
        logger.error("初始化支付数据失败: %s", e)
        return

    task_count = min(len(accounts), MAX_CONCURRENT_WINDOWS)
    logger.info("成功加载 %s 个账号，准备启动 %s 个并发任务...", len(accounts), task_count)

    threads = []

    # 3. 分发任务到线程
    for i in range(task_count):
        account = accounts[i]
        task_name = f"Task_{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}"

        t = threading.Thread(
            name=task_name,
            target=run_browser_task,
            args=(account, task_name, output_service, payment_data_service),
        )
        threads.append(t)
        t.start()
        time.sleep(0.5)  # 错峰启动，防止卡顿

    # 等待所有线程完成
    for t in threads:
        t.join()

    logger.info("=== 所有自动化任务已全部结束 ===")


if __name__ == "__main__":
    main()
