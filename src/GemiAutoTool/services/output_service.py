# GemiAutoTool/services/output_service.py

import logging
import os
import re
import threading
from datetime import datetime
from GemiAutoTool.config import OUTPUT_DIR
from GemiAutoTool.domain import SubscriptionResult
from GemiAutoTool.exceptions import OutputReadError, OutputWriteError

logger = logging.getLogger(__name__)


class SubscriptionOutputService:
    def __init__(self, output_dir: str | None = None):
        # 创建线程锁，防止多个浏览器实例同时写入导致文本错乱
        self.lock = threading.Lock()
        self.file_path = None
        self.output_dir = output_dir or OUTPUT_DIR

    def _init_file(self):
        """内部方法：在获取到第一个结果时，以当前时间创建专属的 txt 文件"""
        if self.file_path is None:
            try:
                # 按照 年月日_时分秒 格式生成时间戳
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"subscription_results_{timestamp}.txt"
                os.makedirs(self.output_dir, exist_ok=True)
                self.file_path = os.path.join(self.output_dir, filename)
                logger.info("成功创建本次运行的记录文件: %s", filename)
            except Exception as e:
                raise OutputWriteError(f"初始化输出文件失败: {e}") from e

    def save_result(self, result: SubscriptionResult):
        """
        保存检测结果到文件
        :param result: SubscriptionResult 实体对象
        """
        with self.lock:
            # 确保文件路径已被初始化（在第一次调用时触发）
            self._init_file()

            # 根据不同的状态处理输出逻辑
            line = ""
            if result.status == "已订阅":
                # 订阅成功的账号直接标记状态
                line = f"{result.email}----已订阅\n"
            elif result.link and "http" in result.link:
                # 提取到了有效链接的账号，按照 账号__链接 格式写入
                line = f"{result.email}__{result.link}\n"
            else:
                # 其他情况（如支付失败、各种异常状态）
                line = f"{result.email}----{result.status}\n"

            # 写入文件并打印日志
            if line:
                try:
                    with open(self.file_path, "a", encoding="utf-8") as f:
                        f.write(line)
                    logger.info("结果已保存: %s", line.strip())
                except Exception as e:
                    raise OutputWriteError(f"写入结果文件失败 ({self.file_path}): {e}") from e

    def export_sheerid_verify_links(
        self,
        source_file_path: str | None = None,
        output_file_path: str | None = None,
        deduplicate: bool = True,
    ) -> tuple[str, int]:
        """
        从输出结果 txt 中提取 SheerID 验证链接，并按每行一个写入新的 txt 文件。

        :param source_file_path: 源结果文件路径；为空时默认使用当前实例本次运行生成的 file_path
        :param output_file_path: 导出文件路径；为空时自动生成到 output 目录
        :param deduplicate: 是否去重（保持原出现顺序）
        :return: (导出文件路径, 导出的链接数量)
        """
        source_path = source_file_path or self.file_path
        if not source_path:
            raise OutputReadError("未提供源结果文件路径，且当前实例尚未生成结果文件。")

        if not os.path.exists(source_path):
            raise OutputReadError(f"结果文件不存在: {source_path}")

        try:
            with open(source_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            raise OutputReadError(f"读取结果文件失败 ({source_path}): {e}") from e

        # 匹配示例:
        # https://services.sheerid.com/verify/67c8c14f5f17a83b745e3f82/?verificationId=699c691f8d19cc3f1842fa87
        pattern = re.compile(r"https://services\.sheerid\.com/verify/[^\s]+")
        links = pattern.findall(content)

        if deduplicate:
            links = list(dict.fromkeys(links))

        if output_file_path is None:
            source_name = os.path.splitext(os.path.basename(source_path))[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            os.makedirs(self.output_dir, exist_ok=True)
            output_file_path = os.path.join(self.output_dir, f"{source_name}_sheerid_links_{timestamp}.txt")

        try:
            output_parent = os.path.dirname(output_file_path)
            if output_parent:
                os.makedirs(output_parent, exist_ok=True)
            with open(output_file_path, "w", encoding="utf-8") as f:
                if links:
                    f.write("\n".join(links) + "\n")
                else:
                    f.write("")
        except Exception as e:
            raise OutputWriteError(f"写入 SheerID 链接文件失败 ({output_file_path}): {e}") from e

        logger.info("SheerID 链接导出完成: %s 条 -> %s", len(links), output_file_path)
        return output_file_path, len(links)
