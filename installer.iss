; Inno Setup script - build with:  iscc installer.iss  (or run build.ps1)
#define AppName "Browser Agent"
#define AppVersion "1.0.0"

[Setup]
AppId={{6B0F5D5E-3C1A-4E0B-9C52-7A1D2F4B8E13}
AppName={#AppName}
AppVersion={#AppVersion}
DefaultDirName={autopf}\BrowserAgent
DefaultGroupName={#AppName}
PrivilegesRequired=lowest
OutputDir=installer
OutputBaseFilename=BrowserAgentSetup
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\console.exe
CloseApplications=no

[Tasks]
Name: "autostart"; Description: "Start the background agent when I sign in"; Flags: unchecked

[Files]
Source: "dist\agent.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\console.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Browser Agent Console"; Filename: "{app}\console.exe"; WorkingDir: "{app}"

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "BrowserAgent"; ValueData: """{app}\agent.exe"""; Flags: uninsdeletevalue; Tasks: autostart

[Run]
Filename: "{app}\console.exe"; Description: "Open the console now"; Flags: postinstall nowait skipifsilent

[UninstallRun]
Filename: "{app}\console.exe"; Parameters: "quit"; Flags: runhidden; RunOnceId: "StopAgent"
