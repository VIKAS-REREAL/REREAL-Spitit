# Removes REREAL Spitit from Program Files, Start Menu, and registry (per-machine).
# Run as Administrator (same as installer).

#Requires -RunAsAdministrator

$ErrorActionPreference = "Stop"

$AppName = "REREAL Spitit"
$ExeName = "REREAL-Spitit.exe"
$InstallDir = Join-Path $env:ProgramFiles $AppName
$regPath = "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\REREAL-Spitit"
$runKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
$runName = "REREALSpitit"

Write-Host "Stopping $AppName if running..."
$exePath = Join-Path $InstallDir $ExeName
Get-CimInstance Win32_Process -Filter "Name='$ExeName'" -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $exePath } |
    Stop-Process -Force -ErrorAction SilentlyContinue

if (Test-Path $InstallDir) {
    Write-Host "Removing $InstallDir ..."
    Remove-Item -LiteralPath $InstallDir -Recurse -Force
}

$programs = [Environment]::GetFolderPath("CommonPrograms")
$startMenuFolder = Join-Path $programs $AppName
if (Test-Path $startMenuFolder) {
    Remove-Item -LiteralPath $startMenuFolder -Recurse -Force
}

if (Test-Path $regPath) {
    Remove-Item -LiteralPath $regPath -Recurse -Force
}

# Best-effort: remove current user's startup entry (app uses HKCU Run when enabled)
try {
    Remove-ItemProperty -Path $runKey -Name $runName -ErrorAction SilentlyContinue
} catch {
    # ignore
}

$userData = Join-Path $env:LOCALAPPDATA "REREAL_Spitit"
if (Test-Path $userData) {
    Write-Host "Removing user data: $userData"
    Remove-Item -LiteralPath $userData -Recurse -Force
}

Write-Host "Uninstall complete."
