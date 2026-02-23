param(
    [switch]$Clean,
    [switch]$OneFile
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $ProjectRoot

function Assert-LastExitCode {
    param(
        [string]$StepName
    )
    if ($LASTEXITCODE -ne 0) {
        throw "$StepName failed with exit code $LASTEXITCODE"
    }
}

function Remove-PathWithRetry {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PathToRemove,
        [int]$MaxAttempts = 5,
        [int]$DelaySeconds = 2
    )

    if (-not (Test-Path $PathToRemove)) {
        return
    }

    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        try {
            # 清理只读属性，减少 Windows 删除失败概率
            Get-ChildItem -Path $PathToRemove -Recurse -Force -ErrorAction SilentlyContinue | ForEach-Object {
                try { $_.Attributes = 'Normal' } catch {}
            }
            Remove-Item -Recurse -Force $PathToRemove -ErrorAction Stop
            return
        } catch {
            if ($attempt -lt $MaxAttempts) {
                Write-Host "==> Remove failed (attempt $attempt/$MaxAttempts), retrying in ${DelaySeconds}s: $PathToRemove"
                Start-Sleep -Seconds $DelaySeconds
                continue
            }
            throw "Failed to remove '$PathToRemove'. The build output may still be running or locked by another process (Explorer/antivirus). Close GemiAutoTool.exe and try again."
        }
    }
}

function Ensure-PythonModule {
    param(
        [string]$ModuleName,
        [string]$InstallPackage = $ModuleName
    )

    $moduleExists = $false

    # 使用 find_spec 避免 import 失败时输出 traceback；同时兼容 PowerShell 对非 0 退出码的终止行为。
    $probeCmd = "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('$ModuleName') else 1)"
    try {
        & $pythonExe -c $probeCmd *> $null
        $moduleExists = ($LASTEXITCODE -eq 0)
    } catch {
        $moduleExists = $false
    }

    if ($moduleExists) {
        Write-Host "==> Dependency ok: $ModuleName"
        return
    }

    Write-Host "==> Installing missing dependency: $InstallPackage"
    & $pythonExe -m pip install $InstallPackage
    Assert-LastExitCode "install $InstallPackage"

    & $pythonExe -c "import $ModuleName" *> $null
    Assert-LastExitCode "verify import $ModuleName"
}

Write-Host "==> Project root: $ProjectRoot"

if ($Clean) {
    $runningExe = Get-Process -Name "GemiAutoTool" -ErrorAction SilentlyContinue
    if ($runningExe) {
        $pids = ($runningExe | Select-Object -ExpandProperty Id) -join ", "
        throw "Detected running process 'GemiAutoTool.exe' (PID: $pids). Please close it before cleaning/building."
    }

    foreach ($dir in @("build", "dist")) {
        $path = Join-Path $ProjectRoot $dir
        if (Test-Path $path) {
            Write-Host "==> Removing $path"
            Remove-PathWithRetry -PathToRemove $path
        }
    }
}

$venvPython = Join-Path $ProjectRoot ".venv\\Scripts\\python.exe"
$pythonExe = if (Test-Path $venvPython) { $venvPython } else { "python" }

Write-Host "==> Python: $pythonExe"

& $pythonExe -m pip install --upgrade pip
Assert-LastExitCode "pip upgrade"

if (Test-Path (Join-Path $ProjectRoot "requirements.txt")) {
    Write-Host "==> Installing project dependencies from requirements.txt"
    & $pythonExe -m pip install -r requirements.txt
    Assert-LastExitCode "requirements install"
}

& $pythonExe -m pip install pyinstaller
Assert-LastExitCode "pyinstaller install"

# GUI 打包的最小依赖预检（缺失时直接安装，避免打包成功但运行时报缺包）
Ensure-PythonModule -ModuleName "PySide6"
Ensure-PythonModule -ModuleName "selenium"
Ensure-PythonModule -ModuleName "undetected_chromedriver" -InstallPackage "undetected-chromedriver"
Ensure-PythonModule -ModuleName "selenium_stealth" -InstallPackage "selenium-stealth"

if ($OneFile) {
    Write-Host "==> Building one-file exe (experimental for browser automation)"
    & $pythonExe -m PyInstaller `
        --noconfirm `
        --clean `
        --windowed `
        --name GemiAutoTool `
        --icon src/GemiAutoTool/ui/assets/app_icon.ico `
        --paths src `
        --add-data "src/GemiAutoTool/ui/assets;GemiAutoTool/ui/assets" `
        src/GemiAutoTool/run_gui.py
    Assert-LastExitCode "PyInstaller one-file build"
} else {
    Write-Host "==> Building one-dir exe using GemiAutoTool.spec"
    & $pythonExe -m PyInstaller --noconfirm --clean GemiAutoTool.spec
    Assert-LastExitCode "PyInstaller one-dir build"
}

$distDir = Join-Path $ProjectRoot "dist\\GemiAutoTool"
if ($OneFile) {
    $distDir = Join-Path $ProjectRoot "dist"
}

if (Test-Path $distDir) {
    Write-Host "==> Build output: $distDir"
}

if (-not $OneFile) {
    foreach ($dir in @("input", "output", "logs")) {
        $target = Join-Path $distDir $dir
        if (-not (Test-Path $target)) {
            New-Item -ItemType Directory -Path $target | Out-Null
        }
    }
    Write-Host "==> Created runtime folders in dist\\GemiAutoTool (input/output/logs)"
}

Write-Host "==> Done"
