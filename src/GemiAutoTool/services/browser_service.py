# GemiAutoTool/services/browser_service.py

import logging
import undetected_chromedriver as uc
import threading
import time
import shutil
import tempfile
import random
import os

from GemiAutoTool.config import BROWSER_FINGERPRINTS
from GemiAutoTool.exceptions import BrowserInitError

# 创建一个全局的线程锁，防止初始化冲突
browser_init_lock = threading.Lock()
logger = logging.getLogger(__name__)


class IsolatedBrowser:
    def __init__(self, profile_name):
        self.profile_name = profile_name
        self.driver = None
        self.temp_profile_dir = None

    def start_browser(self, login_url):
        logger.info("准备启动浏览器...")

        fingerprint = random.choice(BROWSER_FINGERPRINTS)
        logger.info(
            "抽中指纹 -> OS: %s, 分辨率: %s, 语言: %s",
            fingerprint["os"],
            fingerprint["resolution"],
            fingerprint["lang"],
        )

        self.temp_profile_dir = tempfile.mkdtemp(prefix=f"uc_profile_{self.profile_name}_")

        options = uc.ChromeOptions()
        options.add_argument(f"--user-data-dir={self.temp_profile_dir}")
        options.add_argument(f"--user-agent={fingerprint['user_agent']}")

        # 直接在这里通过启动参数固定初始窗口大小，防止启动后的二次缩放行为
        options.add_argument(f"--window-size={fingerprint['resolution']}")

        options.add_argument(f"--lang={fingerprint['lang']}")
        options.add_argument("--disable-blink-features=AutomationControlled")

        try:
            with browser_init_lock:
                self.driver = uc.Chrome(options=options)
                logger.info("浏览器启动成功，原生窗口大小为 %s", fingerprint["resolution"])

            self.driver.get(login_url)
            logger.info("登录页面已加载")
            return self.driver

        except Exception as e:
            raise BrowserInitError(f"[{self.profile_name}] 启动浏览器失败: {e}") from e

    def close_browser(self):
        logger.info("任务结束，正在关闭并清理缓存...")
        if self.driver is not None:
            try:
                self.driver.quit()
            except Exception as e:
                logger.warning("关闭浏览器时发生异常: %s", e)

        time.sleep(2)

        if self.temp_profile_dir and os.path.exists(self.temp_profile_dir):
            shutil.rmtree(self.temp_profile_dir, ignore_errors=True)
            logger.info("缓存已彻底清除")
