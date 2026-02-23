"""UI icon helper utilities."""

from pathlib import Path


def resolve_app_icon_path() -> Path | None:
    """Prefer .ico on Windows packaging/runtime, fallback to .svg."""
    assets_dir = Path(__file__).resolve().parent / "assets"
    ico_path = assets_dir / "app_icon.ico"
    if ico_path.exists():
        return ico_path
    svg_path = assets_dir / "app_icon.svg"
    if svg_path.exists():
        return svg_path
    return None


__all__ = [
    "resolve_app_icon_path",
]
