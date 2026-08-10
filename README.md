# ArkPlots
# 明日方舟剧情线梳理

## 基本介绍
在该程序内记录并检索《明日方舟》剧情线条目（主线、活动、外传等），提供图形界面筛选、预览与阅读状态管理，方便玩家或研究者快速定位与跟踪剧情信息，查看自己可以接着查看的剧情，和需要补充的剧情。
如果喜欢的话，就请在右上角（↗）给个⭐吧！

## 已经记录的信息
    在$Plotline.json$里按照发布的顺序记录了所有的相关大剧情的以下信息：
    1. "name"剧情名称
    2. "date"剧情的发布日期
    3. "class"剧情类型
    4. "country"剧情相关国家
    5. "new_operator"剧情同时期推出角色
    6. "plot_stage"剧情所在阶段
    7. "related_power"剧情相关势力
    8."related_plot"剧情相关其他信息
    9. "description"剧情描述
    10. "necessary_plot"剧情前置必要项
    11. "optional_plot"剧情前置可选项
    12. "Videos"剧情关联视频信息

## 功能概览
- 轻量 Web 情报站界面：三栏布局（筛选列表 / 详情 / 推荐）。
- 支持多维度筛选：日期范围、剧情类型、国家、同期角色（子串搜索）、阶段、相关势力、相关剧情；部分筛选支持“含任意一个 / 全部包含”模式。
- 列表支持多选、高亮与批量设置阅读状态。
- 详情区显示剧情信息与前置剧情（必要/可选），可跳转并支持预览历史前进/后退。
- 推荐栏：急需补充 / 推荐补充 / 推荐继续 / 可以继续。
- 关联视频可打开或复制链接。
- 阅读状态保存在 `Read_record.json`（默认：未读）。
- Web UI 文案已接入可扩展 i18n（默认 `zh-CN`，另含 `en-US`）。右上角可切换语言。英文内容对照在 `web/src/i18n/content/`（剧情名、国家/地区、势力、干员、相关剧情标签）。阅读状态与数据层字段仍用稳定键存储，仅展示可翻译。

## 使用说明（推荐：Web UI）

1. 把 `Plotline.json` 和 `Read_record.json` 放在程序同目录（程序会自动创建或初始化 `Read_record.json`）。
2. **首次或前端有改动时**，构建 Web 界面（需要本机安装 Node.js）：

```bash
cd web
npm install
npm run build
cd ..
```

3. 启动本地服务（会自动打开浏览器）：

```bash
python main.py
```

默认地址：`http://127.0.0.1:8765/`

可选参数：

```bash
python main.py --port 8765          # 指定端口
python main.py --no-browser         # 不自动打开浏览器
python main.py --tk                 # 回退到旧版 tkinter 界面
```

开发联调（可选）：

```bash
# 终端 1：API
python server.py --no-browser

# 终端 2：Vite 热更新（已代理 /api -> 8765）
cd web
npm run dev
```

## 运行说明（EXE/源码）

- 如果你使用打包的可执行文件：

```bash
./Arkplot_ver1.0.2.exe
```

- 源码运行（Web UI）：

```bash
python main.py
```

注意：Web UI 需要先有 `web/dist`（由 `npm run build` 生成）。若缺失，服务会提示构建命令。

## 数据字段说明（Plotline.json 中每条目常见字段）
- `id`: 唯一标识
- `name`: 剧情名称
- `date`: 发布日期（YYYY-MM-DD）
- `class`: 类型（如 main/sidestory/...）
- `country`: 相关国家
- `new_operator`: 同期角色
- `plot_stage`: 重要阶段
- `related_power`: 相关势力
- `related_plot`: 相关剧情
- `description`: 文本描述
- `necessary_plot`: 前置必要剧情
- `optional_plot`: 前置可选剧情
- `Videos`: 关联的视频信息

## 开发与作者
- Web UI：`web/`（Vite + React + TypeScript）
- 本地服务：`server.py`（Python 标准库）
- 启动器 / 旧版 tkinter：`main.py`（`--tk`）
- 作者 / GitHub：ApodidaeDeSwift

```
GitHub: https://github.com/ApodidaeDeSwift
微信: Quantumaster233
QQ: 3195582616
B站: https://space.bilibili.com/281039105
```

## 支持我们
如果你愿意支持项目维护，请作者喝一杯蜜雪冰城，可通过收款码打赏。仓库中已包含支付二维码图片：

 - 支付二维码：

     ![支持我们](coffee.png)

感谢你的支持！

## 许可与说明
- 本项目为个人工具，数据来源归原作者所有；仅用于学习、整理、交流用途。欢迎在 GitHub 上展开协作或提交问题。
