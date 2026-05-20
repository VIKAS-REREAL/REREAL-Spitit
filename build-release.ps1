# Build REREAL-Spitit.exe (PyInstaller) and optionally the Inno Setup installer.
# Run from repo root in PowerShell:  .\build-release.ps1
# For installer: install Inno Setup 6, then re-run with -Installer

param(
    [switch] $Installer
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "Installing build dependencies..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install "pyinstaller>=6.0"

Write-Host "Running PyInstaller..."
python -m PyInstaller --noconfirm REREAL-Spitit.spec

$exe = Join-Path $PSScriptRoot "dist\REREAL-Spitit.exe"
if (-not (Test-Path $exe)) {
    throw "Build failed: missing $exe"
}
Write-Host "OK: $exe"

if ($Installer) {
    $iscc = $null
    foreach ($c in @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles}\Inno Setup 6\ISCC.exe",
        "${env:LOCALAPPDATA}\Programs\Inno Setup 6\ISCC.exe"
    )) {
        if (Test-Path $c) { $iscc = $c; break }
    }
    if (-not $iscc) {
        throw "Inno Setup 6 not found. Install from https://jrsoftware.org/isdl.php then run: .\build-release.ps1 -Installer"
    }
    & $iscc (Join-Path $PSScriptRoot "installer\REREAL-Spitit.iss")
    $setup = Get-ChildItem -Path (Join-Path $PSScriptRoot "dist_installer") -Filter "REREAL-Spitit-Setup-*.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($setup) {
        Write-Host "OK: $($setup.FullName)"
    }
}

Write-Host ""
Write-Host "Portable exe:  $(Join-Path $PSScriptRoot 'dist\REREAL-Spitit.exe')"
Write-Host "Full install:  Right-click installer\Install-REREAL-Spitit.ps1 -> Run with PowerShell as Administrator"
Write-Host "               (copies exe to Program Files, Start Menu, Add/Remove Programs)"
