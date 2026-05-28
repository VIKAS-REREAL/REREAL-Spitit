; REREAL - Spitit Inno Setup Script
; Builds a Windows installer with modern wizard UI.

#define MyAppName "REREAL - Spitit"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "REREAL"
#define MyAppURL "https://vikas-rereal.github.io/REREAL-Spitit/"
#define MyAppExeName "REREAL-Spitit.exe"

[Setup]
AppId={{7F3E2B1A-9C8D-4E5F-B0A1-23456789CDEF}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
WizardStyle=modern
WizardSizePercent=120
DisableWelcomePage=no
LicenseFile=license.rtf
DefaultDirName={autopf}\REREAL Spitit
DefaultGroupName=REREAL Spitit
AllowNoIcons=no
OutputDir=..\dist_installer
OutputBaseFilename=REREAL-Spitit-Setup-{#MyAppVersion}
SetupIconFile=..\assets\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#MyAppExeName}
VersionInfoVersion={#MyAppVersion}.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoProductName={#MyAppName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"
Name: "startmenu"; Description: "Pin to &Start Menu"; GroupDescription: "Additional shortcuts:"; Flags: checkedonce
Name: "startup"; Description: "Launch &automatically on Windows startup"; GroupDescription: "Startup:"

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
  ValueType: string; ValueName: "REREALSpitit"; \
  ValueData: """{app}\{#MyAppExeName}"""; \
  Flags: uninsdeletevalue; Tasks: startup

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; \
  Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{localappdata}\REREAL_Spitit"
