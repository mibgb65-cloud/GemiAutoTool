# GemiAutoTool/actions/google_one.py

import time
from selenium.webdriver.common.by import By


def check_subscription(driver, task_name: str, retry_count=0) -> tuple[str, str]:
    """跳转并检测订阅状态"""
    print(f"[{task_name}] 正在检测订阅状态 (尝试次数: {retry_count + 1})...")

    if retry_count > 0:
        print(f"[{task_name}] 🔄 正在刷新页面重试...")
        driver.refresh()
    else:
        driver.get("https://one.google.com/ai-student")

    time.sleep(8)
    status, link = "未知状态", "无法提取链接"

    # XPaths
    xpath_sub = "//*[contains(text(), \"You're already subscribed\")] | //a[@aria-label='Manage plan']"
    xpath_certified = "//*[contains(text(), 'Get student offer')]"
    xpath_verify = "//a[contains(@href, 'sheerid')] | //a[contains(@aria-label, 'Verify')] | //a[contains(@aria-label, '验证')] | //*[contains(text(), 'Verify')]"

    try:
        # 1. 检查是否已订阅
        if driver.find_elements(By.XPATH, xpath_sub):
            return "已订阅", ""

        # 2. 检查是否已认证但未订阅
        if driver.find_elements(By.XPATH, xpath_certified):
            return "已认证/未订阅", ""

        # 3. 检查是否需要验证 (提取 sheerid 链接)
        btns = driver.find_elements(By.XPATH, xpath_verify)
        if btns:
            status = "未订阅 (需验证)"
            found_link = ""

            # 寻找 href 属性
            for btn in btns:
                href = btn.get_attribute("href")
                if href and "http" in href:
                    found_link = href
                    break

            if not found_link:
                try:
                    found_link = btns[0].find_element(By.XPATH, "./..").get_attribute("href")
                except:
                    pass

            # 验证提取的链接有效性
            if found_link and "services.sheerid.com/verify" in found_link:
                if "verificationId=" in found_link and not found_link.split("verificationId=")[-1].strip():
                    print(f"[{task_name}] ⚠️ 提取到无效链接 (ID为空)，准备重试...")
                    if retry_count < 3:
                        return check_subscription(driver, task_name, retry_count + 1)
                    else:
                        return status, "获取失败: 链接ID为空且重试无效"
                return status, found_link
            elif found_link:
                return status, found_link

    except Exception as e:
        print(f"[{task_name}] ⚠️ 检测出错: {e}")

    return status, link