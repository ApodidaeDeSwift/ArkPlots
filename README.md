# ArkPlots

**明日方舟剧情线梳理工具**

[English](README.en.md) | 简体中文

---

## 普通玩家只需要看这里

本地记录、筛选与跟踪《明日方舟》剧情（主线、别传、故事集、集成战略等），管理阅读进度，并按前置关系推荐「该补什么 / 能接着读什么」。

喜欢的话，欢迎在右上角点一颗 ⭐。

### 下载后怎么用

1. 拿到发布包里的 **`Arkplot_ver26.9.23.2.exe`**，以及同目录下的 **`Plotline.json`**（剧情数据）。
2. 双击 exe 即可。会打开标题为 **ArkPlots** 的独立窗口（约 1400×900，可调大小），**不会**弹出命令行黑框，也**不会**强制打开系统浏览器。
3. 关闭窗口即退出；阅读进度会写回同目录的 `Read_record.json`。

### 同目录需要有什么

| 文件 | 说明 |
| --- | --- |
| `Plotline.json` | **必需**。剧情条目数据，须与 exe 放在同一文件夹 |
| `Read_record.json` | 阅读记录。没有时会自动生成 |

Web 界面已打进 exe，旁边**不需要**再放 `web/dist`。Windows 一般已自带 Edge WebView2；若窗口打不开，请确认系统已安装 WebView2。

### 能做什么（简述）

- 按日期、类型、国家、干员、阶段、势力、相关标签等筛选
- 设置阅读状态：未读 / 计划读 / 正在读 / 已读（可单条或批量）
- 查看必要 / 可选前置，并按进度给出补读与续读推荐
- 关联视频：打开链接或复制
- 右上角切换简体中文 / English；详情可显示宣传图（有数据时）

### 关于不同服务器

日期目前以**大陆服**为准，推荐视频以 **Bilibili** 为主。若有外国服玩家愿意补充其他服信息，欢迎联系。

### 作者与支持

