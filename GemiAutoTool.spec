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
# 注意：不要对 PySide6 使用 collect_all()，否则会把 Qt 全家桶（WebEngine/QML/Designer/3D/...）
# 一起打进去，导致 onedir 体积暴涨。这里仅声明项目实际使用到的 Qt 模块。
hiddenimports = []

qt_hiddenimports = [
    "PySide6",
    "shiboken6",
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
]

hiddenimports.extend(qt_hiddenimports)

for package_name in ("selenium", "undetected_chromedriver", "selenium_stealth"):
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
    excludes=[
        # 显式排除高体积但当前 GUI 未使用的 Qt 模块（作为保险）。
        "PySide6.Qt3DAnimation",
        "PySide6.Qt3DCore",
        "PySide6.Qt3DExtras",
        "PySide6.Qt3DInput",
        "PySide6.Qt3DLogic",
        "PySide6.Qt3DRender",
        "PySide6.QtCharts",
        "PySide6.QtDataVisualization",
        "PySide6.QtDesigner",
        "PySide6.QtGraphs",
        "PySide6.QtHelp",
        "PySide6.QtMultimedia",
        "PySide6.QtMultimediaWidgets",
        "PySide6.QtNetworkAuth",
        "PySide6.QtPdf",
        "PySide6.QtPdfWidgets",
        "PySide6.QtPositioning",
        "PySide6.QtQml",
        "PySide6.QtQuick",
        "PySide6.QtQuick3D",
        "PySide6.QtQuickControls2",
        "PySide6.QtQuickTest",
        "PySide6.QtRemoteObjects",
        "PySide6.QtScxml",
        "PySide6.QtSensors",
        "PySide6.QtSerialBus",
        "PySide6.QtSerialPort",
        "PySide6.QtSpatialAudio",
        "PySide6.QtSql",
        "PySide6.QtStateMachine",
        "PySide6.QtSvgWidgets",
        "PySide6.QtTest",
        "PySide6.QtTextToSpeech",
        "PySide6.QtWebChannel",
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineQuick",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebSockets",
        "PySide6.QtXml",
        "PySide6.QtXmlPatterns",
    ],
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
