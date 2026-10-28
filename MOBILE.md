# ArkPlots Android（手机版）说明

本目录包含 ArkPlots 的 Android APK 打包工程：原 Web 前端改为**纯离线模式**，剧情数据随 APK 打包，阅读记录存在手机本地，无需在手机上运行 Python。

## 产物

- APK：`ArkPlots-v26.10.22.3-android.apk`（约 9MB，自签名，直接安装）
- 包名：`com.arkplots.mobile`，版本名：`26.10.22.3`（与上游 `app_info.py` 对齐）

> 封面图为手机端重新压缩过（原图 45MB → 800px/质量78 的 JPEG 共 5.5MB，`covers.json` 映射同步更新），
> 原图备份在 `E:\zcode\arkplots-mobile\covers-original-backup`。桌面版不受影响（桌面 `web/public` 仅在
> 移动构建时使用；如需恢复原图，把备份目录拷回 `web/public/covers` 即可）。

## 与桌面版的差异

| 功能 | 桌面版 | Android 版 |
|---|---|---|
| 剧情数据 | `Plotline.json`（本地文件） | 打包进 APK（`web/public/Plotline.json`） |
| 阅读记录 | `Read_record.json` | 手机 localStorage（跟随 App，卸载即清除） |
| 检查更新 | 下载新版 exe 并替换 | **检查剧情数据更新**：从 GitHub（jsDelivr/CDN 优先）拉最新 `Plotline.json`，应用内即时生效 |
| 界面 | 三栏桌面布局 | 窄屏单列自适应布局 |

代码改动集中在 `web/src/api.ts`（`IS_NATIVE_APP` 分流：Capacitor 环境走本地实现，桌面模式行为不变），以及 App.tsx / SettingsModal / UpdateDialogs 的移动端文案分支、i18n 新增 `version.mobile*` 文案、theme.css 追加移动端媒体查询。

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

不想重装 APK 时，也可以在 App 内「设置 → 检查更新」直接在线同步最新剧情数据（效果相同）。

## 签名

- Release 构建使用 `web/android/keystore.properties`（已 gitignore）里指向的 keystore 签名；没有该文件时自动回退 debug 签名（仅供本机调试）。
- 自建 keystore：`keytool -genkey -v -keystore my-release.keystore -alias arkplots -keyalg RSA -validity 10950`，然后把路径/口令写进 `keystore.properties`。
- **升级安装新 APK 时必须用同一 keystore 签名**，否则需先卸载旧版（卸载会清掉阅读记录）。请妥善保存 keystore 文件，不要提交进仓库。
