; ArkPlots Windows installer (Inno Setup 6).
; Arknights-inspired industrial dark theme: charcoal panels, amber hazard accents,
; high-contrast light text (avoid medium-gray "slate" styles that wash out labels).

#ifndef MyAppVersion
  #error MyAppVersion must be passed as /DMyAppVersion=...
#endif

#ifndef MyAppId
  #define MyAppId "{E8B3C4A1-7D2F-4E9B-A6C1-1F2E3D4C5B6A}"
#endif

#define MyAppName "ArkPlots"
#define MyAppExeName "ArkPlots.exe"
#define MyAppPublisher "ApodidaeDeSwift"
#define MyAppURL "https://github.com/ApodidaeDeSwift/ArkPlots"
#define MyAppCopyright "Copyright (C) 2024-2026 ApodidaeDeSwift"

[Setup]
AppId={{E8B3C4A1-7D2F-4E9B-A6C1-1F2E3D4C5B6A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}/releases
AppCopyright={#MyAppCopyright}
DefaultDirName={localappdata}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
DisableDirPage=auto
UsePreviousAppDir=yes
UsePreviousTasks=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
AllowNoIcons=yes
Compression=lzma2/fast
SolidCompression=no
; Built-in dark (not slate): slate mid-grays make labels hard to read.
WizardStyle=modern dark
WizardImageFile=wizard_side.png
WizardSmallImageFile=wizard_top.png
WizardBackImageFile=wizard_back.png
WizardImageBackColor=#0a0c10
WizardSmallImageBackColor=#0a0c10
WizardBackColor=#0a0c10
WizardBackImageOpacity=40
SetupIconFile=..\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
OutputDir=..
OutputBaseFilename=Arkplot_setup_ver{#MyAppVersion}
ArchitecturesInstallIn64BitMode=x64
CloseApplications=yes
CloseApplicationsFilter={#MyAppExeName}
RestartApplications=no
MinVersion=10.0
ShowLanguageDialog=no
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoCopyright={#MyAppCopyright}
VersionInfoDescription={#MyAppName} installer
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}
VersionInfoTextVersion={#MyAppVersion}

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Default.isl"

[Messages]
SetupAppTitle=ArkPlots
SetupWindowTitle=ArkPlots  //  INSTALL  {#MyAppVersion}
ButtonBack=< 返回(&B)
ButtonNext=继续(&N) >
ButtonInstall=执行安装(&I)
ButtonFinish=完成(&F)
BeveledLabel=RHODES  ·  PLOTLINE  ·  ARKPLOTS
SelectDirLabel3=指定安装目录。阅读进度将保存在该路径下。
SelectDirBrowseLabel=可使用默认路径，或单击「浏览」选择其他位置。
DiskSpaceMBLabel=预计占用 [mb] MB。
SelectTasksLabel2=附加任务：
ReadyLabel1=系统检查完毕。单击「执行安装」开始部署。
ReadyLabel2a=将执行：
InstallingLabel=正在部署 ArkPlots…
FinishedHeadingLabel=部署完成
FinishedLabelNoIcons=ArkPlots 已就绪。祝检索愉快。
FinishedLabel=ArkPlots 已就绪。可通过开始菜单或桌面快捷方式启动。
ClickFinish=单击「完成」关闭安装程序。
ConfirmUninstall=确定卸载 %1？%n阅读进度文件不会被自动删除。
StatusExtractFiles=解包组件…
StatusCreateIcons=写入快捷方式…
StatusCreateDirs=创建目录…
StatusSavingUninstall=写入卸载信息…

[CustomMessages]
CreateDesktopIcon=在桌面创建快捷方式
LaunchAfterInstall=部署完成后启动 ArkPlots
UpgradeConfirm=检测到本机已部署 ArkPlots。%n%n「是」= 更新至 {#MyAppVersion}（保留阅读进度）%n「否」= 取消
NameAndVersion=%1  %2

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "附加任务:"; Flags: unchecked

[Files]
Source: "..\dist\ArkPlots\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\Plotline.json"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchAfterInstall}"; Flags: nowait postinstall skipifsilent

[Code]
function UninstallRegKey: String;
begin
  Result := 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppId}_is1';
end;

function IsUpgrade: Boolean;
begin
  Result :=
    RegKeyExists(HKCU, UninstallRegKey) or
    RegKeyExists(HKLM, UninstallRegKey);
end;

function InitializeSetup(): Boolean;
begin
  if WizardSilent then
    Result := True
  else if IsUpgrade then
    Result := MsgBox(ExpandConstant('{cm:UpgradeConfirm}'), mbConfirmation, MB_YESNO) = IDYES
  else
    Result := True;
end;
