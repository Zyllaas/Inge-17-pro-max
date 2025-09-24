[Setup]
AppName=Clipboard-AI
AppVersion=1.0.0
AppPublisher=ClipboardAI Team
AppPublisherURL=https://github.com/yourusername/clipboard-ai
AppSupportURL=https://github.com/yourusername/clipboard-ai/issues
AppUpdatesURL=https://github.com/yourusername/clipboard-ai/releases
DefaultDirName={autopf}\ClipboardAI
DefaultGroupName=ClipboardAI
AllowNoIcons=yes
LicenseFile=LICENSE.txt
OutputDir=out
OutputBaseFilename=ClipboardAI-Setup
SetupIconFile=icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1

[Files]
Source: "dist\ClipboardAI.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "config.toml"; DestDir: "{userappdata}\ClipboardAI"; Flags: onlyifdoesntexist uninsneveruninstall
Source: ".env.example"; DestDir: "{userappdata}\ClipboardAI"; DestName: ".env"; Flags: onlyifdoesntexist uninsneveruninstall
Source: "templates\*"; DestDir: "{userappdata}\ClipboardAI\templates"; Flags: onlyifdoesntexist uninsneveruninstall recursesubdirs createallsubdirs
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\Clipboard-AI"; Filename: "{app}\ClipboardAI.exe"
Name: "{group}\{cm:UninstallProgram,Clipboard-AI}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Clipboard-AI"; Filename: "{app}\ClipboardAI.exe"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\Clipboard-AI"; Filename: "{app}\ClipboardAI.exe"; Tasks: quicklaunchicon

[Registry]
Root: HKCU; Subkey: "Software\ClipboardAI"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey

[Run]
Filename: "{app}\ClipboardAI.exe"; Description: "{cm:LaunchProgram,Clipboard-AI}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\ClipboardAI\logs"

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  AppDataDir: String;
begin
  if CurStep = ssPostInstall then
  begin
    AppDataDir := ExpandConstant('{userappdata}\ClipboardAI');
    if not DirExists(AppDataDir) then
    begin
      CreateDir(AppDataDir);
    end;
  end;
end;