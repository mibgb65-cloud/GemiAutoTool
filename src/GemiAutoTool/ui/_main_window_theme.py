"""MainWindow theme and display formatting helpers."""

from datetime import datetime

from PySide6 import QtGui, QtWidgets


class MainWindowThemeMixin:
    def _apply_modern_theme(self) -> None:
        self._apply_theme_mode("auto")

    def _apply_theme_mode(self, mode: str | bool) -> None:
        # 设置全局现代字体，优先使用微软雅黑或系统默认无衬线字体
        font = QtGui.QFont("Microsoft YaHei", 10)
        font.setStyleHint(QtGui.QFont.StyleHint.SansSerif)
        self.setFont(font)
        theme_mode = self._normalize_theme_mode_value(mode)
        use_dark = self._should_use_dark_theme(theme_mode)
        self.setStyleSheet(self._dark_theme_stylesheet() if use_dark else self._light_theme_stylesheet())

    @staticmethod
    def _normalize_theme_mode_value(mode: str | bool) -> str:
        if isinstance(mode, bool):
            return "dark" if mode else "light"
        normalized = str(mode).strip().lower()
        if normalized in {"auto", "light", "dark"}:
            return normalized
        return "auto"

    def _should_use_dark_theme(self, theme_mode: str) -> bool:
        if theme_mode == "dark":
            return True
        if theme_mode == "light":
            return False
        return self._detect_system_dark_mode()

    def _detect_system_dark_mode(self) -> bool:
        app = QtWidgets.QApplication.instance()
        palette = app.palette() if app else self.palette()
        window_color = palette.color(QtGui.QPalette.ColorRole.Window)
        text_color = palette.color(QtGui.QPalette.ColorRole.WindowText)
        # 优先用窗口背景亮度判断；文本亮于背景时也倾向暗色主题
        return window_color.lightness() < 128 or text_color.lightness() > window_color.lightness()

    @staticmethod
    def _light_theme_stylesheet() -> str:
        return """
        /* 全局背景与文字 */
        QWidget {
            background-color: #f5f7fa;
            color: #303133;
            font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
        }

        /* 输入框 & 微调框 */
        QLineEdit, QSpinBox, QPlainTextEdit, QTextEdit {
            background-color: #ffffff;
            border: 1px solid #dcdfe6;
            border-radius: 4px;
            padding: 5px 8px;
            selection-background-color: #409eff;
        }
        QLineEdit:focus, QSpinBox:focus, QPlainTextEdit:focus, QTextEdit:focus {
            border: 1px solid #409eff;
        }
        QLineEdit[readOnly="true"] {
            background-color: #f2f6fc;
            color: #909399;
        }

        /* 按钮通用样式 */
        QPushButton {
            background-color: #ffffff;
            border: 1px solid #dcdfe6;
            color: #606266;
            border-radius: 4px;
            padding: 6px 16px;
            font-weight: 500;
        }
        QPushButton:hover {
            color: #409eff;
            border-color: #c6e2ff;
            background-color: #ecf5ff;
        }
        QPushButton:pressed {
            color: #3a8ee6;
            border-color: #3a8ee6;
        }
        QPushButton:disabled {
            background-color: #f5f7fa;
            border-color: #e4e7ed;
            color: #c0c4cc;
        }

        /* 特殊按钮：主按钮 (开始) 和 危险按钮 (停止) */
        QPushButton#btnPrimary {
            background-color: #409eff;
            border-color: #409eff;
            color: white;
        }
        QPushButton#btnPrimary:hover {
            background-color: #66b1ff;
            border-color: #66b1ff;
        }
        QPushButton#btnDanger {
            background-color: #f56c6c;
            border-color: #f56c6c;
            color: white;
        }
        QPushButton#btnDanger:hover {
            background-color: #f78989;
            border-color: #f78989;
        }
        QPushButton#btnDanger:disabled {
            background-color: #fab6b6;
            border-color: #fab6b6;
        }

        /* 首页工具头部 */
        QFrame#appHero {
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 #ffffff,
                stop:1 #f3f8ff
            );
            border: 1px solid #d9ecff;
            border-radius: 10px;
        }
        QLabel#appHeroTitle {
            font-size: 20px;
            font-weight: 700;
            color: #1f2d3d;
        }
        QLabel#appHeroSubtitle {
            color: #607d8b;
        }
        QLabel#appHeroMeta {
            color: #409eff;
            font-weight: 600;
        }
        QFrame#appHeroInfo {
            background-color: #ffffff;
            border: 1px solid #e4e7ed;
            border-radius: 8px;
        }
        QLabel#appHeroInfoText {
            color: #606266;
        }

        /* 分组框 (GroupBox) */
        QGroupBox {
            font-weight: bold;
            border: 1px solid #ebeef5;
            border-radius: 6px;
            margin-top: 18px;
            padding-top: 6px;
            background-color: #ffffff;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 10px;
            top: 1px;
            padding: 0 6px;
            background-color: #f5f7fa;
            color: #303133;
        }

        /* 选项卡 (TabWidget) */
        QTabWidget::pane {
            border: 1px solid #e4e7ed;
            background: #ffffff;
            border-radius: 4px;
        }
        QTabBar::tab {
            background: #f5f7fa;
            border: 1px solid #e4e7ed;
            border-bottom: none;
            padding: 8px 20px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            color: #909399;
        }
        QTabBar::tab:selected {
            background: #ffffff;
            color: #409eff;
            font-weight: bold;
            border-bottom: 2px solid #409eff;
        }
        QTabBar::tab:hover:!selected {
            color: #409eff;
        }

        /* 表格组件 (TableWidget) */
        QTableWidget {
            background-color: #ffffff;
            alternate-background-color: #fafafa;
            border: none;
            gridline-color: #ebeef5;
            selection-background-color: #ecf5ff;
            selection-color: #409eff;
        }
        QHeaderView::section {
            background-color: #f5f7fa;
            color: #606266;
            padding: 6px;
            border: none;
            border-right: 1px solid #ebeef5;
            border-bottom: 1px solid #ebeef5;
            font-weight: bold;
        }

        /* 进度条 */
        QProgressBar {
            border: none;
            background-color: #ebeef5;
            border-radius: 6px;
            text-align: center;
            color: #303133;
            font-weight: bold;
        }
        QProgressBar::chunk {
            background-color: #67c23a;
            border-radius: 6px;
        }

        /* 分割线 (Splitter) */
        QSplitter::handle {
            background-color: #e4e7ed;
            margin: 2px;
        }

        QCheckBox {
            spacing: 6px;
        }
        """

    @staticmethod
    def _dark_theme_stylesheet() -> str:
        return """
        QWidget {
            background-color: #111827;
            color: #e5e7eb;
            font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
        }

        QLineEdit, QSpinBox, QPlainTextEdit, QTextEdit {
            background-color: #1f2937;
            border: 1px solid #374151;
            border-radius: 4px;
            padding: 5px 8px;
            color: #e5e7eb;
            selection-background-color: #2563eb;
        }
        QLineEdit:focus, QSpinBox:focus, QPlainTextEdit:focus, QTextEdit:focus {
            border: 1px solid #60a5fa;
        }
        QLineEdit[readOnly="true"] {
            background-color: #1b2430;
            color: #9ca3af;
        }

        QPushButton {
            background-color: #1f2937;
            border: 1px solid #374151;
            color: #d1d5db;
            border-radius: 4px;
            padding: 6px 16px;
            font-weight: 500;
        }
        QPushButton:hover {
            color: #bfdbfe;
            border-color: #60a5fa;
            background-color: #1e3a8a;
        }
        QPushButton:pressed {
            border-color: #93c5fd;
        }
        QPushButton:disabled {
            background-color: #111827;
            border-color: #1f2937;
            color: #6b7280;
        }

        QPushButton#btnPrimary {
            background-color: #2563eb;
            border-color: #2563eb;
            color: white;
        }
        QPushButton#btnPrimary:hover {
            background-color: #3b82f6;
            border-color: #3b82f6;
        }
        QPushButton#btnDanger {
            background-color: #dc2626;
            border-color: #dc2626;
            color: white;
        }
        QPushButton#btnDanger:hover {
            background-color: #ef4444;
            border-color: #ef4444;
        }
        QPushButton#btnDanger:disabled {
            background-color: #7f1d1d;
            border-color: #7f1d1d;
            color: #fecaca;
        }

        QFrame#appHero {
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 #1f2937,
                stop:1 #0f172a
            );
            border: 1px solid #334155;
            border-radius: 10px;
        }
        QLabel#appHeroTitle {
            font-size: 20px;
            font-weight: 700;
            color: #f9fafb;
        }
        QLabel#appHeroSubtitle {
            color: #cbd5e1;
        }
        QLabel#appHeroMeta {
            color: #93c5fd;
            font-weight: 600;
        }
        QFrame#appHeroInfo {
            background-color: #111827;
            border: 1px solid #334155;
            border-radius: 8px;
        }
        QLabel#appHeroInfoText {
            color: #cbd5e1;
        }

        QGroupBox {
            font-weight: bold;
            border: 1px solid #334155;
            border-radius: 6px;
            margin-top: 18px;
            padding-top: 6px;
            background-color: #0f172a;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 10px;
            top: 1px;
            padding: 0 6px;
            background-color: #111827;
            color: #e5e7eb;
        }

        QTabWidget::pane {
            border: 1px solid #334155;
            background: #0f172a;
            border-radius: 4px;
        }
        QTabBar::tab {
            background: #1f2937;
            border: 1px solid #334155;
            border-bottom: none;
            padding: 8px 20px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            color: #94a3b8;
        }
        QTabBar::tab:selected {
            background: #0f172a;
            color: #93c5fd;
            font-weight: bold;
            border-bottom: 2px solid #3b82f6;
        }
        QTabBar::tab:hover:!selected {
            color: #bfdbfe;
        }

        QTableWidget {
            background-color: #0f172a;
            alternate-background-color: #111827;
            border: none;
            gridline-color: #243244;
            selection-background-color: #1d4ed8;
            selection-color: #eff6ff;
        }
        QHeaderView::section {
            background-color: #1f2937;
            color: #cbd5e1;
            padding: 6px;
            border: none;
            border-right: 1px solid #334155;
            border-bottom: 1px solid #334155;
            font-weight: bold;
        }

        QProgressBar {
            border: none;
            background-color: #1f2937;
            border-radius: 6px;
            text-align: center;
            color: #e5e7eb;
            font-weight: bold;
        }
        QProgressBar::chunk {
            background-color: #22c55e;
            border-radius: 6px;
        }

        QSplitter::handle {
            background-color: #334155;
            margin: 2px;
        }

        QCheckBox {
            spacing: 6px;
        }
        """

    @staticmethod
    def _now_text() -> str:
        return datetime.now().strftime("%H:%M:%S")

    @staticmethod
    def _display_result_text(result_kind: str, business_status: str) -> str:
        kind = (result_kind or "").lower()
        if kind == "success":
            return f"成功 | {business_status or '已订阅'}"
        if kind == "failed":
            return f"失败 | {business_status or '业务失败'}"
        if kind == "login_failed":
            return "失败 | 登录失败"
        if kind == "needs_verify":
            return f"需验证 | {business_status or '需验证'}"
        if kind == "crashed":
            return "崩溃 | 线程异常"
        if kind == "other":
            return f"其他 | {business_status}" if business_status else "其他"
        if business_status:
            return business_status
        return ""



__all__ = [
    "MainWindowThemeMixin",
]
