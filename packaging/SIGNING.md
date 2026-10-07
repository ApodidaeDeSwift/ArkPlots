# 代码签名与 SmartScreen「发布者未知」

## 这条提示是什么？

```
Microsoft Defender SmartScreen 阻止了无法识别的应用启动。
发行者: 发布者未知
```

这**不是**杀毒引擎误报文件内容，而是 Windows 信誉系统：安装包**没有 Authenticode 数字签名**（或签名不被信任），且文件下载量/信誉还不够。

仅靠「关 UPX / 改 onedir / 换主题」**无法**去掉「发布者未知」。要显示可识别的发行者，必须用**代码签名证书**签名。

## 根本解决办法（推荐）

1. 购买 **代码签名证书**（Code Signing）  
   - 个人/小团队：OV Code Signing（约数百美元/年，视厂商）  
   - 企业常用：EV Code Signing（SmartScreen 信誉建立更快，通常更贵，且需 USB 硬件密钥）  
   - 也可了解 [Azure Trusted Signing](https://learn.microsoft.com/en-us/azure/trusted-signing/)（按量计费，适合已有 Azure 订阅时）
2. 从证书厂商拿到 `.pfx`（或等价私钥），**不要**把证书提交进 Git。
3. 本地或 CI 签名后再发布：

```powershell
# 本地示例（PowerShell）
$env:SIGN_PFX = "D:\secrets\arkplots-codesign.pfx"
$env:SIGN_PFX_PASSWORD = "你的密码"
python packaging/build_release.py
```

`build_release.py` 会在存在 `SIGN_PFX` 时自动用 `signtool` 签名：

- `dist/ArkPlots/ArkPlots.exe`
- `Arkplot_setup_ver*.exe`

需要本机已安装 **Windows SDK** 中的 `signtool.exe`。

### GitHub Actions

在仓库 Settings → Secrets 中添加：

| Secret | 含义 |
| --- | --- |
| `SIGN_PFX_BASE64` | `.pfx` 文件的 Base64 |
| `SIGN_PFX_PASSWORD` | 证书密码 |

工作流会在构建安装包前解码并签名（见 `.github/workflows/app-release.yml`）。

生成 Base64（本地）：

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("arkplots-codesign.pfx")) | Set-Clipboard
```

## 没有证书时的权宜之计

1. 用户侧：SmartScreen 页点「更多信息」→「仍要运行」（仅当你信任该构建时）。
2. 向微软提交样本建立信誉：  
   https://www.microsoft.com/wdsi/filesubmission  
   （选 Software developer → 误报 / 未签名新软件，按表单说明开源与下载地址。）
3. 固定从 GitHub Releases 分发同一文件名/渠道，下载量上来后 SmartScreen 会逐渐放宽，但**仍不如签名可靠**。

## 我们已做的减负措施（仍无法替代签名）

- PyInstaller **onedir**（非 onefile 自解压）
- 关闭 **UPX**
- 安装包由 Inno Setup 生成，并写入完整 VersionInfo

这些能降低启发式杀软误报，但**不能**把「发布者未知」改成你的名字。
