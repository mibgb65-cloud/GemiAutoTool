param(
    [switch]$Clean,
    [string]$Version = "1.0.0",
    [string]$IsccPath
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
            Get-ChildItem -Path $PathToRemove -Recurse -Force -ErrorAction SilentlyContinue | ForEach-Object {
                try { $_.Attributes = "Normal" } catch {}
            }
            Remove-Item -Recurse -Force $PathToRemove -ErrorAction Stop
            return
        } catch {
            if ($attempt -lt $MaxAttempts) {
                Write-Host "==> Remove failed (attempt $attempt/$MaxAttempts), retrying in ${DelaySeconds}s: $PathToRemove"
                Start-Sleep -Seconds $DelaySeconds
                continue
            }
            throw "Failed to remove '$PathToRemove'. Close Explorer windows or installer EXE that may be locking files and try again."
        }
    }
}

function Resolve-IsccExecutable {
    param(
        [string]$CandidatePath
    )

    if ($CandidatePath) {
        $resolved = (Resolve-Path $CandidatePath -ErrorAction Stop).Path
        if (-not (Test-Path $resolved)) {
            throw "ISCC.exe not found: $CandidatePath"
        }
        return $resolved
    }

    $commonCandidates = @(
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe"
    )

    foreach ($path in $commonCandidates) {
        if (Test-Path $path) {
            return $path
        }
    }

    $cmd = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }

    throw "ISCC.exe not found. Install Inno Setup 6 or pass -IsccPath 'C:\Path\To\ISCC.exe'."
}

Write-Host "==> Project root: $ProjectRoot"

$issFile = Join-Path $ProjectRoot "packaging\GemiAutoTool.iss"
if (-not (Test-Path $issFile)) {
    throw "Inno Setup script not found: $issFile"
}

$distAppDir = Join-Path $ProjectRoot "dist\GemiAutoTool"
$distExe = Join-Path $distAppDir "GemiAutoTool.exe"
if (-not (Test-Path $distExe)) {
    throw "PyInstaller output not found: $distExe`nPlease run .\tools\build_exe.ps1 first."
}

$installerOutputDir = Join-Path $ProjectRoot "dist_installer"

if ($Clean -and (Test-Path $installerOutputDir)) {
    Write-Host "==> Removing $installerOutputDir"
    Remove-PathWithRetry -PathToRemove $installerOutputDir
}

$isccExe = Resolve-IsccExecutable -CandidatePath $IsccPath
Write-Host "==> ISCC: $isccExe"
Write-Host "==> Version: $Version"
Write-Host "==> Source: $distAppDir"

$isccArgs = @(
    "/Qp",
    "/DAppVersion=$Version",
    $issFile
)

& $isccExe @isccArgs
Assert-LastExitCode "Inno Setup build"

if (Test-Path $installerOutputDir) {
    Write-Host "==> Installer output: $installerOutputDir"
    Get-ChildItem -File $installerOutputDir | ForEach-Object {
        Write-Host ("    - " + $_.Name)
    }
}

Write-Host "==> Done"
