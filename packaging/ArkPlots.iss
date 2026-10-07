; ArkPlots Windows installer (Inno Setup 6).
; Compile via: python packaging/build_release.py
;   iscc /DMyAppVersion=x.y.z.w packaging/ArkPlots.iss
;
; Packaging choices that reduce antivirus false positives:
;   - Install a PyInstaller *onedir* tree (not a self-extracting onefile exe)
;   - No UPX on the payload
;   - Full VersionInfo metadata on the setup binary

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
; Non-solid compression is slightly less "packed-looking" to some scanners.
Compression=lzma2/fast
SolidCompression=no
WizardStyle=modern
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
; Optional: set SIGNTOOL env / SignTool in CI when you have a code-signing cert.
; SignTool=signtool $p
; SignedUninstaller=yes

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Default.isl"

[Messages]
SetupAppTitle=ArkPlots 安装
SetupWindowTitle=ArkPlots 安装 — {#MyAppVersion}
ButtonBack=< 上一步(&B)
ButtonNext=下一步(&N) >
ButtonInstall=安装(&I)
ButtonFinish=完成(&F)
SelectDirLabel3=安装程序将把 [name] 安装到下列文件夹。
SelectDirBrowseLabel=单击「下一步」继续。若要选择其他文件夹，单击「浏览」。
DiskSpaceMBLabel=至少需要 [mb] MB 可用磁盘空间。
SelectTasksLabel2=请选择要执行的附加任务，然后单击「下一步」。
ReadyLabel1=安装程序准备将 [name] 安装到你的计算机。
InstallingLabel=正在安装 [name]，请稍候…
FinishedHeadingLabel=正在完成 [name] 安装向导
FinishedLabelNoIcons=安装程序已将 [name] 安装到你的计算机。
FinishedLabel=安装程序已将 [name] 安装到你的计算机。单击「完成」退出。
ClickFinish=单击「完成」退出安装程序。
ConfirmUninstall=确定要完全移除 %1 及其所有组件吗？阅读进度文件不会被自动删除。

[CustomMessages]
CreateDesktopIcon=在桌面创建快捷方式
LaunchAfterInstall=安装完成后运行 ArkPlots
UpgradeConfirm=检测到本机已安装 ArkPlots。%n%n点击「是」将更新程序（不会清空阅读进度等用户数据）。%n点击「否」取消。

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "附加任务:"; Flags: unchecked

[Files]
; Onedir payload from PyInstaller (ArkPlots.exe + DLLs/data). Always replace on upgrade.
Source: "..\dist\ArkPlots\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Story catalog for first install / refresh. Never ships Read_record.json.
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
  { In-app silent upgrade must not pop a confirm dialog. }
  if WizardSilent then
    Result := True
  else if IsUpgrade then
    Result := MsgBox(ExpandConstant('{cm:UpgradeConfirm}'), mbConfirmation, MB_YESNO) = IDYES
  else
    Result := True;
end;
