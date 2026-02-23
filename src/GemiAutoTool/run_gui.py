"""GUI entrypoint for GemiAutoTool."""

import sys

from GemiAutoTool.logging_config import setup_logging
from GemiAutoTool.ui.icon_utils import resolve_app_icon_path

try:
    from PySide6 import QtGui, QtWidgets
except ImportError as e:  # pragma: no cover - runtime environment dependent
    raise SystemExit(
        "缺少 PySide6，请先安装依赖：pip install PySide6"
    ) from e

from GemiAutoTool.ui import MainWindow


def main() -> int:
    setup_logging()
    app = QtWidgets.QApplication(sys.argv)
    icon_path = resolve_app_icon_path()
    if icon_path:
        app.setWindowIcon(QtGui.QIcon(str(icon_path)))
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
