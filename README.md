# ArkPlots

**明日方舟剧情线梳理工具**（本地 Web 版）

[English](README.en.md) | 简体中文

在本地记录、筛选与跟踪《明日方舟》剧情条目（主线、别传、故事集、集成战略等），管理阅读进度，并根据前置关系推荐「该补什么 / 能接着读什么」。

喜欢的话，欢迎在右上角点一颗 ⭐。

---

# 普通玩家只需要看这里

## 怎么用

### 方式一：打包版（最省事）

若仓库中有 `Arkplot_ver*.exe`（当前例如 `Arkplot_ver1.0.4.exe`）：

1. 把 exe 与同目录的 `Plotline.json` 放在一起（阅读记录文件不需要事先准备）
2. 双击 exe
3. 浏览器会自动打开本地页面（一般为 `http://127.0.0.1:8765/`）

> 打包版已内嵌界面；同目录只需保证有 `Plotline.json`。`Read_record.json` 首次运行会自动生成。

### 方式二：源码最简启动

若你已装好 Python，且仓库里已有构建好的 `web/dist`：

```bash
python main.py
```

默认打开浏览器访问：**http://127.0.0.1:8765/**  
若 `8765` 被占用，程序会自动换下一个空闲端口（看终端提示）。

同目录需要：

| 文件 | 说明 |
| --- | --- |
| `Plotline.json` | 剧情数据（仓库已附带） |
| `Read_record.json` | 阅读记录（不存在时自动创建） |

## 功能速览

- 三栏界面：筛选列表 / 详情预览 / 阅读推荐
- 按日期、类型、国家、干员、阶段、势力等筛选；管理未读 / 计划读 / 正在读 / 已读
- 查看必要 / 可选前置，并给出补读与续读推荐
- 关联视频可打开或复制链接
- 右上角可切换 **简体中文 / English**

## 联系 / 支持 / 声明

- GitHub：[@ApodidaeDeSwift](https://github.com/ApodidaeDeSwift)
- 微信：`Quantumaster233` · QQ：`3195582616`
- B站：[space.bilibili.com/281039105](https://space.bilibili.com/281039105)

如果本工具对你有帮助，请作者喝一杯蜜雪冰城：

![支持我们](coffee.png)

本项目为个人学习与整理工具。《明日方舟》及相关文本、设定归上海鹰角网络科技有限公司等权利方所有。本仓库数据与界面仅供学习、交流，请勿用于商业用途。

---

# 想做修改或高级启动的玩家请看这里

## 环境

| 用途 | 依赖 |
| --- | --- |
| 运行 Web UI | Python 3.10+（标准库即可，无需额外 pip 包） |
| 构建 / 改前端 | [Node.js](https://nodejs.org/) 18+（含 npm） |
| 可选：旧版桌面 UI | tkinter（多数 Python 安装已自带） |

## 构建前端与启动

首次，或 `web/` 有改动后：

```bash
cd web
npm install
npm run build
cd ..
python main.py
```

构建产物在 `web/dist/`。若缺失，启动时会提示先执行上述命令。

### 常用参数

```bash
python main.py --port 8765     # 指定端口（默认 8765）
python main.py --no-browser    # 不自动打开浏览器
python main.py --tk            # 使用旧版 tkinter 界面
```

也可直接跑服务端：

```bash
python server.py --port 8765 --no-browser
```

`server.py` 负责本地 HTTP：静态资源来自 `web/dist`，并提供：

- `GET /api/plots` — 剧情数据
- `GET /api/records` / `PUT /api/records` — 阅读记录
- `GET /api/health` — 健康检查

## 开发联调

前后端分开跑，前端热更新：

```bash
# 终端 1：API（默认 8765）
python server.py --no-browser

# 终端 2：Vite（已代理 /api → 8765）
cd web
npm run dev
```

## 关于不同服务器

日期目前以**大陆服**为准，推荐视频以 **bilibili** 为主。若有外国玩家愿意补充其他服务器信息，欢迎联系。

## 数据说明

### Plotline.json

按发布顺序记录剧情条目，常见字段：

| 字段 | 说明 |
| --- | --- |
| `id` | 唯一标识 |
| `name` | 剧情名称（中文，展示层可按语言映射） |
| `date` | 发布日期（`YYYY-MM-DD`） |
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

### Read_record.json

键为剧情 `id`（字符串），值为：`未读` | `计划读` | `正在读` | `已读`。  
状态值在数据层固定为中文；切换界面语言只改显示文案，不改写文件。

## 多语言（i18n）

- 默认 `zh-CN`，另有 `en-US`；偏好保存在浏览器 `localStorage`（键名 `arkplots.locale`）
- 界面文案：`web/src/i18n/locales/`；内容对照：`web/src/i18n/content/`
- **翻译多由 Cursor 对照萌娘百科整理，可能不准确**；发现问题可提 Issue / PR

### 添加新语言

1. 在 `web/src/i18n/locales/` 新增语言包（形状与 `zh-CN.ts` 相同）
2. 在 `locales/index.ts` 的 `localeRegistry` 中注册
3. （可选）在 `web/src/i18n/content/` 增加内容映射
4. 重新 `npm run build`

## 项目结构

```
ArkPlots/
├── Plotline.json          # 剧情数据
├── Read_record.json       # 阅读记录
├── main.py                # 启动器（默认 Web；--tk 旧界面）
├── server.py              # 本地 HTTP API + 静态资源
├── web/                   # Vite + React + TypeScript 前端
│   ├── src/i18n/          # 界面与内容国际化
│   └── dist/              # 构建输出（npm run build）
├── README.md              # 本说明（中文）
└── README.en.md           # English README
```
