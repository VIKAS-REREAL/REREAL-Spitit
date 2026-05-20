; Inno Setup 6 — builds a full Windows installer (Program Files, Start Menu, Uninstaller).
; Prerequisite: Inno Setup installed (https://jrsoftware.org/isdl.php)
; From repo root: iscc.exe installer\REREAL-Spitit.iss

#define MyAppName "REREAL-Spitit"
#define MyAppVersion "1.1.0"
#define MyAppPublisher "REREAL"
#define MyAppExeName "REREAL-Spitit.exe"

[Setup]
AppId={{7F3E2B1A-9C8D-4E5F-B0A1-23456789CDEF}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL=https://github.com/
DefaultDirName={autopf}\REREAL Spitit
DefaultGroupName=Spitit
AllowNoIcons=yes
OutputDir=..\dist_installer
OutputBaseFilename=REREAL-Spitit-Setup-{#MyAppVersion}
SetupIconFile=..\assets\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
InfoBeforeFile=
SetupLogging=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Remove per-user settings and cached tray icon (full uninstall)
Type: filesandordirs; Name: "{localappdata}\REREAL_Spitit"
