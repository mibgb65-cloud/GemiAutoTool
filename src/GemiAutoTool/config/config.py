# GemiAutoTool/config/config.py

import os

# 定义 15 个不同的浏览器指纹配置
BROWSER_FINGERPRINTS = [
    {"os": "Win10", "resolution": "1920,1080", "lang": "en-US", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"},
    {"os": "Win11", "resolution": "2560,1440", "lang": "en-US", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"},
    {"os": "macOS", "resolution": "1440,900",  "lang": "en-US", "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"},
    {"os": "Win10", "resolution": "1366,768",  "lang": "en-US", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"},
    {"os": "macOS", "resolution": "1920,1080", "lang": "en-US", "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"},
    {"os": "Win11", "resolution": "1536,864",  "lang": "en-US", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0"},
    {"os": "Win10", "resolution": "1920,1080", "lang": "en-US", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"},
    {"os": "macOS", "resolution": "2560,1600", "lang": "en-US", "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"},
    {"os": "Win10", "resolution": "1280,720",  "lang": "en-US", "user_agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"},
    {"os": "Win11", "resolution": "1920,1080", "lang": "en-US", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"},
    {"os": "macOS", "resolution": "1366,768",  "lang": "en-US", "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"},
    {"os": "Win10", "resolution": "1600,900",  "lang": "en-US", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"},
    {"os": "Win11", "resolution": "1920,1200", "lang": "en-US", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"},
    {"os": "macOS", "resolution": "1920,1080", "lang": "en-US", "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"},
    {"os": "Win10", "resolution": "2560,1080", "lang": "en-US", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 OPR/107.0.0.0"}
]

DEFAULT_LOGIN_URL = "https://accounts.google.com/signin"
SIMULATE_WAIT_TIME = 15
MAX_CONCURRENT_WINDOWS = 3

# ==========================================
# 支付流程配置
# ==========================================
PAYMENT_ACTION_TIMINGS = {
    "offer_click_wait": 10,
    "offer_after_click_sleep": 5,
    "iframe_scan_before_sleep": 5,
    "iframe_probe_timeout": 0.1,
    "add_card_form_animation_sleep": 8,
    "tab_sleep": 1.5,
    "double_tab_sleep": 1.0,
    "typing_speed": 0.2,
    "action_pause": 0.5,
    "save_redirect_wait": 10,
    "subscribe_process_wait": 15,
}

PAYMENT_ACTION_ADD_CARD_XPATHS = [
    "//button[.//span[contains(text(), 'Add card')]]",
    "//span[contains(text(), 'Add card')]",
    "//div[contains(text(), 'Add card')]",
]

# ==========================================
# 路径与输出配置
# ==========================================
# 获取当前 config.py 所在目录的绝对路径
_current_dir = os.path.dirname(os.path.abspath(__file__))

# 向上推两级，定位到项目根目录 (GemiAutoTool)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_current_dir)))

# 定义统一的输出目录路径
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")

# 如果输出目录不存在，则自动创建它
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

INPUT_DIR = os.path.join(PROJECT_ROOT, "input")

# 如果输入目录不存在，自动创建它（提醒用户放文件）
if not os.path.exists(INPUT_DIR):
    os.makedirs(INPUT_DIR, exist_ok=True)
