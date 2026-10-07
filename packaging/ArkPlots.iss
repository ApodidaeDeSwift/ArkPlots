; ArkPlots Windows installer (Inno Setup 6).
; Visual language mirrors the in-app UI (teal terminal / plotline archive),
; not Inno's stock modern-dark chrome.

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
; classic + custom art = less stock "modern dark" chrome
WizardStyle=classic
WizardSizePercent=120
WizardImageFile=wizard_side.png
WizardSmallImageFile=wizard_top.png
WizardImageStretch=yes
WizardImageBackColor=$19120B
WizardSmallImageBackColor=$19120B
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
; Chocolatey / minimal Inno installs often omit Languages\*.isl — use Default
; and override UI strings in [Messages] (Chinese copy below).
Name: "chinesesimplified"; MessagesFile: "compiler:Default.isl"

[Messages]
SetupAppTitle=ArkPlots
SetupWindowTitle=ArkPlots  ·  {#MyAppVersion}
ButtonBack=< 返回(&B)
ButtonNext=继续(&N) >
ButtonInstall=开始安装(&I)
ButtonFinish=完成(&F)
BeveledLabel=PLOTLINE ARCHIVE
WelcomeLabel1=欢迎使用 ArkPlots
WelcomeLabel2=接下来会把程序安装到本机。%n%n阅读进度保存在安装目录的本地文件里；升级不会清空它们。
SelectDirLabel3=选择安装目录。阅读进度与配置会保存在此路径下。
SelectDirBrowseLabel=可保留默认路径，或单击「浏览」选择其他位置。
DiskSpaceMBLabel=预计占用 [mb] MB
SelectTasksLabel2=附加选项
ReadyLabel1=准备就绪。单击「开始安装」继续。
ReadyLabel2a=将执行：
InstallingLabel=正在安装 ArkPlots…
FinishedHeadingLabel=安装完成
FinishedLabelNoIcons=ArkPlots 已就绪，可以开始检索剧情。
FinishedLabel=ArkPlots 已就绪。可通过开始菜单或桌面快捷方式启动。
ClickFinish=单击「完成」关闭安装程序。
ConfirmUninstall=确定卸载 %1？%n阅读进度文件不会被自动删除。
StatusExtractFiles=正在解包…
StatusCreateIcons=正在创建快捷方式…
StatusCreateDirs=正在创建目录…
StatusSavingUninstall=正在写入卸载信息…

[CustomMessages]
CreateDesktopIcon=在桌面创建快捷方式
LaunchAfterInstall=安装完成后启动 ArkPlots
UpgradeConfirm=本机已安装 ArkPlots。%n%n「是」= 更新到 {#MyAppVersion}（保留阅读进度）%n「否」= 取消
NameAndVersion=%1  %2

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "附加选项:"; Flags: unchecked

[Files]
Source: "..\dist\ArkPlots\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\Plotline.json"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchAfterInstall}"; Flags: nowait postinstall skipifsilent

[Code]
const
  { Delphi TColor is BGR; mirrors web/src/styles/theme.css }
  CBg0 = $19120B;      { #0b1219 }
  CBg1 = $241B11;      { #111b24 }
  CAccent = $C7C73E;   { #3ec7c7 }
  CText = $EFE6D7;     { #d7e6ef }
  CTextDim = $B2A08A;  { #8aa0b2 }

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

procedure StyleLabel(L: TNewStaticText; Color: Integer; Bold: Boolean);
begin
  if L = nil then Exit;
  L.Font.Color := Color;
  L.Font.Name := 'Segoe UI';
  if Bold then
    L.Font.Style := [fsBold]
  else
    L.Font.Style := [];
end;

procedure ApplyArkPlotsTheme;
begin
  WizardForm.Color := CBg0;
  WizardForm.MainPanel.Color := CBg0;
  WizardForm.InnerPage.Color := CBg1;
  WizardForm.InnerNotebook.Color := CBg1;
  WizardForm.OuterNotebook.Color := CBg0;
  WizardForm.Bevel.Visible := False;

  WizardForm.WizardBitmapImage.BackColor := CBg0;
  WizardForm.WizardSmallBitmapImage.BackColor := CBg0;

  StyleLabel(WizardForm.PageNameLabel, CAccent, True);
  StyleLabel(WizardForm.PageDescriptionLabel, CTextDim, False);
  StyleLabel(WizardForm.WelcomeLabel1, CText, True);
  StyleLabel(WizardForm.WelcomeLabel2, CTextDim, False);
  StyleLabel(WizardForm.FinishedLabel, CTextDim, False);
  StyleLabel(WizardForm.FinishedHeadingLabel, CText, True);

  WizardForm.PageNameLabel.Font.Name := 'Consolas';
  WizardForm.PageNameLabel.Font.Size := 9;
  WizardForm.BeveledLabel.Font.Name := 'Consolas';
  WizardForm.BeveledLabel.Font.Color := CAccent;
  WizardForm.BeveledLabel.Font.Size := 8;

  WizardForm.DirEdit.Color := CBg0;
  WizardForm.DirEdit.Font.Color := CText;
  WizardForm.GroupEdit.Color := CBg0;
  WizardForm.GroupEdit.Font.Color := CText;
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

procedure InitializeWizard;
begin
  ApplyArkPlotsTheme;
  WizardForm.WelcomeLabel1.Caption := 'ArkPlots';
  WizardForm.WelcomeLabel1.Font.Size := 16;
  WizardForm.WelcomeLabel2.Caption :=
    'PLOTLINE ARCHIVE  ·  BUILD {#MyAppVersion}' + #13#10#13#10 +
    '将程序安装到本机。阅读进度保存在安装目录的本地文件中；' + #13#10 +
    '升级只会替换程序，不会清空你的剧情进度。';
  WizardForm.FinishedHeadingLabel.Caption := '安装完成';
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  ApplyArkPlotsTheme;
  if CurPageID = wpSelectDir then
  begin
    WizardForm.PageNameLabel.Caption := 'INSTALL PATH';
    WizardForm.PageDescriptionLabel.Caption := '指定程序与本地数据的存放位置';
  end
  else if CurPageID = wpSelectTasks then
  begin
    WizardForm.PageNameLabel.Caption := 'OPTIONS';
    WizardForm.PageDescriptionLabel.Caption := '可选的附加任务';
  end
  else if CurPageID = wpReady then
  begin
    WizardForm.PageNameLabel.Caption := 'READY';
    WizardForm.PageDescriptionLabel.Caption := '确认后开始安装';
  end
  else if CurPageID = wpInstalling then
  begin
    WizardForm.PageNameLabel.Caption := 'INSTALLING';
    WizardForm.PageDescriptionLabel.Caption := '正在写入文件…';
  end
  else if CurPageID = wpFinished then
  begin
    WizardForm.PageNameLabel.Caption := 'DONE';
    WizardForm.PageDescriptionLabel.Caption := 'ArkPlots 已就绪';
  end;
end;
