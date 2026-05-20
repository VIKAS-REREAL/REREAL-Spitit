# Installs REREAL Spitit to Program Files with Start Menu shortcut and Add/Remove Programs entry.
# Right-click → Run with PowerShell as Administrator, or from elevated PowerShell:
#   Set-ExecutionPolicy -Scope Process Bypass -Force; .\Install-REREAL-Spitit.ps1

#Requires -RunAsAdministrator

$ErrorActionPreference = "Stop"

$AppName = "REREAL Spitit"
$ExeName = "REREAL-Spitit.exe"
$Version = "1.0.0"
$Publisher = "REREAL"
$InstallDir = Join-Path $env:ProgramFiles $AppName
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$SourceExe = Join-Path $RepoRoot "dist\$ExeName"
$UninstallScriptName = "uninstall-REREAL-Spitit.ps1"
$SourceUninstall = Join-Path $ScriptDir $UninstallScriptName

if (-not (Test-Path $SourceExe)) {
    throw "Missing built executable. Run from repo root first: .\build-release.ps1`nExpected: $SourceExe"
}
if (-not (Test-Path $SourceUninstall)) {
    throw "Missing uninstall script: $SourceUninstall"
}

Write-Host "Installing $AppName to $InstallDir ..."

New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
Copy-Item -Path $SourceExe -Destination (Join-Path $InstallDir $ExeName) -Force
Copy-Item -Path $SourceUninstall -Destination (Join-Path $InstallDir $UninstallScriptName) -Force

$programs = [Environment]::GetFolderPath("CommonPrograms")
$startMenuFolder = Join-Path $programs $AppName
New-Item -ItemType Directory -Force -Path $startMenuFolder | Out-Null

$wsh = New-Object -ComObject WScript.Shell
$mainSc = $wsh.CreateShortcut((Join-Path $startMenuFolder "$AppName.lnk"))
$mainSc.TargetPath = Join-Path $InstallDir $ExeName
$mainSc.WorkingDirectory = $InstallDir
$mainSc.Description = $AppName
$mainSc.Save()

$uninstallSc = $wsh.CreateShortcut((Join-Path $startMenuFolder "Uninstall $AppName.lnk"))
$uninstallSc.TargetPath = "powershell.exe"
$uninstallSc.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$(Join-Path $InstallDir $UninstallScriptName)`""
$uninstallSc.Save()

$regPath = "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\REREAL-Spitit"
if (-not (Test-Path $regPath)) {
    New-Item -Path $regPath -Force | Out-Null
}

$uninstallCmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$(Join-Path $InstallDir $UninstallScriptName)`""
$exePath = Join-Path $InstallDir $ExeName

Set-ItemProperty -Path $regPath -Name "DisplayName" -Value $AppName -Type String
Set-ItemProperty -Path $regPath -Name "DisplayVersion" -Value $Version -Type String
Set-ItemProperty -Path $regPath -Name "Publisher" -Value $Publisher -Type String
Set-ItemProperty -Path $regPath -Name "InstallLocation" -Value $InstallDir -Type String
Set-ItemProperty -Path $regPath -Name "DisplayIcon" -Value "$exePath,0" -Type String
Set-ItemProperty -Path $regPath -Name "UninstallString" -Value $uninstallCmd -Type String
Set-ItemProperty -Path $regPath -Name "QuietUninstallString" -Value $uninstallCmd -Type String
Set-ItemProperty -Path $regPath -Name "NoModify" -Value 1 -Type DWord
Set-ItemProperty -Path $regPath -Name "NoRepair" -Value 1 -Type DWord

Write-Host "Done. Launch from Start Menu or: $exePath"
Write-Host "Settings file (after first run): $env:LOCALAPPDATA\REREAL_Spitit\config.json"
