# GemiAutoTool/actions/google_auth.py

import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from GemiAutoTool.utils import TOTPUtil, is_element_exist, wait_and_click, wait_and_type

logger = logging.getLogger(__name__)


def login_google(driver, account, task_name: str) -> bool:
    """执行极简版的 Google 登录流程"""
    logger.info("正在执行登录流程: %s", account.email)

    # 0. 访问 Google 首页并点击右上角的登录按钮
    driver.get("https://www.google.com")
    logger.info("已打开 Google 首页，寻找登录按钮...")
    time.sleep(2)  # 稍微等待页面渲染

    # 使用 CSS 选择器匹配 href 中包含 ServiceLogin 的 a 标签。
    # 这样无论是中文的"登录"还是英文的"Sign in"，都可以稳定点击到右上角的按钮。
    login_btn_locator = "a[href*='ServiceLogin']"
    if not wait_and_click(driver, By.CSS_SELECTOR, login_btn_locator, timeout=10, task_name=task_name):
        logger.warning("未能在首页找到登录按钮，请检查页面是否加载完全。")
        return False

    logger.info("成功点击首页登录按钮，正在进入账号密码输入页...")
    time.sleep(3)  # 等待页面跳转

    # 1. 输入账号并点击下一步
    if not wait_and_type(driver, By.ID, "identifierId", account.email, task_name=task_name):
        return False
    wait_and_click(driver, By.ID, "identifierNext", task_name=task_name)

    # 2. 输入密码并点击下一步
    # 注意：密码输入框通常需要等待动画展开，稍微多等一会
    time.sleep(1)
    if not wait_and_type(driver, By.NAME, "Passwd", account.password, task_name=task_name):
        return False
    wait_and_click(driver, By.ID, "passwordNext", task_name=task_name)

    # 3. 处理 2FA
    logger.info("检测 2FA 验证...")
    code = TOTPUtil.generate_code(account.two_fa_secret)
    totp_locator = "input[type='tel'], input[id='totpPin']"

    if code and is_element_exist(driver, By.CSS_SELECTOR, totp_locator, timeout=8):
        logger.info("成功生成 2FA，正在输入...")
        wait_and_type(driver, By.CSS_SELECTOR, totp_locator, code, timeout=5, task_name=task_name)
        time.sleep(1)
        # 发送回车键
        driver.find_element(By.CSS_SELECTOR, totp_locator).send_keys(Keys.ENTER)
        time.sleep(5)
    elif not code:
        logger.info("账号无有效 2FA 密钥，直接跳过 2FA 步骤。")

    # 4. 跳过风控/推广弹窗 (Simplify your sign-in)
    skip_xpath = "//*[text()='Not now' or text()='暂不' or text()='以后再说']"
    if is_element_exist(driver, By.XPATH, skip_xpath, timeout=5):
        logger.info("发现推广弹窗，正在跳过...")
        wait_and_click(driver, By.XPATH, skip_xpath, timeout=5, task_name=task_name)
        time.sleep(4)

    # 5. 判断是否登录成功
    time.sleep(4)
    current_url = driver.current_url
    if "myaccount.google.com" in current_url or "google.com" in current_url:
        logger.info("登录成功")
        return True

    logger.info("登录后停留页面未识别: %s...", current_url[:50])
    return False
