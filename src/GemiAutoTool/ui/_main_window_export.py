"""MainWindow SheerID export actions."""

import os

from PySide6 import QtWidgets

from GemiAutoTool.services import SubscriptionOutputService


class MainWindowExportMixin:
    def _export_sheerid_links_from_file(self) -> None:
        source_file, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "选择结果文件",
            self._get_configured_output_dir(),
            "Text Files (*.txt);;All Files (*)",
        )
        if not source_file:
            return

        default_name = f"{os.path.splitext(os.path.basename(source_file))[0]}_sheerid_links.txt"
        suggested_output = os.path.join(self._get_configured_output_dir(), default_name)
        output_file, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "保存 SheerID 链接文件",
            suggested_output,
            "Text Files (*.txt);;All Files (*)",
        )

        if output_file == "":
            # 用户取消保存对话框时，回退到服务默认命名规则
            output_file = None  # type: ignore[assignment]

        try:
            service = SubscriptionOutputService(output_dir=self._get_configured_output_dir())
            export_path, count = service.export_sheerid_verify_links(
                source_file_path=source_file,
                output_file_path=output_file,
            )
            self._append_system_log(
                "INFO",
                "UI",
                "-",
                f"SheerID 链接导出完成: {count} 条 -> {export_path}",
            )
            QtWidgets.QMessageBox.information(
                self,
                "导出完成",
                f"已导出 {count} 条链接\n\n文件: {export_path}",
            )
        except Exception as e:
            self._append_system_log("ERROR", "UI", "-", f"导出 SheerID 链接失败: {e}")
            QtWidgets.QMessageBox.warning(self, "导出失败", str(e))

    def _export_sheerid_links_from_latest_result(self) -> None:
        latest_file = self._find_latest_result_file()
        if not latest_file:
            msg = "未找到结果文件（subscription_results_*.txt）。"
            self._append_system_log("WARNING", "UI", "-", msg)
            QtWidgets.QMessageBox.information(self, "未找到结果文件", msg)
            return

        try:
            service = SubscriptionOutputService(output_dir=self._get_configured_output_dir())
            export_path, count = service.export_sheerid_verify_links(source_file_path=latest_file)
            self._append_system_log(
                "INFO",
                "UI",
                "-",
                f"已从最近结果文件导出 {count} 条 SheerID 链接 -> {export_path}",
            )
            QtWidgets.QMessageBox.information(
                self,
                "导出完成",
                f"源文件: {latest_file}\n\n已导出 {count} 条链接\n输出: {export_path}",
            )
        except Exception as e:
            self._append_system_log("ERROR", "UI", "-", f"一键导出最近结果失败: {e}")
            QtWidgets.QMessageBox.warning(self, "导出失败", str(e))

    def _find_latest_result_file(self) -> str | None:
        try:
            candidates = []
            output_dir = self._get_configured_output_dir()
            if not os.path.isdir(output_dir):
                return None
            for name in os.listdir(output_dir):
                if not name.endswith(".txt"):
                    continue
                if not name.startswith("subscription_results_"):
                    continue
                if "_sheerid_links_" in name:
                    continue
                path = os.path.join(output_dir, name)
                if os.path.isfile(path):
                    candidates.append(path)
            if not candidates:
                return None
            return max(candidates, key=os.path.getmtime)
        except Exception:
            return None



__all__ = [
    "MainWindowExportMixin",
]
