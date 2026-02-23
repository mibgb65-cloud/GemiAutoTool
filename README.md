# GemiAutoTool

GemiAutoTool 是一个基于 Python 的桌面自动化工具（PySide6 GUI），用于批量任务执行、运行监控、输入数据配置、结果查看与链接导出。

项目当前同时支持：
- GUI 模式（推荐）：可视化配置与运行
- CLI 模式：用于快速启动或脚本化调用

## 免责声明

本项目仅适用于合法、合规且已获授权的自动化测试与流程处理场景。

请勿将本项目用于任何违反目标平台服务条款、法律法规或未经授权的操作。使用者需自行承担使用风险与责任。

## 功能特性

### 核心能力

- 多线程任务执行（可配置并发数）
- 任务监控面板（线程状态、业务阶段、最终结果、详情）
- 结构化日志（控制台 + 文件轮转日志）
- 全局异常体系（业务异常与未知异常分层处理）
- 输入数据管理（账号 / 银行卡 / 姓名 / 邮编）
- 输出结果保存（按运行生成结果文件）

### GUI 能力（PySide6）

- `任务监控` 页面
  - 开始 / 停止
  - 重试失败任务（仅业务失败，排除“需验证”）
  - 实时日志查看
  - 任务状态表与进度统计
  - SheerID 链接导出（手动选择 / 一键导出最近结果）

- `数据配置` 页面
  - 图形化维护 `account.txt / card.txt / name.txt / zip_code.txt`
  - 银行卡结构化录入（表格填写 PAN / CVV / 月份 / 年份）
  - 格式校验并保存
  - 导入账号文件（覆盖 / 追加）

- `结果查看` 页面
  - 加载最近结果文件 / 手动选择结果文件
  - 表格查看每个账号结果（账号、状态、认证链接、原始记录）
  - 搜索筛选
  - 仅显示有认证链接的记录
  - 一键复制 / 打开认证链接

- `全局配置` 页面
  - 默认并发数
  - 主题模式（自动 / 亮色 / 暗色）
  - 日志自动滚动
  - 启动前自动清空任务表
  - 输入目录 / 输出目录（可编辑、可选择、可本地持久化）

### 日志与可观测性

- 使用 `logging` 替代 `print`
- 控制台彩色日志（按级别着色）
- 文件轮转日志（`logs/runtime.log`）
- 多线程 `task_name` 上下文日志

## 项目结构

```text
GemiAutoTool/
├─ input/                         # 输入数据目录（可在 UI 中改为其他目录）
├─ output/                        # 输出结果目录（可在 UI 中改为其他目录）
├─ logs/                          # 运行日志目录
├─ src/GemiAutoTool/
│  ├─ actions/                    # 自动化动作（登录、订阅检测、支付）
│  ├─ config/                     # 默认配置与路径定义
│  ├─ domain/                     # 数据模型（账号、支付信息、结果）
│  ├─ services/                   # 输入/输出/浏览器/支付数据等服务
│  ├─ tasks/                      # 线程任务逻辑
│  ├─ ui/                         # PySide6 UI（已拆分模块）
│  ├─ app_controller.py           # CLI / GUI 共用流程编排层
│  ├─ logging_config.py           # 日志配置
│  ├─ exceptions.py               # 全局异常定义
│  ├─ main.py                     # CLI 入口
│  └─ run_gui.py                  # GUI 入口
└─ tools/
   ├─ build_exe.ps1               # Windows EXE 打包脚本（PyInstaller）
   ├─ build_installer.ps1         # Windows 安装包打包脚本（Inno Setup）
   └─ generate_app_icon_ico.py    # SVG -> ICO 图标生成脚本
```

## 环境要求

- 操作系统：Windows（推荐，项目当前主要在 Windows 环境使用）
- Python：`3.10+`（建议 `3.11 ~ 3.13`）
- Chrome 浏览器（与 `undetected-chromedriver` 配合）

## 安装

### 1. 克隆仓库

```powershell
git clone https://github.com/mibgb65-cloud/GemiAutoTool.git
cd GemiAutoTool
```

### 2. 创建虚拟环境并安装依赖

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

如果 GUI 启动报错提示缺少 `PySide6`，可单独安装：

