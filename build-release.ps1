param([switch]$Installer)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "========================================" -ForegroundColor Yellow
Write-Host "  REREAL - Spitit Build Script" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""

Write-Host "[1/5] Installing dependencies..." -ForegroundColor Cyan
python -m pip install --upgrade pip -q
python -m pip install -r requirements.txt -q
python -m pip install "pyinstaller>=6.0" -q

Write-Host "[2/5] Generating icon..." -ForegroundColor Cyan
python scripts/build_icon.py

Write-Host "[3/5] Generating done sound..." -ForegroundColor Cyan
python scripts/generate_sound.py

Write-Host "[4/5] Running PyInstaller..." -ForegroundColor Cyan
python -m PyInstaller --noconfirm REREAL-Spitit.spec

$exe = "dist\REREAL-Spitit.exe"
if (-not (Test-Path $exe)) {
    throw "Portable build failed: missing $exe"
}
Write-Host "  Portable: $exe" -ForegroundColor Green

if ($Installer) {
    Write-Host "[5/5] Building installer..." -ForegroundColor Cyan

    $iscc = $null
    foreach ($c in @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles}\Inno Setup 6\ISCC.exe",
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "${env:LOCALAPPDATA}\Programs\Inno Setup 6\ISCC.exe"
    )) {
        if (Test-Path $c) { $iscc = $c; break }
    }

    if (-not $iscc) {
        throw "Inno Setup 6 not found. Install from jrsoftware.org"
    }

    & $iscc "installer\REREAL-Spitit.iss"

    $setup = Get-ChildItem "dist_installer" -Filter "REREAL-Spitit-Setup-*.exe" | Select-Object -First 1
    if ($setup) {
        Write-Host "  Installer: $($setup.FullName)" -ForegroundColor Green
    }
} else {
    Write-Host "[5/5] Skipping installer (use -Installer flag to build)" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Build complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
