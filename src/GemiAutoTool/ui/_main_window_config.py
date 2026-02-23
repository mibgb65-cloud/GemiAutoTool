"""MainWindow global config page and local UI settings persistence."""

import json
import os

from PySide6 import QtCore, QtWidgets

from GemiAutoTool.config import INPUT_DIR, MAX_CONCURRENT_WINDOWS, OUTPUT_DIR, PROJECT_ROOT


class MainWindowGlobalConfigMixin:
    def _ui_settings_file_path(self) -> str:
        return os.path.join(PROJECT_ROOT, "ui_settings.json")

    @staticmethod
    def _default_ui_settings() -> dict[str, object]:
        return {
            "max_concurrent": MAX_CONCURRENT_WINDOWS,
            "auto_scroll_log": True,
            "clear_task_table_on_start": True,
            "theme_mode": "auto",
            "input_dir": INPUT_DIR,
            "output_dir": OUTPUT_DIR,
        }

    def _load_local_ui_settings(self) -> dict[str, object]:
        data = dict(self._default_ui_settings())
        path = self._ui_settings_file_path()
        if not os.path.exists(path):
            return data
        try:
            with open(path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                data.update(loaded)
                # 兼容旧版本配置：dark_mode(bool) -> theme_mode(str)
                if "theme_mode" not in loaded and "dark_mode" in loaded:
                    data["theme_mode"] = "dark" if self._safe_bool(loaded.get("dark_mode"), False) else "light"
        except Exception:
            # 启动阶段不弹窗，避免配置损坏影响 UI 打开；使用默认值继续运行。
            return dict(self._default_ui_settings())
        return data

    def _apply_global_config_to_widgets(self) -> None:
        max_concurrent = self._safe_int(self._ui_settings.get("max_concurrent"), MAX_CONCURRENT_WINDOWS)
        max_concurrent = max(1, min(32, max_concurrent))
        auto_scroll = self._safe_bool(self._ui_settings.get("auto_scroll_log"), True)
        auto_clear = self._safe_bool(self._ui_settings.get("clear_task_table_on_start"), True)
        theme_mode = self._normalize_theme_mode(self._ui_settings.get("theme_mode"))
        input_dir = self._normalize_dir_path(self._ui_settings.get("input_dir"), INPUT_DIR)
        output_dir = self._normalize_dir_path(self._ui_settings.get("output_dir"), OUTPUT_DIR)

        self.concurrency_spin.setValue(max_concurrent)
        self.auto_scroll_log_check.setChecked(auto_scroll)
        self.clear_task_table_on_start_check.setChecked(auto_clear)
        self.input_dir_edit.setText(input_dir)
        self.output_dir_edit.setText(output_dir)
        theme_index = self.theme_mode_combo.findData(theme_mode)
        self.theme_mode_combo.setCurrentIndex(theme_index if theme_index >= 0 else 0)
        self._apply_theme_mode(theme_mode)
        self._refresh_home_header_summary()

    def _collect_global_config_from_widgets(self) -> dict[str, object]:
        input_dir = self._normalize_dir_path(self.input_dir_edit.text(), INPUT_DIR)
        output_dir = self._normalize_dir_path(self.output_dir_edit.text(), OUTPUT_DIR)
        return {
            "max_concurrent": int(self.concurrency_spin.value()),
            "auto_scroll_log": bool(self.auto_scroll_log_check.isChecked()),
            "clear_task_table_on_start": bool(self.clear_task_table_on_start_check.isChecked()),
            "theme_mode": str(self.theme_mode_combo.currentData() or "auto"),
            "input_dir": input_dir,
            "output_dir": output_dir,
        }

    def _save_global_config_to_local(self) -> None:
        self._ui_settings = self._collect_global_config_from_widgets()
        input_dir = str(self._ui_settings.get("input_dir") or INPUT_DIR)
        output_dir = str(self._ui_settings.get("output_dir") or OUTPUT_DIR)
        if not input_dir.strip():
            QtWidgets.QMessageBox.warning(self, "保存失败", "输入目录不能为空。")
            return
        if not output_dir.strip():
            QtWidgets.QMessageBox.warning(self, "保存失败", "输出目录不能为空。")
            return
        try:
            os.makedirs(input_dir, exist_ok=True)
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            self._append_system_log("ERROR", "UI", "-", f"创建配置目录失败: {e}")
            QtWidgets.QMessageBox.warning(self, "保存失败", f"创建目录失败\n\n{e}")
            return
        path = self._ui_settings_file_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self._ui_settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self._append_system_log("ERROR", "UI", "-", f"保存全局配置失败: {e}")
            QtWidgets.QMessageBox.warning(self, "保存失败", f"保存全局配置失败\n\n{e}")
            return

        self._refresh_home_header_summary()
        self._append_system_log("INFO", "UI", "-", f"全局配置已保存: {path}")
        QtWidgets.QMessageBox.information(self, "保存成功", f"全局配置已保存到本地。\n\n{path}")

    def _reload_global_config_from_local(self) -> None:
        self._ui_settings = self._load_local_ui_settings()
        self._apply_global_config_to_widgets()
        self._append_system_log("INFO", "UI", "-", "已重新加载本地全局配置")
        QtWidgets.QMessageBox.information(self, "已重新加载", "已从本地配置文件重新加载全局配置。")

    def _reset_global_config_to_defaults(self) -> None:
        self._ui_settings = dict(self._default_ui_settings())
        self._apply_global_config_to_widgets()
        self._append_system_log("INFO", "UI", "-", "已恢复默认全局配置（尚未保存）")
        QtWidgets.QMessageBox.information(self, "已恢复默认", "已恢复默认配置，请点击“保存全局配置到本地”生效持久化。")

    def _refresh_home_header_summary(self) -> None:
        if not hasattr(self, "home_runtime_label"):
            return
        concurrency = self.concurrency_spin.value() if hasattr(self, "concurrency_spin") else MAX_CONCURRENT_WINDOWS
        auto_scroll = "开" if getattr(self, "auto_scroll_log_check", None) and self.auto_scroll_log_check.isChecked() else "关"
        auto_clear = (
            "开"
            if getattr(self, "clear_task_table_on_start_check", None)
            and self.clear_task_table_on_start_check.isChecked()
            else "关"
        )
        theme_name_map = {"auto": "自动", "light": "亮色", "dark": "暗色"}
        theme_mode = "auto"
        if getattr(self, "theme_mode_combo", None):
            theme_mode = str(self.theme_mode_combo.currentData() or "auto")
        theme_name = theme_name_map.get(theme_mode, theme_mode)
        self.home_runtime_label.setText(
            f"默认并发: {concurrency}  |  日志自动滚动: {auto_scroll}  |  启动前清空任务表: {auto_clear}  |  主题: {theme_name}"
        )
        self.home_path_info_label.setText(f"输入目录: {self._get_configured_input_dir()}")
        self.home_output_info_label.setText(f"输出目录: {self._get_configured_output_dir()}")

    def _get_configured_input_dir(self) -> str:
        if hasattr(self, "input_dir_edit"):
            return self._normalize_dir_path(self.input_dir_edit.text(), INPUT_DIR)
        return self._normalize_dir_path(self._ui_settings.get("input_dir"), INPUT_DIR)

    def _get_configured_output_dir(self) -> str:
        if hasattr(self, "output_dir_edit"):
            return self._normalize_dir_path(self.output_dir_edit.text(), OUTPUT_DIR)
        return self._normalize_dir_path(self._ui_settings.get("output_dir"), OUTPUT_DIR)

    @staticmethod
    def _safe_int(value: object, default: int) -> int:
        try:
            return int(value)  # type: ignore[arg-type]
        except Exception:
            return default

    @staticmethod
    def _safe_bool(value: object, default: bool) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"1", "true", "yes", "on"}:
                return True
            if lowered in {"0", "false", "no", "off"}:
                return False
        return default

    @staticmethod
    def _normalize_dir_path(value: object, fallback: str) -> str:
        raw = str(value).strip() if value is not None else ""
        if not raw:
            raw = fallback
        return os.path.abspath(os.path.expanduser(raw))

    def _build_global_config_page(self) -> QtWidgets.QWidget:
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        container = QtWidgets.QWidget()
        container_layout = QtWidgets.QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(10)

        container_layout.addWidget(self._build_global_runtime_group())
        container_layout.addWidget(self._build_global_paths_group())
        container_layout.addWidget(self._build_global_config_actions())
        container_layout.addStretch(1)

        scroll.setWidget(container)
        layout.addWidget(scroll)
        return page

    def _build_global_runtime_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("运行配置（本地保存）")
        grid = QtWidgets.QGridLayout(group)
        grid.setColumnStretch(1, 1)

        self.concurrency_spin = QtWidgets.QSpinBox()
        self.concurrency_spin.setRange(1, 32)
        self.concurrency_spin.valueChanged.connect(self._refresh_home_header_summary)

        self.theme_mode_combo = QtWidgets.QComboBox()
        self.theme_mode_combo.addItem("自动（跟随系统）", "auto")
        self.theme_mode_combo.addItem("亮色", "light")
        self.theme_mode_combo.addItem("暗色", "dark")
        self.theme_mode_combo.currentIndexChanged.connect(self._on_theme_mode_changed)
        self.theme_mode_combo.currentIndexChanged.connect(self._refresh_home_header_summary)

        self.auto_scroll_log_check = QtWidgets.QCheckBox("日志面板自动滚动到底部")
        self.clear_task_table_on_start_check = QtWidgets.QCheckBox("每次开始前自动清空任务表")
        self.auto_scroll_log_check.toggled.connect(self._refresh_home_header_summary)
        self.clear_task_table_on_start_check.toggled.connect(self._refresh_home_header_summary)

        grid.addWidget(QtWidgets.QLabel("默认并发数"), 0, 0)
        grid.addWidget(self.concurrency_spin, 0, 1)
        grid.addWidget(QtWidgets.QLabel("主题模式"), 1, 0)
        grid.addWidget(self.theme_mode_combo, 1, 1)
        grid.addWidget(self.auto_scroll_log_check, 2, 0, 1, 2)
        grid.addWidget(self.clear_task_table_on_start_check, 3, 0, 1, 2)
        return group

    def _build_global_paths_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("目录信息（项目配置）")
        grid = QtWidgets.QGridLayout(group)

        self.input_dir_edit = QtWidgets.QLineEdit(INPUT_DIR)
        self.input_dir_edit.setClearButtonEnabled(True)
        self.input_dir_edit.textChanged.connect(self._refresh_home_header_summary)
        self.output_dir_edit = QtWidgets.QLineEdit(OUTPUT_DIR)
        self.output_dir_edit.setClearButtonEnabled(True)
        self.output_dir_edit.textChanged.connect(self._refresh_home_header_summary)

        browse_input_btn = QtWidgets.QPushButton("选择输入目录")
        browse_output_btn = QtWidgets.QPushButton("选择输出目录")
        open_input_btn = QtWidgets.QPushButton("打开")
        open_output_btn = QtWidgets.QPushButton("打开")
        reset_dirs_btn = QtWidgets.QPushButton("恢复默认目录")
        browse_input_btn.clicked.connect(self._browse_input_dir)
        browse_output_btn.clicked.connect(self._browse_output_dir)
        open_input_btn.clicked.connect(lambda: self._open_directory(self._get_configured_input_dir()))
        open_output_btn.clicked.connect(lambda: self._open_directory(self._get_configured_output_dir()))
        reset_dirs_btn.clicked.connect(self._reset_directory_widgets_to_defaults)

        tip = QtWidgets.QLabel("说明：这里配置 UI/运行使用的 input/output 目录，保存后会写入本地配置并用于后续运行。")
        tip.setWordWrap(True)
        tip.setStyleSheet("color: #909399;")

        grid.addWidget(QtWidgets.QLabel("输入目录"), 0, 0)
        grid.addWidget(self.input_dir_edit, 0, 1)
        grid.addWidget(browse_input_btn, 0, 2)
        grid.addWidget(open_input_btn, 0, 3)
        grid.addWidget(QtWidgets.QLabel("输出目录"), 1, 0)
        grid.addWidget(self.output_dir_edit, 1, 1)
        grid.addWidget(browse_output_btn, 1, 2)
        grid.addWidget(open_output_btn, 1, 3)
        grid.addWidget(reset_dirs_btn, 2, 0, 1, 4)
        grid.addWidget(tip, 3, 0, 1, 4)
        return group

    def _build_global_config_actions(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("配置操作")
        layout = QtWidgets.QVBoxLayout(group)
        layout.setSpacing(8)

        btn_grid = QtWidgets.QGridLayout()
        btn_grid.setHorizontalSpacing(8)
        btn_grid.setVerticalSpacing(8)
        self.save_global_config_btn = QtWidgets.QPushButton("保存全局配置到本地")
        self.save_global_config_btn.setObjectName("btnPrimary")
        reload_btn = QtWidgets.QPushButton("重新加载本地配置")
        reset_btn = QtWidgets.QPushButton("恢复默认配置")

        self.save_global_config_btn.clicked.connect(self._save_global_config_to_local)
        reload_btn.clicked.connect(self._reload_global_config_from_local)
        reset_btn.clicked.connect(self._reset_global_config_to_defaults)

        btn_grid.addWidget(self.save_global_config_btn, 0, 0)
        btn_grid.addWidget(reload_btn, 0, 1)
        btn_grid.addWidget(reset_btn, 1, 0)
        btn_grid.setColumnStretch(0, 1)
        btn_grid.setColumnStretch(1, 1)

        self.global_config_path_label = QtWidgets.QLabel(f"配置文件: {self._ui_settings_file_path()}")
        self.global_config_path_label.setWordWrap(True)
        self.global_config_path_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        self.global_config_path_label.setStyleSheet("color: #909399;")
        self.global_config_hint_label = QtWidgets.QLabel("修改后点击“保存全局配置到本地”，下次启动会自动加载。")
        self.global_config_hint_label.setWordWrap(True)
        self.global_config_hint_label.setStyleSheet("color: #606266;")

        layout.addLayout(btn_grid)
        layout.addWidget(self.global_config_hint_label)
        layout.addWidget(self.global_config_path_label)
        return group

    def _on_theme_mode_changed(self, _index: int) -> None:
        self._apply_theme_mode(str(self.theme_mode_combo.currentData() or "auto"))

    @staticmethod
    def _normalize_theme_mode(value: object) -> str:
        if isinstance(value, str):
            mode = value.strip().lower()
            if mode in {"auto", "light", "dark"}:
                return mode
        return "auto"

    def _browse_input_dir(self) -> None:
        selected = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "选择输入目录",
            self._get_configured_input_dir(),
        )
        if selected:
            self.input_dir_edit.setText(self._normalize_dir_path(selected, INPUT_DIR))

    def _browse_output_dir(self) -> None:
        selected = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "选择输出目录",
            self._get_configured_output_dir(),
        )
        if selected:
            self.output_dir_edit.setText(self._normalize_dir_path(selected, OUTPUT_DIR))

    def _reset_directory_widgets_to_defaults(self) -> None:
        self.input_dir_edit.setText(self._normalize_dir_path(INPUT_DIR, INPUT_DIR))
        self.output_dir_edit.setText(self._normalize_dir_path(OUTPUT_DIR, OUTPUT_DIR))



__all__ = [
    "MainWindowGlobalConfigMixin",
]
