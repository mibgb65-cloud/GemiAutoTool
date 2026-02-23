"""MainWindow monitor page, runtime orchestration, log and task table handling."""

import html
from datetime import datetime

from PySide6 import QtCore, QtGui, QtWidgets

from GemiAutoTool.ui.workers import AutomationWorker


class MainWindowMonitorMixin:
    def _build_monitor_page(self) -> QtWidgets.QWidget:
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        main_splitter = self._build_main_splitter()
        layout.addWidget(self._build_monitor_header())
        layout.addWidget(self._build_toolbar())
        layout.addWidget(self._build_summary_group())
        layout.addWidget(main_splitter, stretch=1)
        return page

    def _build_monitor_header(self) -> QtWidgets.QFrame:
        frame = QtWidgets.QFrame()
        frame.setObjectName("appHero")
        layout = QtWidgets.QHBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        left = QtWidgets.QVBoxLayout()
        left.setSpacing(4)
        title = QtWidgets.QLabel("GemiAutoTool")
        title.setObjectName("appHeroTitle")
        subtitle = QtWidgets.QLabel("自动化任务控制台 · 运行监控 / 数据配置 / 结果导出")
        subtitle.setObjectName("appHeroSubtitle")
        self.home_runtime_label = QtWidgets.QLabel()
        self.home_runtime_label.setObjectName("appHeroMeta")
        left.addWidget(title)
        left.addWidget(subtitle)
        left.addWidget(self.home_runtime_label)

        right_box = QtWidgets.QFrame()
        right_box.setObjectName("appHeroInfo")
        right_layout = QtWidgets.QVBoxLayout(right_box)
        right_layout.setContentsMargins(12, 10, 12, 10)
        right_layout.setSpacing(4)
        self.home_path_info_label = QtWidgets.QLabel()
        self.home_path_info_label.setObjectName("appHeroInfoText")
        self.home_output_info_label = QtWidgets.QLabel()
        self.home_output_info_label.setObjectName("appHeroInfoText")
        right_layout.addWidget(self.home_path_info_label)
        right_layout.addWidget(self.home_output_info_label)

        layout.addLayout(left, 1)
        layout.addWidget(right_box, 0)
        return frame

    def _build_toolbar(self) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        self.start_btn = QtWidgets.QPushButton("开始")
        self.start_btn.setObjectName("btnPrimary")
        self.stop_btn = QtWidgets.QPushButton("停止")
        self.stop_btn.setObjectName("btnDanger")
        self.stop_btn.setEnabled(False)
        retry_failed_btn = QtWidgets.QPushButton("重试失败任务")
        clear_log_btn = QtWidgets.QPushButton("清空日志")
        clear_tasks_btn = QtWidgets.QPushButton("清空任务表")
        export_links_btn = QtWidgets.QPushButton("导出 SheerID 链接")
        export_latest_links_btn = QtWidgets.QPushButton("一键导出最近结果链接")

        self.start_btn.clicked.connect(self._start_run)
        self.stop_btn.clicked.connect(self._request_stop)
        retry_failed_btn.clicked.connect(self._retry_failed_tasks)
        clear_log_btn.clicked.connect(self.log_view.clear)
        clear_tasks_btn.clicked.connect(self._clear_task_table)
        export_links_btn.clicked.connect(self._export_sheerid_links_from_file)
        export_latest_links_btn.clicked.connect(self._export_sheerid_links_from_latest_result)

        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)
        layout.addWidget(retry_failed_btn)
        layout.addWidget(clear_log_btn)
        layout.addWidget(clear_tasks_btn)
        layout.addWidget(export_links_btn)
        layout.addWidget(export_latest_links_btn)
        layout.addStretch(1)
        return widget

    def _build_summary_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("运行状态")
        layout = QtWidgets.QVBoxLayout(group)

        top_row = QtWidgets.QHBoxLayout()
        self.summary_label = QtWidgets.QLabel()
        self.run_state_label = QtWidgets.QLabel("空闲")
        self.run_state_label.setStyleSheet("font-weight: 600;")
        top_row.addWidget(self.summary_label, 1)
        top_row.addWidget(QtWidgets.QLabel("当前状态:"))
        top_row.addWidget(self.run_state_label)

        bottom_row = QtWidgets.QHBoxLayout()
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_text_label = QtWidgets.QLabel("0 / 0")
        bottom_row.addWidget(QtWidgets.QLabel("进度"))
        bottom_row.addWidget(self.progress_bar, 1)
        bottom_row.addWidget(self.progress_text_label)

        layout.addLayout(top_row)
        layout.addLayout(bottom_row)
        return group

    def _build_main_splitter(self) -> QtWidgets.QSplitter:
        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_task_group())
        splitter.addWidget(self._build_log_group())
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 4)
        return splitter

    def _build_task_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("任务状态")
        layout = QtWidgets.QVBoxLayout(group)

        self.task_table = QtWidgets.QTableWidget(0, 7)
        self.task_table.setHorizontalHeaderLabels(["任务", "账号", "线程状态", "业务阶段", "最终结果", "详情", "更新时间"])
        self.task_table.horizontalHeader().setStretchLastSection(True)
        self.task_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.task_table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.task_table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.task_table.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.task_table.horizontalHeader().setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.task_table.horizontalHeader().setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.task_table.verticalHeader().setVisible(False)
        self.task_table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.task_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.task_table.setAlternatingRowColors(True)
        layout.addWidget(self.task_table)
        return group

    def _build_log_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("实时日志")
        layout = QtWidgets.QVBoxLayout(group)

        self.log_view = QtWidgets.QTextEdit()
        self.log_view.setReadOnly(True)
        font = QtGui.QFont("Consolas")
        font.setStyleHint(QtGui.QFont.StyleHint.Monospace)
        self.log_view.setFont(font)
        layout.addWidget(self.log_view)
        return group

    def _start_run(self) -> None:
        self._start_run_with_retry_emails(None)

    def _retry_failed_tasks(self) -> None:
        retry_emails = self._collect_retryable_failed_emails()
        if not retry_emails:
            QtWidgets.QMessageBox.information(
                self,
                "无可重试任务",
                "当前任务表中没有可重试的失败任务。\n\n仅会重试“失败/崩溃”，不会重试“需验证”。",
            )
            return
        self._start_run_with_retry_emails(retry_emails)

    def _start_run_with_retry_emails(self, retry_emails: list[str] | None) -> None:
        if self._worker_thread and self._worker_thread.isRunning():
            QtWidgets.QMessageBox.information(self, "提示", "任务正在运行中。")
            return

        if self.clear_task_table_on_start_check.isChecked():
            self._clear_task_table()
        self._scheduled_tasks_total = 0
        input_dir = self._get_configured_input_dir()
        output_dir = self._get_configured_output_dir()
        self._append_system_log("INFO", "UI", "-", f"使用输入目录: {input_dir}")
        self._append_system_log("INFO", "UI", "-", f"使用输出目录: {output_dir}")
        if retry_emails:
            self._append_system_log("INFO", "UI", "-", f"开始失败任务重试（排除需验证），目标账号数: {len(retry_emails)}")
        else:
            self._append_system_log("INFO", "UI", "-", "开始新的任务运行")
        self.run_state_label.setText("启动中...")

        self._worker_thread = QtCore.QThread(self)
        self._worker = AutomationWorker(
            max_concurrent=self.concurrency_spin.value(),
            input_dir=input_dir,
            output_dir=output_dir,
            retry_emails=retry_emails,
        )
        self._worker.moveToThread(self._worker_thread)

        self._worker_thread.started.connect(self._worker.run)
        self._worker.log_record.connect(self._on_log_record)
        self._worker.controller_event.connect(self._on_controller_event)
        self._worker.run_started.connect(self._on_run_started)
        self._worker.run_error.connect(self._on_run_error)
        self._worker.run_finished.connect(self._on_run_finished)
        self._worker.run_finished.connect(lambda _: self._worker_thread.quit())
        self._worker_thread.finished.connect(self._cleanup_worker)

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self._worker_thread.start()

    def _collect_retryable_failed_emails(self) -> list[str]:
        # 对同一邮箱取“最后一次任务状态”，避免历史失败但后续成功仍被重试。
        latest_result_by_email: dict[str, str] = {}
        for state in self._task_state_map.values():
            email = str(state.get("email", "")).strip()
            if not email:
                continue
            latest_result_by_email[email] = str(state.get("result", "")).strip()

        retry_emails: list[str] = []
        for email, result_text in latest_result_by_email.items():
            if result_text.startswith("失败"):
                retry_emails.append(email)
        return retry_emails

    def _request_stop(self) -> None:
        if not self._worker:
            return
        self.run_state_label.setText("停止中...")
        self._append_system_log("WARNING", "UI", "-", "已发送停止请求（等待已启动任务结束）")
        self._worker.request_stop()

    def _on_run_started(self) -> None:
        self.run_state_label.setText("运行中")

    def _on_run_error(self, message: str) -> None:
        self.run_state_label.setText("错误")
        self._append_system_log("ERROR", "Worker", "-", message)

    def _on_run_finished(self, payload: dict) -> None:
        ok = payload.get("ok", False)
        self.run_state_label.setText("空闲" if ok else "结束(失败)")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def _cleanup_worker(self) -> None:
        if self._worker:
            self._worker.deleteLater()
        if self._worker_thread:
            self._worker_thread.deleteLater()
        self._worker = None
        self._worker_thread = None

    def _on_controller_event(self, event: dict) -> None:
        event_type = event.get("type", "")
        if event_type == "run_started":
            self._scheduled_tasks_total = int(event.get("scheduled_tasks", 0) or 0)
            retry_mode = bool(event.get("retry_mode", False))
            retry_part = ""
            if retry_mode:
                retry_part = f" / 重试模式: 是 / 重试候选: {event.get('retry_candidates', 0)}"
            self._append_system_log(
                "INFO",
                "Controller",
                "-",
                (
                    f"计划任务数: {event.get('scheduled_tasks')} / 账号总数: {event.get('total_accounts')}"
                    f" / 输入目录: {event.get('input_dir', '-')}"
                    f" / 输出目录: {event.get('output_dir', '-')}"
                    f"{retry_part}"
                ),
            )
            self._refresh_summary()
            return

        if event_type == "run_error":
            self._append_system_log("ERROR", "Controller", "-", str(event.get("message", "未知错误")))
            return

        if event_type == "stop_requested":
            self._append_system_log("WARNING", "Controller", "-", "控制器已收到停止请求")
            return

        if event_type == "task_scheduled":
            self._upsert_task_row(
                event.get("task_name", "-"),
                event.get("email", "-"),
                thread_status="queued",
                stage="待启动",
            )
            self._refresh_summary()
            return

        if event_type == "task_started":
            self._upsert_task_row(
                event.get("task_name", "-"),
                event.get("email", "-"),
                thread_status="running",
                stage="线程已启动",
            )
            self._refresh_summary()
            return

        if event_type == "task_progress":
            self._upsert_task_row(
                event.get("task_name", "-"),
                event.get("email", "-"),
                stage=str(event.get("stage", "")),
                detail=str(event.get("detail", "")),
            )
            return

        if event_type == "task_business_result":
            result_kind = str(event.get("result_kind", "unknown"))
            self._upsert_task_row(
                event.get("task_name", "-"),
                event.get("email", "-"),
                result=self._display_result_text(result_kind, str(event.get("business_status", ""))),
                detail=str(event.get("detail", "")),
            )
            self._refresh_summary()
            return

        if event_type == "task_finished":
            thread_status = str(event.get("status", "finished"))
            task_name = event.get("task_name", "-")
            email = event.get("email", "-")
            self._upsert_task_row(
                task_name,
                email,
                thread_status=thread_status,
                stage="完成" if thread_status == "finished" else "线程异常",
                result=self._display_result_text(
                    str(event.get("result_kind", "unknown")),
                    str(event.get("business_status", "")),
                ),
                detail=str(event.get("detail", event.get("error", ""))),
            )
            self._refresh_summary()
            return

        if event_type == "run_finished":
            stopped = bool(event.get("stopped", False))
            msg = "运行已停止" if stopped else "运行已完成"
            self._append_system_log("INFO", "Controller", "-", msg)
            return

    def _on_log_record(self, record: dict) -> None:
        self._append_system_log(
            str(record.get("level", "INFO")),
            str(record.get("logger", "log")),
            str(record.get("task_name", "-")),
            str(record.get("message", "")),
            time_text=str(record.get("time", "")),
        )

    def _append_system_log(
        self,
        level: str,
        logger_name: str,
        task_name: str,
        message: str,
        time_text: str | None = None,
    ) -> None:
        colors = {
            "DEBUG": "#4aa3df",
            "INFO": "#2e7d32",
            "WARNING": "#b26a00",
            "ERROR": "#c62828",
            "CRITICAL": "#7b1fa2",
        }
        color = colors.get(level.upper(), "#333333")
        ts = time_text or datetime.now().strftime("%H:%M:%S")
        line = f"{ts} | {level:<8} | task={task_name} | {logger_name} | {message}"
        self.log_view.append(f'<span style="color:{color}">{html.escape(line)}</span>')
        if self.auto_scroll_log_check.isChecked():
            self.log_view.moveCursor(QtGui.QTextCursor.MoveOperation.End)

    def _upsert_task_row(
        self,
        task_name: str,
        email: str,
        *,
        thread_status: str | None = None,
        stage: str | None = None,
        result: str | None = None,
        detail: str | None = None,
    ) -> None:
        row = self._task_rows.get(task_name)
        state = self._task_state_map.setdefault(
            task_name,
            {
                "email": email,
                "thread_status": "",
                "stage": "",
                "result": "",
                "detail": "",
            },
        )
        state["email"] = email or state.get("email", "")
        if thread_status is not None:
            state["thread_status"] = thread_status
        if stage is not None:
            state["stage"] = stage
        if result is not None:
            state["result"] = result
        if detail is not None:
            state["detail"] = detail

        row_values = [
            task_name,
            state["email"],
            state["thread_status"],
            state["stage"],
            state["result"],
            state["detail"],
            self._now_text(),
        ]
        if row is None:
            row = self.task_table.rowCount()
            self.task_table.insertRow(row)
            self._task_rows[task_name] = row
            for col, text in enumerate(row_values):
                self.task_table.setItem(row, col, QtWidgets.QTableWidgetItem(text))
        else:
            for col, text in enumerate(row_values):
                item = self.task_table.item(row, col)
                if item is None:
                    self.task_table.setItem(row, col, QtWidgets.QTableWidgetItem(text))
                else:
                    item.setText(text)

        self._colorize_cells(row, state.get("thread_status", ""), state.get("result", ""))

    def _colorize_cells(self, row: int, thread_status: str, result_text: str) -> None:
        thread_item = self.task_table.item(row, 2)
        result_item = self.task_table.item(row, 4)
        thread_colors = {
            "queued": QtGui.QColor("#616161"),
            "running": QtGui.QColor("#1565c0"),
            "finished": QtGui.QColor("#2e7d32"),
            "crashed": QtGui.QColor("#c62828"),
        }
        if thread_item is not None:
            thread_item.setForeground(thread_colors.get(thread_status, QtGui.QColor("#333333")))

        result_color = QtGui.QColor("#333333")
        if result_text.startswith("成功"):
            result_color = QtGui.QColor("#2e7d32")
        elif result_text.startswith("失败") or result_text.startswith("崩溃"):
            result_color = QtGui.QColor("#c62828")
        elif result_text.startswith("需验证"):
            result_color = QtGui.QColor("#b26a00")
        if result_item is not None:
            result_item.setForeground(result_color)

    def _clear_task_table(self) -> None:
        self.task_table.setRowCount(0)
        self._task_rows.clear()
        self._task_state_map.clear()
        self._scheduled_tasks_total = 0
        self._refresh_summary()

    def _refresh_summary(self) -> None:
        thread_counts = {"queued": 0, "running": 0, "finished": 0, "crashed": 0}
        result_counts = {"success": 0, "failed": 0, "needs_verify": 0, "other": 0}

        for state in self._task_state_map.values():
            thread_status = state.get("thread_status", "")
            if thread_status in thread_counts:
                thread_counts[thread_status] += 1
            result_text = state.get("result", "")
            if result_text.startswith("成功"):
                result_counts["success"] += 1
            elif result_text.startswith("失败") or result_text.startswith("崩溃"):
                result_counts["failed"] += 1
            elif result_text.startswith("需验证"):
                result_counts["needs_verify"] += 1
            elif result_text:
                result_counts["other"] += 1

        completed = thread_counts["finished"] + thread_counts["crashed"]
        total = self._scheduled_tasks_total or len(self._task_state_map)
        progress_percent = int((completed / total) * 100) if total else 0
        self.progress_bar.setValue(progress_percent)
        self.progress_text_label.setText(f"{completed} / {total}")
        self.summary_label.setText(
            f"queued={thread_counts['queued']}  running={thread_counts['running']}  "
            f"finished={thread_counts['finished']}  crashed={thread_counts['crashed']}  "
            f"success={result_counts['success']}  failed={result_counts['failed']}  "
            f"need_verify={result_counts['needs_verify']}"
        )



__all__ = [
    "MainWindowMonitorMixin",
]
