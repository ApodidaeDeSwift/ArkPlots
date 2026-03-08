# ArkPlots
# 明日方舟剧情线梳理

## 基本介绍
在该程序内记录并检索《明日方舟》剧情线条目（主线、活动、外传等），提供图形界面筛选、预览与阅读状态管理，方便玩家或研究者快速定位与跟踪剧情信息，查看自己可以接着查看的剧情，和需要补充的剧情。

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
- 以表格式 GUI 列出剧情条目，条目占两行或多行显示，包含：阅读状态、ID、名称、类型、发布日期、阶段、国家、相关势力、相关剧情、同期角色等。
- 支持多维度筛选：日期范围、剧情类型、国家、同期角色（子串搜索）、阶段、相关势力、相关剧情；部分筛选支持“含任意一个 / 全部包含”模式。
- 交互筛选器为弹窗多选（支持全选/全不选/反选），日期选择为年/月/日下拉。
- 列表支持多选（Ctrl/Shift）、高亮与批量设置阅读状态。
- 右侧预览区显示剧情详情，提供前置剧情（必要/可选）预览，前置项显示其阅读状态并可双击跳转。
- 支持将每个剧情关联的视频信息（`Videos` 字段），可以打开或复制视频链接。
- 将用户的阅读状态保存在 `Read_record.json` 中（默认：未读）。

## 使用说明
1. 把 `Plotline.json` 和 `Read_record.json` 放在程序同目录（程序会自动创建或初始化 `Read_record.json`）。
2. 运行：

```bash
python main.py
```

3. 在程序左侧使用筛选控件选择条件，点击“过滤”应用筛选；选中列表项在右侧查看详情；使用“设置阅读状态”或“批量设置”管理阅读记录；点击“相关视频”打开视频列表并操作链接。
# 运行说明（EXE/源码）

- 如果你使用打包的可执行文件（推荐）：

```bash
# 在可执行文件所在目录双击运行，或在命令行运行：
./Arkplot_ver1.0.2.exe
```

- 如果你想运行源码（用于调试或修改）：

```bash
python main.py
```

注意：仓库中的 `main.py` 为源码参考；若已分发 `Arkplot_ver1.0.2.exe`，可直接使用 EXE 运行而无需安装 Python。

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
- 源码：`main.py`（基于 Python + tkinter，纯标准库实现）
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