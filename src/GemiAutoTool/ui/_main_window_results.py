"""MainWindow results viewer page for output txt files."""

import os
import re

from PySide6 import QtCore, QtGui, QtWidgets
from GemiAutoTool.ui.workers import VerifyLinkWorker


class MainWindowResultsMixin:
    def _build_results_page(self) -> QtWidgets.QWidget:
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        layout.addWidget(self._build_results_toolbar())
        layout.addWidget(self._build_results_info_bar())
        layout.addWidget(self._build_results_verify_panel())
        layout.addWidget(self._build_results_table_group(), stretch=1)
        return page

    def _build_results_toolbar(self) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        load_latest_btn = QtWidgets.QPushButton("加载最近结果")
        choose_file_btn = QtWidgets.QPushButton("选择结果文件")
        refresh_btn = QtWidgets.QPushButton("刷新当前文件")
        open_output_dir_btn = QtWidgets.QPushButton("打开输出目录")
        open_link_btn = QtWidgets.QPushButton("打开认证链接")
        copy_link_btn = QtWidgets.QPushButton("复制认证链接")

        self.results_keyword_edit = QtWidgets.QLineEdit()
        self.results_keyword_edit.setPlaceholderText("搜索账号/状态/链接")
        self.results_keyword_edit.setClearButtonEnabled(True)
        self.results_keyword_edit.textChanged.connect(self._apply_results_filter)

        self.results_link_only_check = QtWidgets.QCheckBox("仅看有认证链接")
        self.results_link_only_check.toggled.connect(self._apply_results_filter)

        load_latest_btn.clicked.connect(self._load_latest_results_file)
        choose_file_btn.clicked.connect(self._choose_results_file)
        refresh_btn.clicked.connect(self._reload_current_results_file)
        open_output_dir_btn.clicked.connect(lambda: self._open_directory(self._get_configured_output_dir()))
        open_link_btn.clicked.connect(self._open_selected_result_link)
        copy_link_btn.clicked.connect(self._copy_selected_result_link)

        layout.addWidget(load_latest_btn)
        layout.addWidget(choose_file_btn)
        layout.addWidget(refresh_btn)
        layout.addWidget(open_output_dir_btn)
        layout.addWidget(open_link_btn)
        layout.addWidget(copy_link_btn)
        layout.addSpacing(8)
        layout.addWidget(self.results_link_only_check)
        layout.addWidget(self.results_keyword_edit, 1)
        return widget

    def _build_results_info_bar(self) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QGridLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(6)

        self.results_file_edit = QtWidgets.QLineEdit()
        self.results_file_edit.setReadOnly(True)
        self.results_summary_label = QtWidgets.QLabel("未加载结果文件")
        self.results_summary_label.setStyleSheet("color: #606266;")

        layout.addWidget(QtWidgets.QLabel("结果文件"), 0, 0)
        layout.addWidget(self.results_file_edit, 0, 1)
        layout.addWidget(self.results_summary_label, 1, 0, 1, 2)
        layout.setColumnStretch(1, 1)
        return widget

    def _build_results_verify_panel(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("SheerIDBot 验证（当前选中链接）")
        layout = QtWidgets.QGridLayout(group)
        layout.setColumnStretch(1, 1)

        self.results_verify_api_key_edit = QtWidgets.QLineEdit()
        self.results_verify_api_key_edit.setPlaceholderText("输入 SheerIDBot API Key（X-API-Key）")
        self.results_verify_api_key_edit.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.results_verify_api_key_edit.setClearButtonEnabled(True)

        self.results_verify_run_btn = QtWidgets.QPushButton("验证当前选中链接")
        self.results_verify_run_btn.clicked.connect(self._verify_selected_result_link)

        self.results_verify_status_label = QtWidgets.QLabel("未开始")
        self.results_verify_status_label.setStyleSheet("font-weight: 600;")
        self.results_verify_progress_bar = QtWidgets.QProgressBar()
        self.results_verify_progress_bar.setRange(0, 100)
        self.results_verify_progress_bar.setValue(0)
        self.results_verify_progress_detail_label = QtWidgets.QLabel("等待提交")
        self.results_verify_progress_detail_label.setStyleSheet("color: #606266;")
        self.results_verify_job_label = QtWidgets.QLabel("Job ID: -")
        self.results_verify_job_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        self.results_verify_target_link_label = QtWidgets.QLabel("当前链接: -")
        self.results_verify_target_link_label.setWordWrap(True)
        self.results_verify_target_link_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        self.results_verify_target_link_label.setStyleSheet("color: #606266;")

        layout.addWidget(QtWidgets.QLabel("API Key"), 0, 0)
        layout.addWidget(self.results_verify_api_key_edit, 0, 1)
        layout.addWidget(self.results_verify_run_btn, 0, 2)
        layout.addWidget(QtWidgets.QLabel("状态"), 1, 0)
        layout.addWidget(self.results_verify_status_label, 1, 1, 1, 2)
        layout.addWidget(QtWidgets.QLabel("进度"), 2, 0)
        layout.addWidget(self.results_verify_progress_bar, 2, 1, 1, 2)
        layout.addWidget(self.results_verify_progress_detail_label, 3, 0, 1, 3)
        layout.addWidget(self.results_verify_job_label, 4, 0, 1, 3)
        layout.addWidget(self.results_verify_target_link_label, 5, 0, 1, 3)
        return group

    def _build_results_table_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("账号结果明细")
        layout = QtWidgets.QVBoxLayout(group)

        self.results_table = QtWidgets.QTableWidget(0, 5)
        self.results_table.setHorizontalHeaderLabels(["账号", "状态", "认证链接", "来源", "原始记录"])
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.results_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.horizontalHeader().setStretchLastSection(False)
        self.results_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.results_table.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.results_table.itemDoubleClicked.connect(self._on_results_table_item_double_clicked)

        layout.addWidget(self.results_table)
        return group

    def _init_results_page_state(self) -> None:
        self._results_records: list[dict[str, str]] = []
        self._results_current_file_path: str = ""
        self._verify_thread: QtCore.QThread | None = None
        self._verify_worker: VerifyLinkWorker | None = None

    def _try_load_results_view_latest(self, silent: bool = True) -> None:
        latest_file = self._find_latest_result_file()
        if latest_file:
            self._load_results_file_into_view(latest_file, silent=silent)
        elif not silent and hasattr(self, "results_summary_label"):
            self.results_summary_label.setText("未找到结果文件（subscription_results_*.txt）")

    def _load_latest_results_file(self) -> None:
        latest_file = self._find_latest_result_file()
        if not latest_file:
            msg = "未找到结果文件（subscription_results_*.txt）。"
            self._append_system_log("WARNING", "UI", "-", msg)
            QtWidgets.QMessageBox.information(self, "未找到结果文件", msg)
            return
        self._load_results_file_into_view(latest_file, silent=False)

    def _choose_results_file(self) -> None:
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "选择结果文件",
            self._get_configured_output_dir(),
            "Text Files (*.txt);;All Files (*)",
        )
        if not file_path:
            return
        self._load_results_file_into_view(file_path, silent=False)

    def _reload_current_results_file(self) -> None:
        if not self._results_current_file_path:
            self._load_latest_results_file()
            return
        self._load_results_file_into_view(self._results_current_file_path, silent=False)

    def _load_results_file_into_view(self, file_path: str, silent: bool = False) -> None:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = [line.rstrip("\n") for line in f]
        except Exception as e:
            self._append_system_log("ERROR", "UI", "-", f"读取结果文件失败: {e}")
            if not silent:
                QtWidgets.QMessageBox.warning(self, "读取失败", str(e))
            return

        records: list[dict[str, str]] = []
        for line_no, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()
            if not line:
                continue
            record = self._parse_result_record_line(line=line, line_no=line_no, source_file=file_path)
            records.append(record)

        self._results_records = records
        self._results_current_file_path = file_path
        self.results_file_edit.setText(file_path)
        self._apply_results_filter()

        self._append_system_log("INFO", "UI", "-", f"已加载结果文件: {file_path}（{len(records)} 条）")
        if not silent:
            self.page_tabs.setCurrentWidget(self._results_page_widget)

    def _parse_result_record_line(self, *, line: str, line_no: int, source_file: str) -> dict[str, str]:
        email = ""
        status = ""
        link = ""

        if "__" in line:
            email_part, right = line.split("__", 1)
            email = email_part.strip()
            right = right.strip()
            found_link = self._extract_first_url(right)
            if found_link:
                link = found_link
                status = "待认证"
            else:
                status = right or "未知"
        elif "----" in line:
            email_part, right = line.split("----", 1)
            email = email_part.strip()
            status = right.strip()
            link = self._extract_first_url(status)
        else:
            email = self._extract_email(line)
            link = self._extract_first_url(line)
            status = line if not email else line.replace(email, "", 1).strip("-_ ")
            if not status:
                status = "未知"

        if not status:
            status = "未知"

        if not email:
            email = "(无法识别账号)"

        return {
            "email": email,
            "status": status,
            "link": link or "",
            "source": f"{os.path.basename(source_file)}:{line_no}",
            "raw": line,
        }

    def _apply_results_filter(self) -> None:
        keyword = self.results_keyword_edit.text().strip().lower() if hasattr(self, "results_keyword_edit") else ""
        link_only = bool(self.results_link_only_check.isChecked()) if hasattr(self, "results_link_only_check") else False

        filtered: list[dict[str, str]] = []
        for record in getattr(self, "_results_records", []):
            if link_only and not record.get("link"):
                continue
            if keyword:
                haystack = " ".join(
                    [
                        record.get("email", ""),
                        record.get("status", ""),
                        record.get("link", ""),
                        record.get("raw", ""),
                    ]
                ).lower()
                if keyword not in haystack:
                    continue
            filtered.append(record)

        self._render_results_records(filtered)

    def _render_results_records(self, records: list[dict[str, str]]) -> None:
        self.results_table.setRowCount(0)
        status_counts = {"success": 0, "failed": 0, "verify": 0, "other": 0}

        for row, record in enumerate(records):
            self.results_table.insertRow(row)
            row_values = [
                record.get("email", ""),
                record.get("status", ""),
                record.get("link", ""),
                record.get("source", ""),
                record.get("raw", ""),
            ]
            for col, text in enumerate(row_values):
                item = QtWidgets.QTableWidgetItem(text)
                if col == 2 and text:
                    item.setToolTip(text)
                self.results_table.setItem(row, col, item)

            status_text = record.get("status", "")
            if status_text == "已订阅" or status_text.startswith("成功"):
                status_counts["success"] += 1
                self._set_results_row_color(row, "#2e7d32")
            elif status_text.startswith("需验证") or status_text == "待认证":
                status_counts["verify"] += 1
                self._set_results_row_color(row, "#b26a00")
            elif status_text.startswith("失败") or status_text.startswith("崩溃"):
                status_counts["failed"] += 1
                self._set_results_row_color(row, "#c62828")
            else:
                status_counts["other"] += 1

        current_file_name = os.path.basename(self._results_current_file_path) if self._results_current_file_path else "-"
        total_all = len(getattr(self, "_results_records", []))
        self.results_summary_label.setText(
            f"当前文件: {current_file_name} | 显示 {len(records)} / 总计 {total_all} 条 | "
            f"已订阅/成功 {status_counts['success']} | 需认证 {status_counts['verify']} | "
            f"失败 {status_counts['failed']} | 其他 {status_counts['other']}"
        )

    def _set_results_row_color(self, row: int, color_hex: str) -> None:
        color = QtGui.QColor(color_hex)
        for col in range(self.results_table.columnCount()):
            item = self.results_table.item(row, col)
            if item is not None:
                item.setForeground(color)

    def _get_selected_results_link(self) -> str:
        row = self.results_table.currentRow()
        if row < 0:
            return ""
        item = self.results_table.item(row, 2)
        return item.text().strip() if item and item.text() else ""

    def _copy_selected_result_link(self) -> None:
        link = self._get_selected_results_link()
        if not link:
            QtWidgets.QMessageBox.information(self, "提示", "当前选中行没有认证链接。")
            return
        QtWidgets.QApplication.clipboard().setText(link)
        self._append_system_log("INFO", "UI", "-", "已复制认证链接到剪贴板")

    def _open_selected_result_link(self) -> None:
        link = self._get_selected_results_link()
        if not link:
            QtWidgets.QMessageBox.information(self, "提示", "当前选中行没有认证链接。")
            return
        ok = QtGui.QDesktopServices.openUrl(QtCore.QUrl(link))
        if not ok:
            QtWidgets.QMessageBox.warning(self, "打开失败", "无法打开认证链接。")

    def _on_results_table_item_double_clicked(self, item: QtWidgets.QTableWidgetItem) -> None:
        if item.column() == 2:
            self._copy_selected_result_link()

    def _verify_selected_result_link(self) -> None:
        if self._verify_thread and self._verify_thread.isRunning():
            QtWidgets.QMessageBox.information(self, "提示", "当前已有验证任务正在进行。")
            return

        api_key = self.results_verify_api_key_edit.text().strip() if hasattr(self, "results_verify_api_key_edit") else ""
        if not api_key:
            self._set_results_verify_progress_state(
                status_text="已跳过",
                detail_text="未填写 API Key，已跳过验证。",
                percent=0,
                job_id="",
                target_link=self._get_selected_results_link(),
            )
            self._append_system_log("INFO", "UI", "-", "SheerIDBot API Key 未填写，已跳过验证。")
            return

        link = self._get_selected_results_link()
        if not link:
            self._append_system_log("WARNING", "UI", "-", "验证已取消：当前选中行没有认证链接")
            QtWidgets.QMessageBox.information(self, "提示", "当前选中行没有认证链接。")
            return

        self._set_results_verify_controls_enabled(False)
        self._set_results_verify_progress_state(
            status_text="提交中",
            detail_text="正在提交验证任务...",
            percent=None,
            job_id="",
            target_link=link,
        )
        self._append_system_log("INFO", "UI", "-", "开始提交 SheerIDBot 验证任务（当前选中链接）")

        self._verify_thread = QtCore.QThread(self)
        self._verify_worker = VerifyLinkWorker(api_key=api_key, verify_url=link)
        self._verify_worker.moveToThread(self._verify_thread)

        self._verify_thread.started.connect(self._verify_worker.run)
        self._verify_worker.progress.connect(self._on_results_verify_progress)
        self._verify_worker.finished.connect(self._on_results_verify_finished)
        self._verify_worker.skipped.connect(self._on_results_verify_skipped)
        self._verify_worker.error.connect(self._on_results_verify_error)
        self._verify_worker.finished.connect(lambda _: self._verify_thread.quit())
        self._verify_worker.skipped.connect(lambda _: self._verify_thread.quit())
        self._verify_worker.error.connect(lambda _: self._verify_thread.quit())
        self._verify_thread.finished.connect(self._cleanup_results_verify_worker)

        self._verify_thread.start()

    def _on_results_verify_progress(self, payload: dict) -> None:
        status = str(payload.get("status", "") or "")
        stage = str(payload.get("stage", "") or "")
        message = str(payload.get("message", "") or "")
        stage_number = payload.get("stage_number")
        total_stages = payload.get("total_stages")
        percentage = payload.get("percentage")
        job_id = str(payload.get("job_id", "") or "")

        status_text = status or "处理中"
        detail_parts: list[str] = []
        if stage and stage_number and total_stages:
            detail_parts.append(f"阶段 {stage_number}/{total_stages}: {stage}")
        elif stage:
            detail_parts.append(f"阶段: {stage}")
        if message:
            detail_parts.append(message)
        detail_text = " | ".join(part for part in detail_parts if part) or "等待状态更新..."

        percent_value: int | None = None
        if isinstance(percentage, (int, float)):
            percent_value = max(0, min(100, int(percentage)))

        self._set_results_verify_progress_state(
            status_text=status_text,
            detail_text=detail_text,
            percent=percent_value,
            job_id=job_id,
            target_link=self._get_selected_results_link(),
        )

    def _on_results_verify_finished(self, payload: dict) -> None:
        final = payload.get("final")
        final_data = final if isinstance(final, dict) else {}
        status = str(payload.get("status", "") or final_data.get("status", "") or "unknown")
        job_id = str(payload.get("job_id", "") or final_data.get("job_id", "") or "")
        credits = final_data.get("credits_charged")
        detail_text = f"验证完成，状态: {status}"
        if credits is not None:
            detail_text += f" | credits_charged={credits}"

        self._set_results_verify_progress_state(
            status_text=f"完成: {status}",
            detail_text=detail_text,
            percent=100,
            job_id=job_id,
            target_link=self._get_selected_results_link(),
        )
        self._set_results_verify_controls_enabled(True)
        self._append_system_log("INFO", "UI", "-", f"SheerIDBot 验证完成: status={status} job_id={job_id or '-'}")

    def _on_results_verify_skipped(self, payload: dict) -> None:
        message = str(payload.get("message", "已跳过验证"))
        self._set_results_verify_progress_state(
            status_text="已跳过",
            detail_text=message,
            percent=0,
            job_id="",
            target_link=self._get_selected_results_link(),
        )
        self._set_results_verify_controls_enabled(True)
        self._append_system_log("INFO", "UI", "-", message)

    def _on_results_verify_error(self, message: str) -> None:
        self._set_results_verify_progress_state(
            status_text="验证失败",
            detail_text=message or "未知错误",
            percent=0,
            job_id=self._extract_job_id_from_label(),
            target_link=self._get_selected_results_link(),
        )
        self._set_results_verify_controls_enabled(True)
        self._append_system_log("ERROR", "UI", "-", f"SheerIDBot 验证失败: {message}")
        QtWidgets.QMessageBox.warning(self, "验证失败", message or "未知错误")

    def _cleanup_results_verify_worker(self) -> None:
        if self._verify_worker:
            self._verify_worker.deleteLater()
        if self._verify_thread:
            self._verify_thread.deleteLater()
        self._verify_worker = None
        self._verify_thread = None
        self._set_results_verify_controls_enabled(True)

    def _set_results_verify_controls_enabled(self, enabled: bool) -> None:
        if hasattr(self, "results_verify_run_btn"):
            self.results_verify_run_btn.setEnabled(enabled)

    def _set_results_verify_progress_state(
        self,
        *,
        status_text: str,
        detail_text: str,
        percent: int | None,
        job_id: str,
        target_link: str,
    ) -> None:
        if hasattr(self, "results_verify_status_label"):
            self.results_verify_status_label.setText(status_text)
        if hasattr(self, "results_verify_progress_detail_label"):
            self.results_verify_progress_detail_label.setText(detail_text)
        if hasattr(self, "results_verify_job_label"):
            self.results_verify_job_label.setText(f"Job ID: {job_id or '-'}")
        if hasattr(self, "results_verify_target_link_label"):
            self.results_verify_target_link_label.setText(f"当前链接: {target_link or '-'}")
        if hasattr(self, "results_verify_progress_bar"):
            if percent is None:
                self.results_verify_progress_bar.setRange(0, 0)
            else:
                self.results_verify_progress_bar.setRange(0, 100)
                self.results_verify_progress_bar.setValue(max(0, min(100, int(percent))))

    def _extract_job_id_from_label(self) -> str:
        if not hasattr(self, "results_verify_job_label"):
            return ""
        text = self.results_verify_job_label.text().strip()
        if ":" in text:
            return text.split(":", 1)[1].strip()
        return ""

    @staticmethod
    def _extract_first_url(text: str) -> str:
        match = re.search(r"https?://\S+", text)
        return match.group(0) if match else ""

    @staticmethod
    def _extract_email(text: str) -> str:
        match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
        return match.group(0) if match else ""


__all__ = [
    "MainWindowResultsMixin",
]
