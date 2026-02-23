# GemiAutoTool/utils/selenium_util.py

import logging
import time
import random
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

logger = logging.getLogger(__name__)

def random_sleep(min_seconds=1, max_seconds=3):
    """随机等待一段时间，模拟人类行为"""
    time.sleep(random.uniform(min_seconds, max_seconds))

def type_slowly(element, text, min_delay=0.05, max_delay=0.2):
    """模拟人类缓慢输入"""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(min_delay, max_delay))

def wait_and_type(driver, by, locator, text, timeout=20, task_name="Task"):
    """等待元素出现并缓慢输入文字"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, locator))
        )
        time.sleep(random.uniform(0.5, 1.0))
        element.clear()
        type_slowly(element, text)
        random_sleep(1, 2)
        return True
    except TimeoutException:
        logger.warning("输入超时，未找到元素: %s", locator)
        return False
    except Exception as e:
        logger.warning("输入异常 (%s): %s", locator, e)
        return False

def wait_and_click(driver, by, locator, timeout=20, task_name="Task"):
    """等待元素可点击并执行点击"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, locator))
        )
        random_sleep(1, 2)
        element.click()
        return True
    except TimeoutException:
        logger.warning("点击超时，未找到可点击元素: %s", locator)
        return False
    except Exception as e:
        logger.warning("点击异常 (%s): %s", locator, e)
        return False

def is_element_exist(driver, by, locator, timeout=5):
    """判断元素是否存在（不抛出异常，常用于检测弹窗或状态）"""
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, locator))
        )
        return True
    except:
        return False
