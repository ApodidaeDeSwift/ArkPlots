# ArkPlots

**明日方舟剧情线梳理工具**

[English](README.en.md) | 简体中文

在本地记录、筛选与跟踪《明日方舟》剧情条目（主线、别传、故事集、集成战略等），管理阅读进度，并根据前置关系推荐「该补什么 / 能接着读什么」。

喜欢的话，欢迎在右上角点一颗 ⭐。

---

## 功能概览

- **Web 情报站界面**：三栏布局（筛选列表 / 详情预览 / 阅读推荐）
- **多维筛选**：日期范围、剧情类型、国家/地区、同期干员（子串）、阶段、相关势力、相关剧情标签；部分条件支持「含任意一个 / 全部包含」
- **阅读状态**：未读 / 计划读 / 正在读 / 已读；支持单条与批量设置，保存在 `Read_record.json`
- **详情与前置**：必要 / 可选前置剧情、跳转、预览历史前进 / 后退
- **智能推荐**：急需补充、推荐补充、推荐继续、可以继续
- **关联视频**：打开链接或复制到剪贴板
- **多语言**：界面与展示名支持简体中文 / English（右上角切换）

---

## 关于不同服务器的内容

所有相关日期目前都以大陆服为准，推荐视频也以bilibili为准。如有外国网友愿意补充其他服务器相关信息，欢迎联系

---

## 环境要求

| 用途 | 依赖 |
| --- | --- |
| 运行 Web UI | Python 3.10+（标准库即可，无需额外 pip 包） |
| 首次构建前端 | [Node.js](https://nodejs.org/) 18+（含 npm） |
| 可选：旧版桌面 UI | tkinter（多数 Python 安装已自带） |

数据文件需与程序放在同一目录：

- `Plotline.json` — 剧情条目（仓库已附带）
- `Read_record.json` — 阅读记录（不存在时会自动创建）

---

## 快速开始（推荐）

### 1. 构建前端（首次，或 `web/` 有改动后）

```bash
cd web
npm install
npm run build
cd ..
```

构建产物在 `web/dist/`。若缺失，启动服务时会提示先执行上述命令。

### 2. 启动

```bash
python main.py
```

默认打开浏览器访问：`http://127.0.0.1:8765/`  
若 `8765` 已被占用，程序会自动尝试后续空闲端口。

### 3. 常用参数

```bash
python main.py --port 8765     # 指定端口
python main.py --no-browser    # 不自动打开浏览器
python main.py --tk            # 使用旧版 tkinter 界面
```

也可直接运行服务端：

```bash
python server.py --port 8765 --no-browser
```

### 打包版

若使用仓库中的可执行文件：

```bash
./Arkplot_ver1.0.3.exe
```

请确保同目录下有 `Plotline.json`，以及已构建的 `web/dist`（或按程序提示操作）。

---

## 开发联调

前后端分开跑，前端热更新：

```bash
# 终端 1：API（默认 8765）
python server.py --no-browser

# 终端 2：Vite 开发服务器（已代理 /api → 8765）
cd web
npm run dev
```

---

## 数据说明

### Plotline.json

按发布顺序记录剧情条目，常见字段如下：

| 字段 | 说明 |
| --- | --- |
| `id` | 唯一标识 |
| `name` | 剧情名称（中文，展示层可按语言映射） |
| `date` | 发布日期（`YYYY-MM-DD`） |
| `class` | 类型代码：`main` / `sidestory` / `interlude` / `ministory` / `manga` / `anime` / `rougelike` / `RA` / `other` |
| `country` | 相关国家 / 地区 |
| `new_operator` | 同期干员 |
| `plot_stage` | 剧情阶段 |
| `related_power` | 相关势力 |
| `related_plot` | 相关标签（如源石、巨兽等） |
| `description` | 描述 |
| `necessary_plot` | 必要前置（可含 `id`、`reason`，可选 `reason_en`） |
| `optional_plot` | 可选前置 |
| `Videos` | 关联视频 |

### Read_record.json

键为剧情 `id`（字符串），值为阅读状态：`未读` | `计划读` | `正在读` | `已读`。  
**注意**：状态值在数据层固定为中文，切换界面语言只会改变显示文案，不会改写文件内容。

---

## 多语言（i18n）

- 默认语言：`zh-CN`；另有 `en-US`
- 语言偏好保存在浏览器 `localStorage`（键名 `arkplots.locale`）
- 界面文案：`web/src/i18n/locales/`
- 内容对照（剧情名、国家、势力、干员、相关标签）：`web/src/i18n/content/`
- **所有翻译内容均由Cursor查询萌娘百科完成，翻译目前可能不准确**，如发现翻译错误可以上报issue或直接提pr

### 添加新语言

1. 在 `web/src/i18n/locales/` 新增语言包（形状与 `zh-CN.ts` 相同）
2. 在 `locales/index.ts` 的 `localeRegistry` 中注册
3. （可选）在 `web/src/i18n/content/` 增加对应内容映射
4. 重新 `npm run build`

语言切换器会自动列出已注册语言。

---

## 项目结构

```
ArkPlots/
├── Plotline.json          # 剧情数据
├── Read_record.json       # 阅读记录
├── main.py                # 启动器（Web 默认；--tk 旧界面）
├── server.py              # 本地 HTTP API + 静态资源
├── web/                   # Vite + React + TypeScript 前端
│   ├── src/i18n/          # 界面与内容国际化
│   └── dist/              # 构建输出（需 npm run build）
├── README.md              # 本说明（中文）
└── README.en.md           # English README
```

API 概要：

- `GET /api/plots` — 剧情数据
- `GET /api/records` / `PUT /api/records` — 阅读记录

---

## 作者与联系

- GitHub：[@ApodidaeDeSwift](https://github.com/ApodidaeDeSwift)
- 微信：`Quantumaster233`
- QQ：`3195582616`
- B站：[space.bilibili.com/281039105](https://space.bilibili.com/281039105)

---

## 支持我们

如果本工具对你有帮助，请作者喝一杯蜜雪冰城：

![支持我们](coffee.png)

感谢支持！

---

## 许可与声明

本项目为个人学习与整理工具。《明日方舟》及相关文本、设定归上海鹰角网络科技有限公司等权利方所有。本仓库数据与界面仅供学习、交流，请勿用于商业用途。欢迎在 GitHub 提 Issue / PR。