```powershell
pip install PySide6
```

## 启动方式

### GUI 模式（推荐）

PowerShell：

```powershell
$env:PYTHONPATH = "src"
python -m GemiAutoTool.run_gui
```

或直接运行：

```powershell
python src\GemiAutoTool\run_gui.py
```

### CLI 模式

```powershell
$env:PYTHONPATH = "src"
python -m GemiAutoTool.main
```

## 打包为 Windows EXE（PyInstaller）

项目已内置 `PyInstaller` 打包配置，支持生成可发布的 Windows GUI 可执行文件。

构建脚本特性（`tools/build_exe.ps1`）：
- 自动安装 `requirements.txt` 中依赖
- 自动安装/检查 `pyinstaller`
- 自动检查关键依赖（如 `PySide6`、`selenium`、`undetected-chromedriver`）
- `-Clean` 时清理 `build/` 与 `dist/`（含重试删除逻辑）

### 方式 1（推荐）：使用仓库内置脚本（OneDir）

```powershell
.venv\Scripts\activate
powershell -ExecutionPolicy Bypass -File .\tools\build_exe.ps1
```

输出目录（推荐发布目录）：

```text
dist\GemiAutoTool\
```

该目录内会包含：
- `GemiAutoTool.exe`
- PyInstaller 运行时依赖文件
- 自动创建的 `input/`, `output/`, `logs/` 目录（构建脚本会预创建）

### 清理旧构建后重新打包

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\build_exe.ps1 -Clean
```

### 方式 2：打包为单文件 EXE（实验性）

> 浏览器自动化（Selenium / undetected-chromedriver）在 `onefile` 模式下更容易遇到杀软误报、临时目录权限或驱动运行问题，建议优先使用 `onedir`。

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\build_exe.ps1 -OneFile
```

输出目录：

```text
dist\
```

### 方式 3：直接使用 Spec 文件构建（高级用法）

```powershell
.venv\Scripts\activate
pip install pyinstaller
pyinstaller --noconfirm --clean .\GemiAutoTool.spec
```

### 打包配置文件

- `GemiAutoTool.spec`
  - 包含 GUI 入口
  - 包含图标资源 `app_icon.ico`
  - 收集 `GemiAutoTool/ui/assets`
  - 显式收集 `PySide6 / shiboken6` 运行时资源
  - 显式收集 `selenium / undetected_chromedriver / selenium_stealth` 模块与动态导入

### 打包后的路径行为（已兼容）

打包后程序会自动以 **exe 所在目录** 作为运行根目录，用于：
- `input/`
- `output/`
- `logs/`
- `ui_settings.json`

这样不会把配置和结果写到 PyInstaller 的临时解压目录。

### 发布建议（给用户分发）

推荐优先使用 `OneDir` 构建产物发布：

- 直接将整个目录 `dist\GemiAutoTool\` 压缩为 ZIP 发布
- 不要只发布 `GemiAutoTool.exe`（`onedir` 依赖旁边的运行时文件）

推荐命名示例：

```text
GemiAutoTool-win-x64-v1.0.0.zip
```

后续如需安装包，可再使用 `Inno Setup` / `NSIS` 基于 `dist\GemiAutoTool\` 制作安装程序。

## 打包为 Windows 安装程序（Inno Setup）

项目已提供 Inno Setup 安装包脚本，可将 `PyInstaller onedir` 产物封装为安装向导式 `.exe`。

### 前置条件

1. 已成功生成 `PyInstaller` onedir 产物（`dist\GemiAutoTool\`）
2. 已安装 `Inno Setup 6`（包含 `ISCC.exe`）

### 安装 Inno Setup

官网：<https://jrsoftware.org/isinfo.php>

默认安装后 `ISCC.exe` 常见路径：

```text
C:\Program Files (x86)\Inno Setup 6\ISCC.exe
```

### 使用仓库脚本构建安装包（推荐）

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\build_installer.ps1
```

脚本行为：
- 自动检查 `dist\GemiAutoTool\GemiAutoTool.exe` 是否存在
- 自动查找 `ISCC.exe`（常见安装路径或系统 PATH）
- 使用 `packaging\GemiAutoTool.iss` 构建安装程序

输出目录：

