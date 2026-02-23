# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules


# PyInstaller 执行 spec 时不一定提供 __file__，优先使用其注入的 SPECPATH，
# 再回退到当前工作目录（构建脚本会先 cd 到项目根目录）。
project_root = Path(globals().get("SPECPATH") or Path.cwd()).resolve()
src_root = project_root / "src"
entry_script = src_root / "GemiAutoTool" / "run_gui.py"
icon_path = src_root / "GemiAutoTool" / "ui" / "assets" / "app_icon.ico"

binaries = []
datas = [
    (str(src_root / "GemiAutoTool" / "ui" / "assets"), "GemiAutoTool/ui/assets"),
]

# 打包时显式收集关键依赖（Qt / Selenium / UC），避免运行时缺包。
hiddenimports = []

for package_name in ("PySide6", "shiboken6", "selenium", "undetected_chromedriver", "selenium_stealth"):
    try:
        pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(package_name)
        datas.extend(pkg_datas)
        binaries.extend(pkg_binaries)
        hiddenimports.extend(pkg_hiddenimports)
    except Exception:
        pass

for package_name in ("selenium", "undetected_chromedriver", "selenium_stealth"):
    try:
        hiddenimports.extend(collect_submodules(package_name))
    except Exception:
        # 构建机未安装某个依赖时，不在 spec 解析阶段崩溃；后续由 PyInstaller 输出缺失信息。
        pass

# 确保顶级模块名也在隐藏导入中（某些版本仅收集了子模块列表，运行时仍可能报根模块缺失）
hiddenimports.extend(
    [
        "PySide6",
        "shiboken6",
        "selenium",
        "undetected_chromedriver",
        "selenium_stealth",
    ]
)

# 去重，保持顺序
_seen = set()
hiddenimports = [m for m in hiddenimports if not (m in _seen or _seen.add(m))]


a = Analysis(
    [str(entry_script)],
    pathex=[str(src_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="GemiAutoTool",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icon_path) if icon_path.exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="GemiAutoTool",
)
