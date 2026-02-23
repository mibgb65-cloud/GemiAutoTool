# GemiAutoTool/tasks/browser_task.py

from GemiAutoTool.config import DEFAULT_LOGIN_URL
from GemiAutoTool.services import IsolatedBrowser, SubscriptionOutputService
from GemiAutoTool.domain import GoogleAccount, SubscriptionResult
from GemiAutoTool.actions import check_subscription, fill_payment_form, login_google
from GemiAutoTool.exceptions import (
    GemiAutoToolBaseException,
    PaymentDataError,
    PaymentProcessError,
    SubscriptionCheckError,
)


# [修改点] 这里接收了 payment_data_service 参数
def run_browser_task(account: GoogleAccount, task_name: str, output_service: SubscriptionOutputService,
                     payment_data_service):
    """
    单个浏览器的核心业务执行流
    """
    print(f"\n[{task_name}] 开始处理账号: {account.email}")

    browser = IsolatedBrowser(task_name)
    try:
        driver = browser.start_browser(DEFAULT_LOGIN_URL)

        # 1. 尝试登录
        if login_google(driver, account, task_name):

            # 2. 登录成功，去检测订阅状态
            try:
                status, link = check_subscription(driver, task_name)
            except SubscriptionCheckError as e:
                status, link = f"订阅检测失败 ({str(e)[:80]})", ""
                print(f"[{task_name}] ⚠️ {e}")
            print(f"[{task_name}] ✨ 初始订阅检测 -> 状态: {status}")

            # 3. 支付逻辑分支
            if status == "已认证/未订阅":
                print(f"[{task_name}] 需要进行支付验证，正在提取本地支付信息...")

                try:
                    # 向 PaymentDataService 索取一条组合好的支付信息
                    payment_data = payment_data_service.get_next_payment_info()

                    # 传入数据进行自动填表操作
                    is_paid, pay_msg = fill_payment_form(driver, payment_data, task_name)

                    if is_paid:
                        status = "已订阅"
                    else:
                        status = f"支付失败 ({pay_msg})"
                except PaymentDataError as e:
                    status = "支付失败 (本地数据不完整)"
                    print(f"[{task_name}] ⚠️ {e}")
                except PaymentProcessError as e:
                    status = f"支付失败 ({str(e)[:100]})"
                    print(f"[{task_name}] ⚠️ {e}")

            # 4. 生成结果实体，写入到 output 文件夹中
            result = SubscriptionResult(email=account.email, status=status, link=link)
            output_service.save_result(result)

        else:
            print(f"[{task_name}] ❌ 登录流程失败或中断，跳过后续步骤。")

    except GemiAutoToolBaseException as e:
        print(f"[{task_name}] ⚠️ 业务异常: {e}")
    except Exception as e:
        print(f"[{task_name}] 💥 发生全局崩溃性异常: {e}")
    finally:
        browser.close_browser()