```text
dist_installer\
```

### 指定版本号（推荐用于发布）

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\build_installer.ps1 -Version 1.0.0
```

生成示例：

```text
dist_installer\GemiAutoTool-Setup-1.0.0.exe
```

### 清理旧安装包后构建

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\build_installer.ps1 -Clean -Version 1.0.0
```

### 手动使用 Inno Setup 编译（高级用法）

```powershell
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" /Qp /DAppVersion=1.0.0 .\packaging\GemiAutoTool.iss
```

### 安装包方案说明（当前配置）

- 安装目录默认使用当前用户可写路径（避免 `Program Files` 写入权限问题）：
  - `{localappdata}\Programs\GemiAutoTool`
- 安装后可选创建桌面快捷方式
- 安装完成后可直接启动程序
- 卸载器自动注册
- 默认英文安装界面（如本机 Inno Setup 安装了中文语言包，可自行在 `.iss` 中启用）

> 之所以默认安装到用户目录，而不是 `Program Files`，是因为程序运行时会在安装目录下写入 `input/output/logs/ui_settings.json`。

## 快速开始（推荐流程）

1. 启动 GUI
2. 打开 `全局配置` 页面
3. 设置并保存：
   - 输入目录
   - 输出目录
   - 默认并发数
   - 主题模式（自动 / 亮色 / 暗色）
4. 打开 `数据配置` 页面，录入或导入数据
5. 点击 `校验并保存`
6. 返回 `任务监控` 页面，点击 `开始`
7. 完成后到 `结果查看` 页面查看每个账号的结果与认证链接

## 输入文件格式（重要）

输入目录下需要以下文件（默认在项目根目录 `input/`，也可以在 UI 全局配置中改路径）：

- `account.txt`
- `card.txt`
- `name.txt`
- `zip_code.txt`

### `account.txt`

每行一个账号，格式：

```text
email----password----recovery_email----2fa_secret
```

示例：

```text
user1@example.com----password123----recovery1@example.com----JBSWY3DPEHPK3PXP
user2@example.com----password456----recovery2@example.com----KRSXG5DSNFXGOIDB
```

说明：
- `2fa_secret` 为 TOTP 密钥（如有）
- 格式错误的行在解析时会被忽略，并记录日志告警

### `card.txt`

项目内部使用固定格式，但 GUI 已提供结构化表格录入，无需手写。

文件格式（每行一张卡）：

```text
[pan:4111111111111111, cvv:123, exp_month:10/30]
```

字段说明：
- `pan`: 卡号（12-19 位数字）
- `cvv`: 3 或 4 位数字
- `exp_month`: `MM/YY` 或 `MM/YYYY`

### `name.txt`

每行一个姓名：

```text
Alice Test
Bob Smith
```

### `zip_code.txt`

每行一个邮编：

```text
10001
94105
```

## 输出文件格式

输出目录下会生成运行结果文件，例如：

```text
subscription_results_20260224_003213.txt
```

常见记录格式：

- 已订阅：
```text
user@example.com----已订阅
```

- 含认证链接（待进一步认证）：
```text
user@example.com__https://services.sheerid.com/verify/xxxx/?verificationId=yyyy
```

- 业务失败：
```text
user@example.com----登录失败
user@example.com----支付失败(...)
```

## 结果查看页面（新增）

`结果查看` 页签可以直接解析结果文件并按账号展示：

- 账号
- 状态
- 认证链接
- 来源（文件名:行号）
- 原始记录

支持操作：
- `加载最近结果`
- `选择结果文件`
- `刷新当前文件`
- `搜索账号/状态/链接`
- `仅看有认证链接`
- `复制认证链接`
- `打开认证链接`

## 失败任务重试（排除需验证）

`任务监控` 页面提供 `重试失败任务` 按钮。

重试规则：
- 会重试：业务失败（例如登录失败、支付失败）
- 不会重试：`需验证`
- 不会重试：线程崩溃（`崩溃`）

说明：
- 重试是基于当前任务表中的“最后一次结果状态”进行筛选
- 若清空任务表后再点重试，将没有可重试项

## SheerID 链接导出

项目支持从结果文件中提取 `https://services.sheerid.com/verify/...` 链接并导出为新 TXT（每行一个链接）：

