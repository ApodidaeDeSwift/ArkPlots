; ArkPlots Windows installer (Inno Setup 6).
; Deep-blue rounded window. Inner pages, memos and buttons are recolored
; because Inno's classic wizard otherwise leaves them on the system white.

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
ButtonBack=返回(&B)
ButtonNext=继续(&N)
ButtonCancel=取消(&C)
ButtonInstall=开始安装(&I)
ButtonFinish=完成(&F)
ButtonWizardBrowse=浏览(&R)…
ExitSetupMessage=安装还没有完成。%n确定要退出吗？
BeveledLabel=阅读进度会保留在本机
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
; New catalog, extracted before the copy so the still-installed Plotline.json can be read.
Source: "..\Plotline.json"; DestDir: "{tmp}"; DestName: "Plotline.new.json"; Flags: dontcopy
Source: "migrate_read_record.ps1"; DestDir: "{tmp}"; Flags: dontcopy
; Runs on silent in-app updates as well. Fresh installs have no record and skip it.
Source: "..\Plotline.json"; DestDir: "{app}"; Flags: ignoreversion; BeforeInstall: MigrateReadRecord

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchAfterInstall}"; Flags: nowait postinstall skipifsilent

[Code]
const
  { Delphi TColor is $00BBGGRR. Matches web/src/styles/theme.css }
  CBg0 = $19120B;       { #0b1219 }
  CHeader = $3A2B1B;    { #1b2b3a }
  CCard = $302216;      { #162230 }
  CTrack = $4A3824;     { #24384a }
  CAccent = $E8B86E;    { #6eb8e8 }
  CText = $EFE6D7;      { #d7e6ef }
  CTextDim = $B2A08A;   { #8aa0b2 }

var
  ChipBack, ChipNext, ChipCancel, ChipBrowse: TPanel;
  BarTrack, BarFill: TPanel;
  UnBarTrack, UnChipCancel: TPanel;

function DwmSetWindowAttribute(hwnd: HWND; dwAttribute: Cardinal; var pvAttribute: Integer; cbAttribute: Cardinal): Integer;
  external 'DwmSetWindowAttribute@dwmapi.dll stdcall delayload';
function CreateRoundRectRgn(p1, p2, p3, p4, p5, p6: Integer): THandle;
  external 'CreateRoundRectRgn@gdi32.dll stdcall';
function SetWindowRgn(hWnd: HWND; hRgn: THandle; bRedraw: Boolean): Integer;
  external 'SetWindowRgn@user32.dll stdcall';

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

function StripAccel(const S: String): String;
var
  P: Integer;
begin
  Result := S;
  P := Pos('(&', Result);
  if (P > 0) and (Length(Result) >= P + 3) and (Result[P + 3] = ')') then
    Delete(Result, P, 4);
  StringChangeEx(Result, '&', '', True);
end;

procedure StyleStatic(L: TNewStaticText; TextColor, BackColor: Integer; Bold: Boolean);
begin
  if L = nil then Exit;
  L.Color := BackColor;
  L.Font.Color := TextColor;
  L.Font.Name := 'Microsoft YaHei UI';
  if Bold then
    L.Font.Style := [fsBold]
  else
    L.Font.Style := [];
end;

procedure StyleMemo(M: TNewMemo);
begin
  if M = nil then Exit;
  M.Color := CCard;
  M.Font.Color := CText;
  M.Font.Name := 'Microsoft YaHei UI';
  M.BorderStyle := bsNone;
  M.ScrollBars := ssVertical;
end;

procedure StyleCheckList(L: TNewCheckListBox);
begin
  if L = nil then Exit;
  L.Color := CCard;
  L.Font.Color := CText;
  L.Font.Name := 'Microsoft YaHei UI';
  L.BorderStyle := bsNone;
  L.Flat := True;
end;

procedure RoundControl(Control: TWinControl; Radius: Integer);
var
  Rgn: THandle;
begin
  if (Control = nil) or (Control.Width < 4) or (Control.Height < 4) then Exit;
  Rgn := CreateRoundRectRgn(0, 0, Control.Width + 1, Control.Height + 1, Radius, Radius);
  SetWindowRgn(Control.Handle, Rgn, True);
end;

procedure ApplyFormChrome(Form: TForm);
var
  Pref, Attr: Integer;
  Rgn: THandle;
begin
  try
    Pref := 2; { DWMWCP_ROUND }
    DwmSetWindowAttribute(Form.Handle, 33, Pref, 4);
    Pref := 1; { immersive dark title bar }
    DwmSetWindowAttribute(Form.Handle, 20, Pref, 4);
    Attr := CBg0;
    DwmSetWindowAttribute(Form.Handle, 35, Attr, 4); { caption }
    DwmSetWindowAttribute(Form.Handle, 34, Attr, 4); { border }
    Attr := CText;
    DwmSetWindowAttribute(Form.Handle, 36, Attr, 4); { caption text }
  except
  end;
  Rgn := CreateRoundRectRgn(0, 0, Form.Width, Form.Height, 28, 28);
  SetWindowRgn(Form.Handle, Rgn, True);
end;

procedure ColorPage(Page: TNewNotebookPage);
begin
  if Page <> nil then
    Page.Color := CBg0;
end;

procedure MakeChip(var Chip: TPanel);
begin
  Chip := TPanel.Create(WizardForm);
  Chip.Parent := WizardForm;
  Chip.BevelOuter := bvNone;
  Chip.BevelInner := bvNone;
  Chip.BevelKind := bkNone;
  Chip.BorderStyle := bsNone;
  Chip.ParentBackground := False;
  Chip.Alignment := taCenter;
  Chip.Font.Name := 'Microsoft YaHei UI';
  Chip.Font.Size := 9;
  Chip.Cursor := crHandPoint;
  Chip.Visible := False;
end;

procedure PlaceChip(Chip: TPanel; Btn: TNewButton; Fill, TextColor: Integer; Bold: Boolean);
var
  L, T, W, H: Integer;
begin
  if (Chip = nil) or (Btn = nil) then Exit;
  Chip.BevelOuter := bvNone;
  Chip.BevelInner := bvNone;
  Chip.BevelKind := bkNone;
  Chip.BorderStyle := bsNone;
  Chip.ParentBackground := False;
  Chip.Alignment := taCenter;
  Chip.Font.Name := 'Microsoft YaHei UI';
  Chip.Font.Size := 9;
  Chip.Cursor := crHandPoint;
  Chip.Caption := StripAccel(Btn.Caption);
  Chip.Color := Fill;
  Chip.Font.Color := TextColor;
  if Bold then
    Chip.Font.Style := [fsBold]
  else
    Chip.Font.Style := [];
  Chip.Visible := Btn.Visible and Btn.Enabled;
  if Btn.Left < 0 then
  begin
    if Chip.Visible then
      Chip.BringToFront;
    Exit;
  end;
  L := Btn.Left;
  T := Btn.Top;
  W := Btn.Width;
  H := Btn.Height;
  if (W < 8) or (H < 8) then Exit;
  Chip.Parent := Btn.Parent;
  Chip.SetBounds(L, T, W, H);
  RoundControl(Chip, H);
  Btn.Left := -W - 40;
  if Chip.Visible then
    Chip.BringToFront;
end;

procedure ChipBackClick(Sender: TObject);
begin
  WizardForm.BackButton.OnClick(WizardForm.BackButton);
end;

procedure ChipNextClick(Sender: TObject);
begin
  WizardForm.NextButton.OnClick(WizardForm.NextButton);
end;

procedure ChipCancelClick(Sender: TObject);
begin
  WizardForm.CancelButton.OnClick(WizardForm.CancelButton);
end;

procedure ChipBrowseClick(Sender: TObject);
begin
  WizardForm.DirBrowseButton.OnClick(WizardForm.DirBrowseButton);
end;

procedure PlaceActionChips;
begin
  PlaceChip(ChipBack, WizardForm.BackButton, CHeader, CText, False);
  PlaceChip(ChipNext, WizardForm.NextButton, CAccent, CBg0, True);
  PlaceChip(ChipCancel, WizardForm.CancelButton, CHeader, CTextDim, False);
  PlaceChip(ChipBrowse, WizardForm.DirBrowseButton, CHeader, CText, False);
end;

procedure ApplyArkPlotsTheme;
begin
  WizardForm.Color := CBg0;
  WizardForm.Font.Name := 'Microsoft YaHei UI';
  WizardForm.Font.Color := CText;

  WizardForm.MainPanel.ParentBackground := False;
  WizardForm.MainPanel.BevelOuter := bvNone;
  WizardForm.MainPanel.BevelInner := bvNone;
  WizardForm.MainPanel.Color := CHeader;
  WizardForm.Bevel.Visible := False;
  WizardForm.Bevel1.Visible := False;

  ColorPage(WizardForm.WelcomePage);
  ColorPage(WizardForm.InnerPage);
  ColorPage(WizardForm.FinishedPage);
  ColorPage(WizardForm.LicensePage);
  ColorPage(WizardForm.PasswordPage);
  ColorPage(WizardForm.InfoBeforePage);
  ColorPage(WizardForm.UserInfoPage);
  ColorPage(WizardForm.SelectDirPage);
  ColorPage(WizardForm.SelectComponentsPage);
  ColorPage(WizardForm.SelectProgramGroupPage);
  ColorPage(WizardForm.SelectTasksPage);
  ColorPage(WizardForm.ReadyPage);
  ColorPage(WizardForm.PreparingPage);
  ColorPage(WizardForm.InstallingPage);
  ColorPage(WizardForm.InfoAfterPage);

  StyleStatic(WizardForm.PageNameLabel, CText, CHeader, True);
  StyleStatic(WizardForm.PageDescriptionLabel, CTextDim, CHeader, False);
  WizardForm.PageNameLabel.Font.Size := 12;
  StyleStatic(WizardForm.WelcomeLabel1, CText, CBg0, True);
  StyleStatic(WizardForm.WelcomeLabel2, CTextDim, CBg0, False);
  StyleStatic(WizardForm.FinishedLabel, CTextDim, CBg0, False);
  StyleStatic(WizardForm.FinishedHeadingLabel, CText, CBg0, True);
  StyleStatic(WizardForm.BeveledLabel, CAccent, CBg0, False);
  StyleStatic(WizardForm.SelectDirLabel, CText, CBg0, False);
  StyleStatic(WizardForm.SelectDirBrowseLabel, CTextDim, CBg0, False);
  StyleStatic(WizardForm.DiskSpaceLabel, CTextDim, CBg0, False);
  StyleStatic(WizardForm.SelectTasksLabel, CText, CBg0, False);
  StyleStatic(WizardForm.ReadyLabel, CText, CBg0, False);
  StyleStatic(WizardForm.StatusLabel, CText, CBg0, False);
  StyleStatic(WizardForm.FilenameLabel, CTextDim, CBg0, False);
  StyleStatic(WizardForm.PreparingLabel, CText, CBg0, False);

  WizardForm.DirEdit.Color := CCard;
  WizardForm.DirEdit.Font.Color := CText;
  WizardForm.DirEdit.Font.Name := 'Microsoft YaHei UI';
  WizardForm.DirEdit.BorderStyle := bsNone;
  WizardForm.GroupEdit.Color := CCard;
  WizardForm.GroupEdit.Font.Color := CText;
  WizardForm.GroupEdit.Font.Name := 'Microsoft YaHei UI';

  WizardForm.NoIconsCheck.Color := CBg0;
  WizardForm.NoIconsCheck.Font.Color := CText;
  WizardForm.NoIconsCheck.Font.Name := 'Microsoft YaHei UI';
  StyleCheckList(WizardForm.TasksList);
  StyleCheckList(WizardForm.RunList);
  StyleMemo(WizardForm.ReadyMemo);
  StyleMemo(WizardForm.PreparingMemo);

  WizardForm.ProgressGauge.Visible := False;
end;

procedure EnsureInstallBar;
begin
  if BarTrack <> nil then Exit;
  BarTrack := TPanel.Create(WizardForm);
  BarTrack.Parent := WizardForm.InstallingPage;
  BarTrack.BevelOuter := bvNone;
  BarTrack.BevelInner := bvNone;
  BarTrack.ParentBackground := False;
  BarTrack.Caption := '';
  BarTrack.Color := CTrack;
  BarTrack.SetBounds(
    WizardForm.ProgressGauge.Left,
    WizardForm.ProgressGauge.Top,
    WizardForm.ProgressGauge.Width,
    10);
  RoundControl(BarTrack, 10);

  BarFill := TPanel.Create(WizardForm);
  BarFill.Parent := BarTrack;
  BarFill.BevelOuter := bvNone;
  BarFill.BevelInner := bvNone;
  BarFill.ParentBackground := False;
  BarFill.Caption := '';
  BarFill.Color := CAccent;
  BarFill.SetBounds(0, 0, 12, BarTrack.Height);
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
end;

procedure InitializeWizard;
begin
  MakeChip(ChipBack);
  MakeChip(ChipNext);
  MakeChip(ChipCancel);
  MakeChip(ChipBrowse);
  ChipBack.OnClick := @ChipBackClick;
  ChipNext.OnClick := @ChipNextClick;
  ChipCancel.OnClick := @ChipCancelClick;
  ChipBrowse.OnClick := @ChipBrowseClick;

  ApplyArkPlotsTheme;
  ApplyFormChrome(WizardForm);

  WizardForm.WelcomeLabel1.Caption := 'ArkPlots';
  WizardForm.WelcomeLabel1.Font.Size := 20;
  WizardForm.WelcomeLabel2.WordWrap := True;
  if IsUpgrade then
    WizardForm.WelcomeLabel2.Caption :=
      '这台电脑上已经有 ArkPlots。继续会把它更新到 {#MyAppVersion}。' + #13#10 + #13#10 +
      '阅读进度、配置和封面都留在原来的目录里，这次只替换程序本身。'
  else
    WizardForm.WelcomeLabel2.Caption :=
      '把 ArkPlots 安装到这台电脑。' + #13#10 + #13#10 +
      '剧情阅读进度会保存在安装目录中。以后的更新只会替换程序，不会清掉这些文件。';
  WizardForm.AdjustLabelHeight(WizardForm.WelcomeLabel2);
  WizardForm.FinishedHeadingLabel.Caption := '安装完成';
  WizardForm.FinishedHeadingLabel.Font.Size := 16;
  WizardForm.FinishedLabel.Caption :=
    'ArkPlots 已经可以使用。阅读进度会留在安装目录里。';
  WizardForm.FinishedLabel.WordWrap := True;
  PlaceActionChips;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  ApplyArkPlotsTheme;
  ApplyFormChrome(WizardForm);
  if CurPageID = wpWelcome then
  begin
    if IsUpgrade then
      WizardForm.NextButton.Caption := '开始更新(&N)'
    else
      WizardForm.NextButton.Caption := '继续(&N)';
  end
  else if CurPageID = wpSelectDir then
  begin
    WizardForm.PageNameLabel.Caption := '安装位置';
    WizardForm.PageDescriptionLabel.Caption := '程序和阅读进度都会放在这个目录';
  end
  else if CurPageID = wpSelectTasks then
  begin
    WizardForm.PageNameLabel.Caption := '附加选项';
    WizardForm.PageDescriptionLabel.Caption := '可以现在创建桌面快捷方式';
  end
  else if CurPageID = wpReady then
  begin
    if IsUpgrade then
    begin
      WizardForm.PageNameLabel.Caption := '准备更新';
      WizardForm.PageDescriptionLabel.Caption := '确认后开始替换程序';
      WizardForm.NextButton.Caption := '开始更新(&I)';
    end
    else
    begin
      WizardForm.PageNameLabel.Caption := '准备安装';
      WizardForm.PageDescriptionLabel.Caption := '确认目录后开始';
    end;
  end
  else if CurPageID = wpInstalling then
  begin
    WizardForm.PageNameLabel.Caption := '正在安装';
    WizardForm.PageDescriptionLabel.Caption := '请稍候，不要关闭这个窗口';
    EnsureInstallBar;
  end
  else if CurPageID = wpFinished then
  begin
    WizardForm.PageNameLabel.Caption := '安装完成';
    WizardForm.PageDescriptionLabel.Caption := '可以开始检索剧情了';
  end;
  PlaceActionChips;
end;

procedure CurInstallProgressChanged(CurProgress, MaxProgress: Integer);
var
  W: Integer;
begin
  if (BarTrack = nil) or (BarFill = nil) or (MaxProgress <= 0) then Exit;
  W := BarTrack.Width * CurProgress div MaxProgress;
  if W < 8 then W := 8;
  if W > BarTrack.Width then W := BarTrack.Width;
  BarFill.Width := W;
end;

procedure UnChipCancelClick(Sender: TObject);
begin
  UninstallProgressForm.CancelButton.OnClick(UninstallProgressForm.CancelButton);
end;

procedure InitializeUninstallProgressForm;
begin
  ApplyFormChrome(UninstallProgressForm);
  UninstallProgressForm.Color := CBg0;
  UninstallProgressForm.Font.Name := 'Microsoft YaHei UI';
  UninstallProgressForm.Font.Color := CText;
  UninstallProgressForm.InnerPage.Color := CBg0;
  UninstallProgressForm.InstallingPage.Color := CBg0;
  UninstallProgressForm.MainPanel.ParentBackground := False;
  UninstallProgressForm.MainPanel.BevelOuter := bvNone;
  UninstallProgressForm.MainPanel.BevelInner := bvNone;
  UninstallProgressForm.MainPanel.Color := CHeader;
  UninstallProgressForm.Bevel.Visible := False;
  UninstallProgressForm.Bevel1.Visible := False;
  StyleStatic(UninstallProgressForm.PageNameLabel, CText, CHeader, True);
  StyleStatic(UninstallProgressForm.PageDescriptionLabel, CTextDim, CHeader, False);
  StyleStatic(UninstallProgressForm.StatusLabel, CText, CBg0, False);
  StyleStatic(UninstallProgressForm.BeveledLabel, CAccent, CBg0, False);
  UninstallProgressForm.PageNameLabel.Caption := '正在卸载';
  UninstallProgressForm.PageNameLabel.Font.Size := 12;
  UninstallProgressForm.PageDescriptionLabel.Caption := '阅读进度文件会留在原来的目录';
  UninstallProgressForm.ProgressBar.Visible := False;

  UnBarTrack := TPanel.Create(UninstallProgressForm);
  UnBarTrack.Parent := UninstallProgressForm.InstallingPage;
  UnBarTrack.BevelOuter := bvNone;
  UnBarTrack.ParentBackground := False;
  UnBarTrack.Caption := '';
  UnBarTrack.Color := CAccent;
  UnBarTrack.SetBounds(
    UninstallProgressForm.ProgressBar.Left,
    UninstallProgressForm.ProgressBar.Top,
    UninstallProgressForm.ProgressBar.Width,
    10);
  RoundControl(UnBarTrack, 10);

  UnChipCancel := TPanel.Create(UninstallProgressForm);
  UnChipCancel.OnClick := @UnChipCancelClick;
  PlaceChip(UnChipCancel, UninstallProgressForm.CancelButton, CHeader, CTextDim, False);
end;

// Plot ids follow array order. Read_record.json is keyed by those ids, so an
// inserted story would slide every later status onto the wrong plot. Remap by
// plot name while the installed Plotline.json is still the previous catalog.
procedure MigrateReadRecord;
var
  ResultCode: Integer;
  OldPlot, NewPlot, RecordPath, Script, Params: String;
begin
  OldPlot := ExpandConstant('{app}\Plotline.json');
  RecordPath := ExpandConstant('{app}\Read_record.json');
  if (not FileExists(OldPlot)) or (not FileExists(RecordPath)) then
    Exit;
  ExtractTemporaryFile('migrate_read_record.ps1');
  ExtractTemporaryFile('Plotline.new.json');
  Script := ExpandConstant('{tmp}\migrate_read_record.ps1');
  NewPlot := ExpandConstant('{tmp}\Plotline.new.json');
  Params :=
    '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' + Script + '"' +
    ' -OldPlotline "' + OldPlot + '"' +
    ' -NewPlotline "' + NewPlot + '"' +
    ' -Record "' + RecordPath + '"';
  if not Exec(ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe'),
              Params, '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
    RaiseException('无法启动阅读记录迁移。安装已中止，阅读进度未被修改。');
  if ResultCode <> 0 then
    RaiseException('阅读记录迁移失败。安装已中止，阅读进度未被修改。');
end;
