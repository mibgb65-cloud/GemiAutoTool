# GemiAutoTool/main.py

import threading
import time
import string
import random

from GemiAutoTool.config import MAX_CONCURRENT_WINDOWS
from GemiAutoTool.services.account_service import AccountService
from GemiAutoTool.services.input_service import InputService  # 引入新增的 InputService
from GemiAutoTool.tasks.browser_task import run_browser_task
from GemiAutoTool.services.output_service import SubscriptionOutputService
from GemiAutoTool.services.payment_data_service import PaymentDataService

def main():
    print("=== GemiAutoTool 自动化系统启动 ===")

    # 1. 获取账号数据 (改为从 input/account.txt 文件读取)
    raw_accounts_text = InputService.read_accounts_text()

    # 检查是否读取到了内容
    if not raw_accounts_text.strip():
        print("没有读取到账号内容，程序退出。")
        return

    # 解析账号
    accounts = AccountService.parse_accounts_from_text(raw_accounts_text)

    if not accounts:
        print("没有可用的账号，程序退出。")
        return

    output_service = SubscriptionOutputService()
    payment_data_service = PaymentDataService()

    task_count = min(len(accounts), MAX_CONCURRENT_WINDOWS)
    print(f"成功加载 {len(accounts)} 个账号，准备启动 {task_count} 个并发任务...")

    threads = []

    # 3. 分发任务到线程
    for i in range(task_count):
        account = accounts[i]
        task_name = f"Task_{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}"

        t = threading.Thread(target=run_browser_task, args=(account, task_name, output_service, payment_data_service))
        threads.append(t)
        t.start()
        time.sleep(0.5)  # 错峰启动，防止卡顿

    # 等待所有线程完成
    for t in threads:
        t.join()

    print("=== 所有自动化任务已全部结束 ===")


if __name__ == "__main__":
    main()