- `导出 SheerID 链接`（手动选择结果文件）
- `一键导出最近结果链接`

也可通过服务层调用：

```python
from GemiAutoTool.services import SubscriptionOutputService

svc = SubscriptionOutputService(output_dir="output")
path, count = svc.export_sheerid_verify_links(
    source_file_path="output/subscription_results_xxx.txt"
)
```

## 全局配置与本地持久化

GUI 全局配置会保存到项目根目录：

- `ui_settings.json`

当前持久化项：
- `max_concurrent`
- `auto_scroll_log`
- `clear_task_table_on_start`
- `theme_mode`（`auto/light/dark`）
- `input_dir`
- `output_dir`

兼容性：
- 旧版本 `dark_mode: true/false` 会自动迁移为 `theme_mode`

## 日志说明

### 日志输出

- 控制台日志：彩色输出（按级别）
- 文件日志：默认 `logs/runtime.log`（轮转）

### 常用环境变量

PowerShell 示例：

```powershell
$env:GEMI_LOG_LEVEL = "DEBUG"
$env:GEMI_LOG_COLOR = "1"
$env:GEMI_LOG_DIR = "logs"
```

常见变量：
- `GEMI_LOG_LEVEL`
- `GEMI_LOG_FILE_LEVEL`
- `GEMI_LOG_COLOR`
- `GEMI_LOG_DIR`
- `GEMI_LOG_FILE`
- `GEMI_LOG_MAX_BYTES`
- `GEMI_LOG_BACKUP_COUNT`

## 常见问题（FAQ）

### 1. `ModuleNotFoundError: No module named 'PySide6'`

安装 GUI 依赖：

```powershell
pip install PySide6
```

### 2. `ModuleNotFoundError: No module named 'undetected_chromedriver'`

安装自动化依赖：

```powershell
pip install undetected-chromedriver
```

或直接重新安装全部依赖：

```powershell
pip install -r requirements.txt
```

### 3. `ModuleNotFoundError: No module named 'pyotp'`（打包后运行时）

这通常表示**打包时使用的虚拟环境缺少运行依赖**。

请先在打包环境中安装完整依赖后重新打包：

```powershell
pip install -r requirements.txt
powershell -ExecutionPolicy Bypass -File .\tools\build_exe.ps1 -Clean
```

> 现在 `tools/build_exe.ps1` 已会自动执行 `pip install -r requirements.txt`，建议统一用该脚本打包。

### 4. `AttributeError: 'NoneType' object has no attribute 'isatty'`（打包后 GUI 启动）

这是 `windowed` 模式下控制台流对象为空导致的历史问题。

项目已在日志模块中处理该兼容逻辑。如果仍遇到该报错，请确认你运行的是**重新打包后的最新 exe**。

### 5. `-Clean` 时删除 `dist` 失败（DLL 被占用 / Access denied）

常见原因：
- 打包产物 `GemiAutoTool.exe` 仍在运行
- 资源管理器打开了 `dist\GemiAutoTool\_internal\...` 并占用 DLL
- 杀毒软件临时占用 DLL

处理方式：

```powershell
taskkill /IM GemiAutoTool.exe /F
powershell -ExecutionPolicy Bypass -File .\tools\build_exe.ps1 -Clean
```

### 6. 结果查看页没有内容

请检查：
- 输出目录配置是否正确（`全局配置` 页面）
- 是否已生成 `subscription_results_*.txt`
- 结果文件是否为空

### 7. 标题文字显示被挡住 / UI 样式异常

已针对 `QGroupBox` 标题裁切问题做过样式修复。如果仍有问题，请反馈：
- 系统缩放比例（100% / 125% / 150%）
- 操作系统版本
- PySide6 版本

## 开发与维护建议

### 代码组织（当前）

`ui/main_window.py` 已拆分为多个 mixin 模块，便于维护：
- `_main_window_monitor.py`
- `_main_window_data.py`
- `_main_window_results.py`
- `_main_window_export.py`
- `_main_window_config.py`
- `_main_window_theme.py`

### 本地检查

```powershell
python -m compileall src\GemiAutoTool
```

## 许可证

本项目使用 `MIT License`，详见 `LICENSE`。
