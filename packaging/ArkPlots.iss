; ArkPlots Windows installer (Inno Setup 6).
; Compile via: python packaging/build_release.py
;   iscc /DMyAppVersion=x.y.z.w packaging/ArkPlots.iss
;
; Visual style matches the desktop app (dark cyan / slate).

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
WizardStyle=dark
WizardStyleFile=builtin:slate
WizardImageFile=wizard_side.png
WizardSmallImageFile=wizard_top.png
WizardImageBackColor=#0b1219
WizardSmallImageBackColor=#0b1219
WizardBackColor=#0b1219
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
SetupWindowTitle=ArkPlots  ·  安装 {#MyAppVersion}
ButtonBack=< 上一步(&B)
ButtonNext=下一步(&N) >
ButtonInstall=开始安装(&I)
ButtonFinish=完成(&F)
BeveledLabel=明日方舟剧情检索 · ArkPlots
SelectDirLabel3=选择安装位置。剧情进度会保存在该文件夹中。
SelectDirBrowseLabel=默认路径通常无需修改。若要更换，请单击「浏览」。
DiskSpaceMBLabel=大约需要 [mb] MB 可用空间。
SelectTasksLabel2=可选附加项：
ReadyLabel1=准备就绪。单击「开始安装」继续。
ReadyLabel2a=将执行以下操作：
InstallingLabel=正在安装 ArkPlots…
FinishedHeadingLabel=安装完成
FinishedLabelNoIcons=ArkPlots 已就绪。祝检索愉快。
FinishedLabel=ArkPlots 已就绪。可从开始菜单或桌面快捷方式启动。
ClickFinish=单击「完成」关闭向导。
ConfirmUninstall=确定要卸载 %1 吗？%n阅读进度（Read_record.json）不会被自动删除。
StatusExtractFiles=正在展开文件…
StatusCreateIcons=正在创建快捷方式…
StatusCreateDirs=正在创建目录…
StatusSavingUninstall=正在写入卸载信息…

[CustomMessages]
CreateDesktopIcon=在桌面创建快捷方式
LaunchAfterInstall=安装完成后启动 ArkPlots
UpgradeConfirm=检测到本机已安装 ArkPlots。%n%n点击「是」将更新到 {#MyAppVersion}（不会清空阅读进度）。%n点击「否」取消。
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
  { In-app silent/progress upgrade must not pop a confirm dialog. }
  if WizardSilent then
    Result := True
  else if IsUpgrade then
    Result := MsgBox(ExpandConstant('{cm:UpgradeConfirm}'), mbConfirmation, MB_YESNO) = IDYES
  else
    Result := True;
end;
