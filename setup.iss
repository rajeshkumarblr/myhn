; Script generated for HN App
#define MyAppName "Hacker Station"
#define MyAppVersion "1.0"
#define MyAppPublisher "Rajesh Kumar"
#define MyAppURL "https://github.com/rajeshkumarblr/myhn"
#define MyAppExeName "HackerStation.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the Inno Setup Compiler)
AppId={{A1B2C3D4-E5F6-7890-1234-56789ABCDEF0}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
; This makes the installer look modern
WizardStyle=modern
; Where to output the final setup.exe
OutputDir=dist
OutputBaseFilename=HackerStation-Setup
; Icon for the installer itself
SetupIconFile=assets\hn.ico
Compression=lzma
SolidCompression=yes
CpuAccess=64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; IMPORTANT: This assumes your build.ps1 creates a FOLDER in dist/windows/
; If you built a single file, change this to point to that file.
Source: "dist\windows\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\windows\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent