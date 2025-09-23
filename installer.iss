[Setup]
AppName=ClipboardAI
AppVersion=1.0
DefaultDirName={pf}\ClipboardAI
DefaultGroupName=ClipboardAI
OutputDir=out
OutputBaseFilename=ClipboardAI-Setup
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\ClipboardAI.exe"; DestDir: "{app}"
Source: "config.toml"; DestDir: "{userappdata}\ClipboardAI"; Flags: onlyifdoesntexist
Source: ".env.example"; DestDir: "{userappdata}\ClipboardAI"; Flags: onlyifdoesntexist

[Icons]
Name: "{group}\ClipboardAI"; Filename: "{app}\ClipboardAI.exe"
Name: "{commondesktop}\ClipboardAI"; Filename: "{app}\ClipboardAI.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop icon"; GroupDescription: "Additional icons:"