# GemiAutoTool/actions/payment_action.py

import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from GemiAutoTool.domain import PaymentInfo
from GemiAutoTool.actions.google_one import check_subscription
from GemiAutoTool.config import PAYMENT_ACTION_TIMINGS, PAYMENT_ACTION_ADD_CARD_XPATHS
from GemiAutoTool.exceptions import PaymentProcessError, SubscriptionCheckError

logger = logging.getLogger(__name__)


def fill_payment_form(driver, payment: PaymentInfo, task_name: str) -> tuple[bool, str]:
    """自动填写信用卡表单并提交订阅"""
    TAB_SLEEP = PAYMENT_ACTION_TIMINGS["tab_sleep"]
    DOUBLE_TAB_SLEEP = PAYMENT_ACTION_TIMINGS["double_tab_sleep"]
    TYPING_SPEED = PAYMENT_ACTION_TIMINGS["typing_speed"]
    ACTION_PAUSE = PAYMENT_ACTION_TIMINGS["action_pause"]
    logger.info("开始处理支付页面...")

    try:
        # 1. Offer
        offer_btn = WebDriverWait(driver, PAYMENT_ACTION_TIMINGS["offer_click_wait"]).until(
            EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Get student offer')]"))
        )
        offer_btn.click()
        time.sleep(PAYMENT_ACTION_TIMINGS["offer_after_click_sleep"])

        # 2. Add Card
        logger.info("在 Iframe 中寻找 'Add card'...")
        target_xpaths = PAYMENT_ACTION_ADD_CARD_XPATHS
        add_btn = None

        # 直接获取所有 iframe 进行遍历
        time.sleep(PAYMENT_ACTION_TIMINGS["iframe_scan_before_sleep"])
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for f in iframes:
            try:
                # 切入 iframe
                driver.switch_to.frame(f)

                # 在此 iframe 中快速探测
                for xp in target_xpaths:
                    try:
                        add_btn = WebDriverWait(driver, PAYMENT_ACTION_TIMINGS["iframe_probe_timeout"]).until(
                            EC.element_to_be_clickable((By.XPATH, xp))
                        )
                        if add_btn:
                            break
                    except:
                        continue

                if add_btn:
                    # 核心：在切回主页面【之前】，执行点击！
                    driver.execute_script("arguments[0].click();", add_btn)
                    logger.info("成功在 Iframe 中点击 Add card")
                    driver.switch_to.default_content()  # 点击完切回主页面
                    break  # 任务完成，跳出 iframe 遍历循环
                else:
                    # 如果这个 iframe 里没找到，切回主页面，准备探测下一个 iframe
                    driver.switch_to.default_content()

            except Exception as e:
                # 容错处理：如果发生了跨域错误等异常，也要确保切回主页面
                driver.switch_to.default_content()

        if not add_btn:
            logger.warning("未找到 Add card (可能已直接显示表单或网络延迟)")

        # 稍微等待弹窗或新表单的动画加载
        time.sleep(PAYMENT_ACTION_TIMINGS["add_card_form_animation_sleep"])

        # 3. 填表准备
        exp = f"{str(payment.exp_month).zfill(2)}/{str(payment.exp_year)[-2:]}"

        driver.switch_to.default_content()

        # 卡号
        ac = ActionChains(driver)
        for c in payment.pan: ac.send_keys(c).pause(TYPING_SPEED)
        ac.perform()
        time.sleep(TAB_SLEEP)

        # 日期 (Tab)
        ActionChains(driver).send_keys(Keys.TAB).perform()
        time.sleep(TAB_SLEEP)
        ac = ActionChains(driver)
        for c in exp: ac.send_keys(c).pause(TYPING_SPEED)
        ac.perform()
        time.sleep(TAB_SLEEP)

        # CVV
        time.sleep(TAB_SLEEP)
        ac = ActionChains(driver)
        for c in payment.cvv: ac.send_keys(c).pause(TYPING_SPEED)
        ac.perform()
        time.sleep(TAB_SLEEP)

        # 姓名 (Tab)
        ActionChains(driver).send_keys(Keys.TAB).perform()
        time.sleep(TAB_SLEEP)
        ac = ActionChains(driver)
        for c in payment.name: ac.send_keys(c).pause(TYPING_SPEED)
        ac.perform()
        time.sleep(TAB_SLEEP)

        # 邮编 (Tab*2)
        ActionChains(driver).send_keys(Keys.TAB).pause(DOUBLE_TAB_SLEEP).send_keys(Keys.TAB).perform()
        time.sleep(TAB_SLEEP)
        ac = ActionChains(driver)
        for c in payment.zip_code: ac.send_keys(c).pause(TYPING_SPEED)
        ac.perform()
        time.sleep(TAB_SLEEP)

        # 4. 保存
        logger.info("保存卡片...")
        ActionChains(driver).send_keys(Keys.TAB).pause(ACTION_PAUSE).send_keys(Keys.TAB).pause(ACTION_PAUSE).send_keys(Keys.TAB).perform()
        time.sleep(TAB_SLEEP)
        ActionChains(driver).send_keys(Keys.ENTER).perform()

        logger.info("等待保存跳转 (10s)...")
        time.sleep(PAYMENT_ACTION_TIMINGS["save_redirect_wait"])

        # 5. 订阅
        logger.info("点击订阅...")
        ActionChains(driver).send_keys(Keys.TAB).pause(ACTION_PAUSE).send_keys(Keys.TAB).pause(ACTION_PAUSE).send_keys(Keys.TAB).pause(
            ACTION_PAUSE).send_keys(Keys.TAB).pause(ACTION_PAUSE).send_keys(Keys.TAB).perform()
        time.sleep(TAB_SLEEP)
        ActionChains(driver).send_keys(Keys.ENTER).perform()

        logger.info("等待订阅处理 (15s)...")
        time.sleep(PAYMENT_ACTION_TIMINGS["subscribe_process_wait"])

        # 6. 最终检查
        logger.info("最终校验...")
        final_status, _ = check_subscription(driver, task_name)

        if "已订阅" in final_status:
            logger.info("支付并订阅成功")
            return True, "成功"
        else:
            return False, f"流程走完但状态为: {final_status}"

    except SubscriptionCheckError as e:
        raise PaymentProcessError(f"支付流程最终校验失败: {e}") from e
    except Exception as e:
        err = str(e)[:100]
        raise PaymentProcessError(f"填表/订阅异常: {err}") from e
