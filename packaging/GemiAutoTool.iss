#ifndef AppName
  #define AppName "GemiAutoTool"
#endif
#ifndef AppPublisher
  #define AppPublisher "mibgb65-cloud"
#endif
#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif
#ifndef AppExeName
  #define AppExeName "GemiAutoTool.exe"
#endif
#ifndef DistDir
  #define DistDir "..\dist\GemiAutoTool"
#endif
#ifndef OutputDir
  #define OutputDir "..\dist_installer"
#endif
#ifndef AppIconFile
  #define AppIconFile "..\src\GemiAutoTool\ui\assets\app_icon.ico"
#endif
#ifndef ChineseMessagesFile
  #define ChineseMessagesFile AddBackslash(SourcePath) + "languages\ChineseSimplified.isl"
#endif

[Setup]
AppId={{6F8E9A44-5A74-4A4D-9D60-73D7B311B0D7}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir={#OutputDir}
OutputBaseFilename={#AppName}-Setup-{#AppVersion}
SetupIconFile={#AppIconFile}
UninstallDisplayIcon={app}\{#AppExeName}

[Languages]
Name: "chinesesimp"; MessagesFile: "{#ChineseMessagesFile}"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加任务:"; Flags: unchecked

[Files]
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
Name: "{app}\input"
Name: "{app}\output"
Name: "{app}\logs"

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "启动 {#AppName}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
var
  ExePath: string;
begin
  ExePath := ExpandConstant('{#DistDir}\{#AppExeName}');
  if not FileExists(ExePath) then
  begin
    MsgBox(
      '未找到打包产物：' + #13#10 + ExePath + #13#10#13#10 +
      '请先执行 PyInstaller 构建（生成 dist\GemiAutoTool）后再编译安装包。',
      mbError, MB_OK);
    Result := False;
    exit;
  end;
  Result := True;
end;
