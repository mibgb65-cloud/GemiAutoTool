"""PySide6 main window for GemiAutoTool."""

from PySide6 import QtCore, QtGui, QtWidgets

from GemiAutoTool.config import PROJECT_ROOT
from GemiAutoTool.ui.icon_utils import resolve_app_icon_path
from GemiAutoTool.ui.workers import AutomationWorker
from GemiAutoTool.ui._main_window_config import MainWindowGlobalConfigMixin
from GemiAutoTool.ui._main_window_data import MainWindowDataMixin
from GemiAutoTool.ui._main_window_export import MainWindowExportMixin
from GemiAutoTool.ui._main_window_monitor import MainWindowMonitorMixin
from GemiAutoTool.ui._main_window_results import MainWindowResultsMixin
from GemiAutoTool.ui._main_window_theme import MainWindowThemeMixin


class MainWindow(
    MainWindowGlobalConfigMixin,
    MainWindowDataMixin,
    MainWindowExportMixin,
    MainWindowResultsMixin,
    MainWindowMonitorMixin,
    MainWindowThemeMixin,
    QtWidgets.QMainWindow,
):
    def __init__(self):
        super().__init__()
        self._set_window_icon()
        self.setWindowTitle("GemiAutoTool - UI")
        self.resize(1200, 760)

        self._worker_thread: QtCore.QThread | None = None
        self._worker: AutomationWorker | None = None
        self._task_rows: dict[str, int] = {}
        self._task_state_map: dict[str, dict[str, str]] = {}
        self._current_run_task_names: set[str] = set()
        self._scheduled_tasks_total = 0
        self._launched_tasks_total = 0
        self._stop_requested_in_run = False
        self._last_run_stopped = False
        self._data_editors: dict[str, QtWidgets.QPlainTextEdit] = {}
        self._ui_settings = self._load_local_ui_settings()
        self._init_results_page_state()

        self._build_ui()
        self._apply_modern_theme()
        self._apply_global_config_to_widgets()
        self._refresh_summary()
        self._load_input_data_files()
        self._try_load_results_view_latest(silent=True)

    def _build_ui(self) -> None:
        root = QtWidgets.QWidget(self)
        self.setCentralWidget(root)
        layout = QtWidgets.QVBoxLayout(root)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.page_tabs = QtWidgets.QTabWidget()
        self.page_tabs.addTab(self._build_monitor_page(), "任务监控")
        self.page_tabs.addTab(self._build_data_config_page(), "数据配置")
        self._results_page_widget = self._build_results_page()
        self.page_tabs.addTab(self._results_page_widget, "结果查看")
        self.page_tabs.addTab(self._build_global_config_page(), "全局配置")
        layout.addWidget(self.page_tabs, stretch=1)

        self.statusBar().showMessage(f"项目目录: {PROJECT_ROOT}")

    def _set_window_icon(self) -> None:
        icon_path = resolve_app_icon_path()
        if icon_path:
            self.setWindowIcon(QtGui.QIcon(str(icon_path)))



__all__ = [
    "MainWindow",
]
