"""Generate app_icon.ico from app_icon.svg using PySide6.

Run with a Python environment that has PySide6 installed:
    python tools/generate_app_icon_ico.py
"""

from pathlib import Path
import sys

from PySide6.QtCore import QRectF
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer


def render_svg_to_image(svg_path: Path, size: int) -> QImage:
    renderer = QSvgRenderer(str(svg_path))
    if not renderer.isValid():
        raise RuntimeError(f"SVG 无法加载: {svg_path}")

    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(0)
    painter = QPainter(image)
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()
    return image


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    assets_dir = project_root / "src" / "GemiAutoTool" / "ui" / "assets"
    svg_path = assets_dir / "app_icon.svg"
    ico_path = assets_dir / "app_icon.ico"

    if not svg_path.exists():
        print(f"未找到 SVG 图标: {svg_path}")
        return 1

    app = QGuiApplication([])
    image = render_svg_to_image(svg_path, 256)

    # Qt 在 Windows 环境通常支持直接保存 ICO；单尺寸 256x256 已足够多数场景。
    if not image.save(str(ico_path), "ICO"):
        print("生成 .ico 失败：当前 Qt 图像插件可能不支持 ICO 输出。")
        return 2

    print(f"已生成图标: {ico_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
