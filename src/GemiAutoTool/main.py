# GemiAutoTool/main.py

import logging

from GemiAutoTool.app_controller import AutomationController
from GemiAutoTool.logging_config import setup_logging

logger = logging.getLogger(__name__)

def main():
    setup_logging()
    logger.debug("CLI 模式启动。")
    controller = AutomationController()
    controller.run()


if __name__ == "__main__":
    main()