- GitHub：[@ApodidaeDeSwift](https://github.com/ApodidaeDeSwift)
- 微信：`Quantumaster233` · QQ：`3195582616`
- B站：[space.bilibili.com/281039105](https://space.bilibili.com/281039105)

如果本工具对你有帮助，请作者喝一杯蜜雪冰城：

![支持我们](coffee.png)

### 许可与声明

本项目为个人学习与整理工具。《明日方舟》及相关文本、设定归上海鹰角网络科技有限公司等权利方所有。数据与界面仅供学习、交流，请勿用于商业用途。欢迎在 GitHub 提 Issue / PR。

---

## 想做修改或高级启动的玩家请看这里

面向从源码运行、改前端 / 数据、重新打包的用户。

### 环境

| 用途 | 依赖 |
| --- | --- |
| 独立窗口（默认） | Python 3.10+，[pywebview](https://pywebview.flowrl.com/)（`pip install -r requirements.txt`）；Windows 用系统 Edge WebView2 |
| 构建前端 | [Node.js](https://nodejs.org/) 18+（含 npm） |
| 可选：系统浏览器 | `python main.py --browser` |
| 可选：旧版桌面 UI | tkinter（多数 Python 自带），`python main.py --tk` |

数据文件仍须与程序同目录：`Plotline.json`（必需）、`Read_record.json`（可自动创建）。

### 前端构建

首次，或改过 `web/` 之后：

```bash
cd web
npm install
npm run build
cd ..
```

产物在 `web/dist/`。源码启动若缺失会提示先构建。

### 源码启动

```bash
pip install -r requirements.txt
python main.py
```

默认用 **pywebview** 打开独立窗口，不打开系统浏览器。首选端口 `8765`；被占用则自动改用后续空闲端口，窗口加载实际绑定地址。关窗口会停本地服务。

常用参数（以 `main.py` 为准）：

```bash
python main.py --port 8765     # 指定首选端口
python main.py --browser       # 改用系统浏览器
python main.py --no-browser    # 只起本地服务，不开窗口（给前端热更新用）
python main.py --tk            # 旧版 tkinter 界面
```

也可直接跑服务端（默认仍会尝试开浏览器；联调请加 `--no-browser`）：

```bash
python server.py --port 8765 --no-browser
```

`server.py` 仅支持 `--port`、`--no-browser`。

### 开发联调

```bash
# 终端 1：API（默认 8765）
python server.py --no-browser

# 终端 2：Vite（已代理 /api → 8765）
cd web
npm run dev
```

### 数据字段

#### Plotline.json

按发布顺序记录剧情条目，常见字段：

| 字段 | 说明 |
| --- | --- |
| `id` | 唯一标识 |
| `name` | 剧情名称（中文；展示层可按语言映射） |
| `date` | 发布日期（`YYYY-MM-DD`，大陆服） |
| `class` | 类型：`main` / `sidestory` / `interlude` / `ministory` / `manga` / `anime` / `rougelike` / `RA` / `other` |
| `country` | 相关国家 / 地区 |
| `new_operator` | 同期干员 |
| `plot_stage` | 剧情阶段 |
| `related_power` | 相关势力 |
| `related_plot` | 相关标签 |
| `description` | 描述 |
| `necessary_plot` | 必要前置（可含 `id`、`reason`，可选 `reason_en`） |
| `optional_plot` | 可选前置 |
| `Videos` | 关联视频 |

#### Read_record.json

键为剧情 `id`（字符串），值为：`未读` | `计划读` | `正在读` | `已读`。  
数据层状态值固定为中文；切换界面语言只改显示文案，不改写文件。

### 多语言（i18n）

- 默认 `zh-CN`，另有 `en-US`；偏好存在 `localStorage`（键 `arkplots.locale`）
- 界面文案：`web/src/i18n/locales/`；内容对照：`web/src/i18n/content/`
- 翻译多由 Cursor 查萌娘百科起草，**可能不准**；发现错误请提 Issue / PR

添加新语言：在 `locales/` 新增语言包 → 在 `locales/index.ts` 的 `localeRegistry` 注册 →（可选）补 `content/` 映射 → `npm run build`。

### 打包 exe（无命令行窗口）

版本号写在仓库根目录的 `app_info.py`（`VERSION`）。一键打包：

```bash
pip install -r requirements.txt pyinstaller
cd web && npm install && cd ..
python packaging/build_release.py
```

脚本会：同步 `web/src/version.ts` → 构建前端 → 用 `packaging/ArkPlots.spec` 打出稳定名 `dist/ArkPlots.exe` → 再复制为分发名 `Arkplot_ver{VERSION}.exe`。

`Plotline.json` / `Read_record.json` **不**打进包，运行时从 exe 所在目录读取。无控制台黑框由 spec 的 `console=False` 决定。目标机需 Edge WebView2（Win10/11 通常已有）。

后续做自动更新时：配置 `app_info.UPDATE_MANIFEST_URL`，客户端可通过 `GET /api/version` 读取当前版本与清单地址。

### 项目结构

```
ArkPlots/
├── Plotline.json          # 剧情数据
├── Read_record.json       # 阅读记录
├── main.py                # 启动器（默认独立窗口；--browser / --tk 可选）
├── requirements.txt       # pywebview 等
├── server.py              # 本地 HTTP API + 静态资源
├── app_info.py            # 版本号 / 更新元数据
├── packaging/ArkPlots.spec # PyInstaller（console=False）
├── packaging/build_release.py
├── web/                   # Vite + React + TypeScript
│   ├── src/i18n/          # 界面与内容国际化
│   └── dist/              # 构建输出
├── README.md              # 本说明（中文）
└── README.en.md           # English README
```

API 概要：

- `GET /api/plots` — 剧情数据
- `GET /api/records` / `PUT /api/records` — 阅读记录
- `GET /api/version` — 版本与更新元数据
- `GET /api/health` — 健康检查
