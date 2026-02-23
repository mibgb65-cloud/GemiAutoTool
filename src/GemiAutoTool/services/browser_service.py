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
active_browsers_lock = threading.Lock()
active_browsers: set["IsolatedBrowser"] = set()
logger = logging.getLogger(__name__)


def _normalize_window_mode(value: object) -> str:
    mode = str(value or "headless").strip().lower()
    if mode in {"visible", "minimized", "headless"}:
        return mode
    return "headless"


class IsolatedBrowser:
    def __init__(self, profile_name, window_mode: str = "headless"):
        self.profile_name = profile_name
        self.window_mode = _normalize_window_mode(window_mode)
        self.driver = None
        self.temp_profile_dir = None
        self._close_lock = threading.Lock()

    def start_browser(self, login_url):
        logger.info("准备启动浏览器...")

        fingerprint = random.choice(BROWSER_FINGERPRINTS)
        logger.info(
            "选择指纹 -> OS: %s, 分辨率: %s, 语言: %s",
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
        if self.window_mode == "headless":
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")
            logger.warning("[%s] 浏览器模式=无头", self.profile_name)

        try:
            with browser_init_lock:
                self.driver = uc.Chrome(options=options)
                self._register_active()
                logger.info(
                    "浏览器启动成功（模式=%s，期望窗口=%s）",
                    self.window_mode,
                    fingerprint["resolution"],
                )

            self.driver.get(login_url)
            if self.window_mode == "minimized":
                try:
                    self.driver.minimize_window()
                    logger.info("浏览器已最小化")
                except Exception as e:
                    logger.warning("最小化浏览器失败: %s", e)
            self._log_window_metrics()
            logger.info("登录页面已加载")
            return self.driver

        except Exception as e:
            raise BrowserInitError(f"[{self.profile_name}] 启动浏览器失败: {e}") from e

    def _register_active(self) -> None:
        with active_browsers_lock:
            active_browsers.add(self)

    def _unregister_active(self) -> None:
        with active_browsers_lock:
            active_browsers.discard(self)

    def force_close_window(self) -> bool:
        """Force close browser window immediately (used by hard stop)."""
        with self._close_lock:
            if self.driver is None:
                return False
            try:
                self.driver.quit()
                logger.info("[%s] 已执行强制关闭浏览器窗口。", self.profile_name)
            except Exception as e:
                logger.warning("[%s] 强制关闭浏览器时发生异常: %s", self.profile_name, e)
            finally:
                self.driver = None
                self._unregister_active()
            return True

    def _log_window_metrics(self):
        if self.driver is None:
            return
        try:
            rect = self.driver.get_window_rect()
            logger.info(
                "实际窗口尺寸 -> x=%s y=%s w=%s h=%s",
                rect.get("x"),
                rect.get("y"),
                rect.get("width"),
                rect.get("height"),
            )
        except Exception as e:
            logger.debug("读取窗口尺寸失败: %s", e)
        try:
            outer_inner = self.driver.execute_script(
                "return {outerW: window.outerWidth, outerH: window.outerHeight, innerW: window.innerWidth, innerH: window.innerHeight};"
            )
            logger.info(
                "页面视口尺寸 -> outer=%sx%s inner=%sx%s",
                outer_inner.get("outerW"),
                outer_inner.get("outerH"),
                outer_inner.get("innerW"),
                outer_inner.get("innerH"),
            )
        except Exception as e:
            logger.debug("读取视口尺寸失败: %s", e)

    def close_browser(self):
        logger.info("任务结束，正在关闭并清理缓存...")
        with self._close_lock:
            if self.driver is not None:
                try:
                    self.driver.quit()
                except Exception as e:
                    logger.warning("关闭浏览器时发生异常: %s", e)
                finally:
                    self.driver = None
            self._unregister_active()

        time.sleep(2)

        if self.temp_profile_dir and os.path.exists(self.temp_profile_dir):
            shutil.rmtree(self.temp_profile_dir, ignore_errors=True)
            logger.info("缓存已彻底清除")


def force_close_all_active_browsers() -> int:
    """Force close all currently active browser windows. Returns number attempted."""
    with active_browsers_lock:
        browsers = list(active_browsers)

    closed_count = 0
    for browser in browsers:
        try:
            if browser.force_close_window():
                closed_count += 1
        except Exception as e:
            logger.warning("强制关闭浏览器实例失败: %s", e)
    if closed_count:
        logger.warning("硬结束：已强制关闭 %s 个浏览器窗口。", closed_count)
    else:
        logger.info("硬结束：当前没有活动浏览器窗口可关闭。")
    return closed_count
