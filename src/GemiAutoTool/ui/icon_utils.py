"""UI icon helper utilities."""

import sys
from pathlib import Path


def _candidate_assets_dirs() -> list[Path]:
    candidates: list[Path] = []

    # PyInstaller onefile/onedir extraction base
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass) / "GemiAutoTool" / "ui" / "assets")

    # Running from source / packaged modules
    candidates.append(Path(__file__).resolve().parent / "assets")

    # Packaged executable directory fallback (if assets are next to exe)
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        candidates.append(exe_dir / "GemiAutoTool" / "ui" / "assets")
        candidates.append(exe_dir / "assets")

    # Deduplicate while preserving order
    unique: list[Path] = []
    seen: set[str] = set()
    for path in candidates:
        key = str(path)
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique


def resolve_app_icon_path() -> Path | None:
    """Prefer .ico on Windows packaging/runtime, fallback to .svg."""
    for assets_dir in _candidate_assets_dirs():
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
