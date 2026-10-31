# ArkPlots Android（手机版）说明

本目录包含 ArkPlots 的 Android APK 打包工程：原 Web 前端改为**纯离线模式**，剧情数据随 APK 打包，阅读记录存在手机本地，无需在手机上运行 Python。

## 产物

- APK：`ArkPlots-v26.10.28.11-android.apk`（约 9MB，自签名，直接安装）
- 包名：`com.arkplots.mobile`，版本名：`26.10.28.11`（与上游 `app_info.py` 对齐）

> 封面图为手机端重新压缩过（原图 45MB → 800px/质量78 的 JPEG 共 5.5MB，`covers.json` 映射同步更新），
> 原图备份在 `E:\zcode\arkplots-mobile\covers-original-backup`。桌面版不受影响（桌面 `web/public` 仅在
> 移动构建时使用；如需恢复原图，把备份目录拷回 `web/public/covers` 即可）。

## 与桌面版的差异

| 功能 | 桌面版 | Android 版 |
|---|---|---|
| 剧情数据 | `Plotline.json`（本地文件） | 打包进 APK（`web/public/Plotline.json`） |
| 阅读记录 | `Read_record.json` | 手机 localStorage（跟随 App，卸载即清除） |
| 检查更新 | 下载新版 exe 并替换 | **手动**触发剧情数据更新：从 GitHub（jsDelivr 优先，raw 兜底）拉最新 `Plotline.json`，应用内即时生效。**启动时不自动检查**（理由见下） |
| 界面 | 三栏桌面布局 | 窄屏单列自适应布局 |

代码改动分三层：

- **平台判断** —— `web/src/platform.ts` 只导出 `IS_NATIVE_APP`。单独成文件是因为 `settings.ts` 也要用它定默认值；直接放 `api.ts` 会让设置层反向依赖 API 层。
- **数据层分流** —— `web/src/api.ts`：Capacitor 环境读打包的 `Plotline.json`、记录存 localStorage；桌面模式仍走原来的本地服务，行为不变。
- **界面适配** —— App.tsx / SettingsModal / UpdateDialogs 的移动端文案分支、i18n 新增 `version.mobile*` 与 `settings.mobileCheckUpdatesOnLaunch`、theme.css 追加窄屏媒体查询。

### 为什么启动时不自动检查更新

桌面版 `checkUpdatesOnLaunch` 默认开启合理——它查的是真实发版，点一下就能换新版本。

移动端不同：数据已经打进 APK，启动时联网多半只检出一个"没有新数据"，代价却是一次冷启动往返。两个源（jsDelivr / raw.githubusercontent）在国内都不稳定，卡住就是黑屏几秒才进主界面。

所以 `settings.ts` 里这个默认值改成了 `!IS_NATIVE_APP`：**移动端默认关，桌面保持不变**。想同步剧情数据时，到「设置 → 版本」勾选，或直接点「检查更新」。

### 数据更新这块可以整体替换

`api.ts` 里所有"从上游拉数据"的代码都标了 `[UPDATER]`，并有分节注释说明范围。要换实现（或干脆去掉联网同步），按那段注释的三步删干净即可——离线读数据、阅读记录、窄屏 UI 都不依赖它。

## 手机安装

1. 把 `app-release.apk` 传到手机（微信/QQ 文件、USB、网盘均可）
2. 点击安装，系统提示「未知来源/安装未知应用」时允许（自签名应用的标准流程）
3. 打开即可离线使用；阅读进度自动保存在本机

## 上游剧情数据更新后如何重新打包

```bash
cd ArkPlots
# 1. 同步上游最新 Plotline.json（含新增剧情）
git pull                       # 或手动覆盖 Plotline.json
node -e "require('fs').copyFileSync('Plotline.json','web/public/Plotline.json')"

# 2. 重建前端 + 拷入 Android 工程
cd web
node build-mobile.mjs          # vite build + 去掉 Google Fonts 外链
npx cap sync android

# 3. 构建 APK（需要 JAVA_HOME / local.properties 指向本地工具链）
cd android
./gradlew.bat assembleRelease
```

不想重装 APK 时，也可以在 App 内「设置 → 检查更新」手动同步最新剧情数据（效果相同）。这个同步默认不会在启动时自动进行，需要时点一下就行。

## WebView 里会坏、已经处理的地方

桌面浏览器正常的 API 在 Android WebView 里不一定能用，这几处已经改掉：

- **外链** —— WebView 没有"新窗口"，`window.open` 和 `<a target="_blank">` 点下去是静默无响应。视频链接、更新公告里的链接、设置里的仓库链接现在统一走 `openExternal()`：移动端用 `@capacitor/browser` 打开 Chrome Custom Tab，桌面仍是普通新标签页（`ExternalLink` 内部按平台判断，桌面行为没有任何变化）。
- **启动自动检查** —— 见上一节，移动端默认关闭。

插件是按需加载的，`@capacitor/browser` 会被单独打成一个 8 KB 的 chunk，桌面 bundle 不会加载它。

## 还没验证的

- **剪贴板**（`navigator.clipboard.writeText`，视频弹窗的「复制链接」）—— Capacitor 的 WebView 运行在 secure context 里，按规范应该可用，但没有真机验证过。如果发现失效，需要接 `@capacitor/clipboard`。
- **真机安装与签名** —— 目前的构建链路只在命令行验证到 `vite build` + `cap sync`，APK 的实际打包和安装需要 Android SDK 与 keystore，见下一节。

## 签名

- Release 构建使用 `web/android/keystore.properties`（已 gitignore）里指向的 keystore 签名；没有该文件时自动回退 debug 签名（仅供本机调试）。
- 自建 keystore：`keytool -genkey -v -keystore my-release.keystore -alias arkplots -keyalg RSA -validity 10950`，然后把路径/口令写进 `keystore.properties`。
- **升级安装新 APK 时必须用同一 keystore 签名**，否则需先卸载旧版（卸载会清掉阅读记录）。请妥善保存 keystore 文件，不要提交进仓库。
