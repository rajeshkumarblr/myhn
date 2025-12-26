; Script generated for HN App
#define MyAppName "Hacker Station"
#define MyAppVersion "1.0"
#define MyAppPublisher "Rajesh Kumar"
#define MyAppURL "https://github.com/rajeshkumarblr/myhn"
#define MyAppExeName "HackerStation.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-1234-56789ABCDEF0}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
WizardStyle=modern
OutputDir=dist
OutputBaseFilename=HackerStation-Setup
SetupIconFile=assets\hn.ico
Compression=lzma
SolidCompression=yes

; 64-Bit Install Settings
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; FIX: Added 'HackerStation\' to path
Source: "dist\windows\HackerStation\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; FIX: Added 'Excludes' to prevent bundling your personal session data
Source: "dist\windows\HackerStation\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "session.json,cookies.json,*.log"

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent