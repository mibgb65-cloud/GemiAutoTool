"""MainWindow data-config page, card table editing, file IO and validation helpers."""

import os
import re

from PySide6 import QtCore, QtGui, QtWidgets

class CardTableDelegate(QtWidgets.QStyledItemDelegate):
    """Restrict card table cell input to expected formats."""

    def createEditor(self, parent, option, index):  # type: ignore[override]
        editor = QtWidgets.QLineEdit(parent)
        column = index.column()
        editor.setFrame(False)

        if column == 0:
            editor.setPlaceholderText("12-19位数字")
            editor.setMaxLength(19)
            pattern = QtCore.QRegularExpression(r"\d{0,19}")
            editor.setValidator(QtGui.QRegularExpressionValidator(pattern, editor))
        elif column == 1:
            editor.setPlaceholderText("3/4位")
            editor.setMaxLength(4)
            pattern = QtCore.QRegularExpression(r"\d{0,4}")
            editor.setValidator(QtGui.QRegularExpressionValidator(pattern, editor))
            editor.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        elif column == 2:
            editor.setPlaceholderText("MM")
            editor.setMaxLength(2)
            pattern = QtCore.QRegularExpression(r"\d{0,2}")
            editor.setValidator(QtGui.QRegularExpressionValidator(pattern, editor))
            editor.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        elif column == 3:
            editor.setPlaceholderText("YY/YYYY")
            editor.setMaxLength(4)
            pattern = QtCore.QRegularExpression(r"\d{0,4}")
            editor.setValidator(QtGui.QRegularExpressionValidator(pattern, editor))
            editor.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        return editor



class MainWindowDataMixin:
    def _build_data_config_page(self) -> QtWidgets.QWidget:
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        action_bar = QtWidgets.QWidget()
        action_layout = QtWidgets.QHBoxLayout(action_bar)
        action_layout.setContentsMargins(0, 0, 0, 0)

        load_btn = QtWidgets.QPushButton("加载输入文件")
        validate_save_btn = QtWidgets.QPushButton("校验并保存")
        import_accounts_btn = QtWidgets.QPushButton("导入账号文件(覆盖)")
        append_accounts_btn = QtWidgets.QPushButton("追加账号文件")
        open_input_btn = QtWidgets.QPushButton("打开输入目录")

        load_btn.clicked.connect(self._load_input_data_files)
        validate_save_btn.clicked.connect(self._validate_and_save_input_data_files)
        import_accounts_btn.clicked.connect(lambda: self._import_account_file(append=False))
        append_accounts_btn.clicked.connect(lambda: self._import_account_file(append=True))
        open_input_btn.clicked.connect(lambda: self._open_directory(self._get_configured_input_dir()))

        action_layout.addWidget(load_btn)
        action_layout.addWidget(validate_save_btn)
        action_layout.addWidget(import_accounts_btn)
        action_layout.addWidget(append_accounts_btn)
        action_layout.addWidget(open_input_btn)
        action_layout.addStretch(1)

        self.data_stats_label = QtWidgets.QLabel("未加载")
        self.data_stats_label.setStyleSheet("color: #555;")

        self.data_tabs = QtWidgets.QTabWidget()
        self._data_editors["account.txt"] = self._create_data_editor(
            "每行一个账号，格式: email----password----recovery_email----2fa_secret"
        )
        self._data_editors["name.txt"] = self._create_data_editor("每行一个姓名")
        self._data_editors["zip_code.txt"] = self._create_data_editor("每行一个邮编")
        self.card_table = self._create_card_table()

        self.data_tabs.addTab(self._wrap_editor_tab(self._data_editors["account.txt"]), "账号 account.txt")
        self.data_tabs.addTab(self._build_card_data_tab(), "银行卡 card.txt")
        self.data_tabs.addTab(self._wrap_editor_tab(self._data_editors["name.txt"]), "姓名 name.txt")
        self.data_tabs.addTab(self._wrap_editor_tab(self._data_editors["zip_code.txt"]), "邮编 zip_code.txt")

        layout.addWidget(action_bar)
        layout.addWidget(self.data_stats_label)
        layout.addWidget(self.data_tabs, stretch=1)
        return page

    def _create_data_editor(self, placeholder: str) -> QtWidgets.QPlainTextEdit:
        editor = QtWidgets.QPlainTextEdit()
        font = QtGui.QFont("Consolas")
        font.setStyleHint(QtGui.QFont.StyleHint.Monospace)
        editor.setFont(font)
        editor.setPlaceholderText(placeholder)
        editor.textChanged.connect(self._refresh_input_data_stats)
        return editor

    def _create_card_table(self) -> QtWidgets.QTableWidget:
        table = QtWidgets.QTableWidget(0, 4)
        table.setHorizontalHeaderLabels(["卡号 PAN", "CVV", "月份 MM", "年份 YY"])
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setItemDelegate(CardTableDelegate(table))
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        table.horizontalHeader().setStretchLastSection(False)
        table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        table.itemChanged.connect(lambda *_: self._refresh_input_data_stats())
        return table

    def _build_card_data_tab(self) -> QtWidgets.QWidget:
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        tip = QtWidgets.QLabel("结构化录入银行卡信息，保存时会自动转换为固定格式：[pan:..., cvv:..., exp_month:MM/YY]")
        tip.setStyleSheet("color: #606266;")

        toolbar = QtWidgets.QWidget()
        toolbar_layout = QtWidgets.QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        add_row_btn = QtWidgets.QPushButton("新增卡片")
        remove_row_btn = QtWidgets.QPushButton("删除选中")
        clear_rows_btn = QtWidgets.QPushButton("清空卡片")
        toolbar_layout.addWidget(add_row_btn)
        toolbar_layout.addWidget(remove_row_btn)
        toolbar_layout.addWidget(clear_rows_btn)
        toolbar_layout.addStretch(1)

        add_row_btn.clicked.connect(self._add_card_row)
        remove_row_btn.clicked.connect(self._remove_selected_card_rows)
        clear_rows_btn.clicked.connect(self._clear_card_rows)

        layout.addWidget(tip)
        layout.addWidget(toolbar)
        layout.addWidget(self.card_table, stretch=1)
        return page

    def _wrap_editor_tab(self, editor: QtWidgets.QPlainTextEdit) -> QtWidgets.QWidget:
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(editor)
        return page

    def _open_directory(self, path: str) -> None:
        try:
            if os.name == "nt":
                os.startfile(path)  # type: ignore[attr-defined]
            else:
                QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(path))
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "打开目录失败", str(e))

    def _input_file_path(self, filename: str) -> str:
        return os.path.join(self._get_configured_input_dir(), filename)

    def _load_input_data_files(self) -> None:
        try:
            for filename, editor in self._data_editors.items():
                path = self._input_file_path(filename)
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as f:
                        editor.setPlainText(f.read())
                else:
                    editor.setPlainText("")
            self._load_card_file_into_table(self._input_file_path("card.txt"))
        except Exception as e:
            self._append_system_log("ERROR", "UI", "-", f"读取输入文件失败: {e}")
            QtWidgets.QMessageBox.warning(self, "读取失败", f"读取输入文件失败\n\n{e}")
            return
        self._refresh_input_data_stats()
        self._append_system_log("INFO", "UI", "-", f"已加载输入目录数据文件: {self._get_configured_input_dir()}")

    def _save_input_data_files(self) -> None:
        try:
            os.makedirs(self._get_configured_input_dir(), exist_ok=True)
            for filename, editor in self._data_editors.items():
                path = self._input_file_path(filename)
                with open(path, "w", encoding="utf-8") as f:
                    text = editor.toPlainText()
                    if text and not text.endswith("\n"):
                        text += "\n"
                    f.write(text)
            card_path = self._input_file_path("card.txt")
            with open(card_path, "w", encoding="utf-8") as f:
                card_text = self._serialize_card_table_to_text()
                f.write(card_text)
        except Exception as e:
            self._append_system_log("ERROR", "UI", "-", f"保存输入文件失败: {e}")
            QtWidgets.QMessageBox.warning(self, "保存失败", str(e))
            return

        self._refresh_input_data_stats()
        self._append_system_log("INFO", "UI", "-", f"已保存输入配置到目录: {self._get_configured_input_dir()}")
        QtWidgets.QMessageBox.information(self, "保存成功", f"输入文件已保存到目录。\n\n{self._get_configured_input_dir()}")

    def _import_account_file(self, append: bool) -> None:
        source_file, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "选择账号文件",
            self._get_configured_input_dir(),
            "Text Files (*.txt);;All Files (*)",
        )
        if not source_file:
            return

        try:
            with open(source_file, "r", encoding="utf-8") as f:
                imported_text = f.read()
        except Exception as e:
            self._append_system_log("ERROR", "UI", "-", f"读取账号导入文件失败: {e}")
            QtWidgets.QMessageBox.warning(self, "导入失败", str(e))
            return

        account_editor = self._data_editors.get("account.txt")
        if account_editor is None:
            return

        if append and account_editor.toPlainText().strip():
            base = account_editor.toPlainText()
            if not base.endswith("\n"):
                base += "\n"
            account_editor.setPlainText(base + imported_text)
            self._append_system_log("INFO", "UI", "-", f"已追加导入账号文件: {source_file}")
        else:
            account_editor.setPlainText(imported_text)
            self._append_system_log("INFO", "UI", "-", f"已覆盖导入账号文件: {source_file}")

        self.data_tabs.setCurrentIndex(0)
        self._refresh_input_data_stats()

    def _refresh_input_data_stats(self) -> None:
        account_lines = self._count_non_empty_lines(self._data_editors.get("account.txt"))
        card_lines = self._count_card_rows()
        name_lines = self._count_non_empty_lines(self._data_editors.get("name.txt"))
        zip_lines = self._count_non_empty_lines(self._data_editors.get("zip_code.txt"))
        self.data_stats_label.setText(
            f"账号 {account_lines} 行 | 银行卡 {card_lines} 行 | 姓名 {name_lines} 行 | 邮编 {zip_lines} 行"
        )

    @staticmethod
    def _count_non_empty_lines(editor: QtWidgets.QPlainTextEdit | None) -> int:
        if editor is None:
            return 0
        return sum(1 for line in editor.toPlainText().splitlines() if line.strip())

    def _count_card_rows(self) -> int:
        count = 0
        for row in range(self.card_table.rowCount()):
            if any((self.card_table.item(row, col).text().strip() if self.card_table.item(row, col) else "") for col in range(4)):
                count += 1
        return count

    def _add_card_row(self, pan: str = "", cvv: str = "", month: str = "", year: str = "") -> None:
        row = self.card_table.rowCount()
        self.card_table.insertRow(row)
        for col, value in enumerate([pan, cvv, month, year]):
            self.card_table.setItem(row, col, QtWidgets.QTableWidgetItem(value))
        self._refresh_input_data_stats()

    def _remove_selected_card_rows(self) -> None:
        selected_rows = sorted({index.row() for index in self.card_table.selectionModel().selectedRows()}, reverse=True)
        if not selected_rows:
            return
        for row in selected_rows:
            self.card_table.removeRow(row)
        self._refresh_input_data_stats()

    def _clear_card_rows(self) -> None:
        self.card_table.setRowCount(0)
        self._refresh_input_data_stats()

    def _load_card_file_into_table(self, card_file_path: str) -> None:
        self.card_table.blockSignals(True)
        try:
            self.card_table.setRowCount(0)
            if not os.path.exists(card_file_path):
                return
            with open(card_file_path, "r", encoding="utf-8") as f:
                for raw_line in f:
                    line = raw_line.strip()
                    if not line:
                        continue
                    parsed = self._parse_card_line(line)
                    if parsed is None:
                        # 保留原行为：不在加载阶段强制报错，校验阶段再提示
                        self._add_card_row("", "", "", "")
                        last_row = self.card_table.rowCount() - 1
                        self.card_table.setItem(last_row, 0, QtWidgets.QTableWidgetItem(line))
                        continue
                    pan, cvv, month, year = parsed
                    self._add_card_row(pan, cvv, month, year)
        finally:
            self.card_table.blockSignals(False)
        self._refresh_input_data_stats()

    def _serialize_card_table_to_text(self) -> str:
        lines: list[str] = []
        for row in range(self.card_table.rowCount()):
            pan = self._table_text(self.card_table, row, 0)
            cvv = self._table_text(self.card_table, row, 1)
            month = self._table_text(self.card_table, row, 2)
            year = self._table_text(self.card_table, row, 3)
            if not any([pan, cvv, month, year]):
                continue
            exp_year = year[-2:] if len(year) >= 2 else year
            month = month.zfill(2) if month else month
            lines.append(f"[pan:{pan}, cvv:{cvv}, exp_month:{month}/{exp_year}]")
        return ("\n".join(lines) + "\n") if lines else ""

    def _validate_card_table(self) -> list[str]:
        issues: list[str] = []
        exp_month_re = re.compile(r"^(0?[1-9]|1[0-2])$")
        exp_year_re = re.compile(r"^\d{2,4}$")
        for row in range(self.card_table.rowCount()):
            line_no = row + 1
            pan = self._table_text(self.card_table, row, 0)
            cvv = self._table_text(self.card_table, row, 1)
            month = self._table_text(self.card_table, row, 2)
            year = self._table_text(self.card_table, row, 3)
            if not any([pan, cvv, month, year]):
                continue
            if not pan:
                issues.append(f"card.txt 第{line_no}行: pan 不能为空")
            elif not pan.isdigit() or not (12 <= len(pan) <= 19):
                issues.append(f"card.txt 第{line_no}行: pan 应为 12-19 位数字")
            if not cvv:
                issues.append(f"card.txt 第{line_no}行: cvv 不能为空")
            elif not cvv.isdigit() or len(cvv) not in (3, 4):
                issues.append(f"card.txt 第{line_no}行: cvv 应为 3 或 4 位数字")
            if not month:
                issues.append(f"card.txt 第{line_no}行: 月份不能为空")
            elif not exp_month_re.match(month):
                issues.append(f"card.txt 第{line_no}行: 月份应为 1-12")
            if not year:
                issues.append(f"card.txt 第{line_no}行: 年份不能为空")
            elif not exp_year_re.match(year):
                issues.append(f"card.txt 第{line_no}行: 年份应为 2 或 4 位数字")
        return issues

    @staticmethod
    def _parse_card_line(line: str) -> tuple[str, str, str, str] | None:
        if not (line.startswith("[") and line.endswith("]")):
            return None
        content = line[1:-1]
        parts = [p.strip() for p in content.split(",") if p.strip()]
        card_dict: dict[str, str] = {}
        try:
            for part in parts:
                k, v = part.split(":", 1)
                card_dict[k.strip()] = v.strip()
            pan = card_dict["pan"]
            cvv = card_dict["cvv"]
            exp = card_dict["exp_month"]
            month, year = exp.split("/", 1)
            return pan, cvv, month, year
        except Exception:
            return None

    @staticmethod
    def _table_text(table: QtWidgets.QTableWidget, row: int, col: int) -> str:
        item = table.item(row, col)
        return item.text().strip() if item and item.text() else ""

    def _validate_input_data_files(self) -> None:
        issues = self._collect_input_data_validation_issues()

        if issues:
            preview = "\n".join(issues[:20])
            more = "" if len(issues) <= 20 else f"\n... 还有 {len(issues) - 20} 条问题未显示"
            msg = f"发现 {len(issues)} 条格式问题：\n\n{preview}{more}"
            self._append_system_log("WARNING", "UI", "-", f"格式校验失败，共 {len(issues)} 条问题")
            QtWidgets.QMessageBox.warning(self, "格式校验失败", msg)
            return

        self._append_system_log("INFO", "UI", "-", "格式校验通过（账号/银行卡/姓名/邮编）")
        QtWidgets.QMessageBox.information(self, "格式校验通过", "未发现格式问题。")

    def _validate_and_save_input_data_files(self) -> None:
        issues = self._collect_input_data_validation_issues()
        if issues:
            preview = "\n".join(issues[:20])
            more = "" if len(issues) <= 20 else f"\n... 还有 {len(issues) - 20} 条问题未显示"
            msg = f"发现 {len(issues)} 条格式问题，未执行保存：\n\n{preview}{more}"
            self._append_system_log("WARNING", "UI", "-", f"校验未通过，取消保存（{len(issues)} 条问题）")
            QtWidgets.QMessageBox.warning(self, "校验未通过", msg)
            return
        self._save_input_data_files()

    def _collect_input_data_validation_issues(self) -> list[str]:
        issues: list[str] = []
        issues.extend(self._validate_account_text(self._editor_text("account.txt")))
        issues.extend(self._validate_card_table())
        issues.extend(self._validate_name_text(self._editor_text("name.txt")))
        issues.extend(self._validate_zip_text(self._editor_text("zip_code.txt")))
        return issues

    def _editor_text(self, filename: str) -> str:
        if filename == "card.txt":
            return self._serialize_card_table_to_text()
        editor = self._data_editors.get(filename)
        return editor.toPlainText() if editor else ""

    def _validate_account_text(self, text: str) -> list[str]:
        issues: list[str] = []
        for i, raw in enumerate(text.splitlines(), start=1):
            line = raw.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split("----")]
            if len(parts) != 4:
                issues.append(f"account.txt 第{i}行: 应为 4 段 (email----password----recovery_email----2fa)")
                continue
            email, password, recovery_email, _secret = parts
            if not email or "@" not in email:
                issues.append(f"account.txt 第{i}行: 邮箱格式看起来不正确")
            if not password:
                issues.append(f"account.txt 第{i}行: 密码为空")
            if recovery_email and "@" not in recovery_email:
                issues.append(f"account.txt 第{i}行: 恢复邮箱格式看起来不正确")
        return issues

    def _validate_name_text(self, text: str) -> list[str]:
        issues: list[str] = []
        for i, raw in enumerate(text.splitlines(), start=1):
            line = raw.strip()
            if not line:
                continue
            if len(line) < 2:
                issues.append(f"name.txt 第{i}行: 姓名过短")
        return issues

    def _validate_zip_text(self, text: str) -> list[str]:
        issues: list[str] = []
        pattern = re.compile(r"^[A-Za-z0-9\- ]{3,12}$")
        for i, raw in enumerate(text.splitlines(), start=1):
            line = raw.strip()
            if not line:
                continue
            if not pattern.match(line):
                issues.append(f"zip_code.txt 第{i}行: 邮编格式看起来不正确")
        return issues



__all__ = [
    "CardTableDelegate",
    "MainWindowDataMixin",
]
