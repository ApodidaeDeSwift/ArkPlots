#!/usr/bin/env python3
"""
ArkPlots - 简易命令行剧情检索器

功能（基于 README）:
- 从 Plotline.json 加载剧情条目
- 支持按日期范围、类型(`class`)、国家、同期角色(`new_operator`)、阶段(`plot_stage`)、相关势力、相关剧情过滤
- 支持选择要在列表中显示的字段
- 保存/读取用户在 Read_record.json 中的阅读状态

用法：运行后按菜单交互过滤、查看或标记阅读状态。
"""
from __future__ import annotations
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

WORKDIR = os.path.dirname(os.path.abspath(__file__))
PLOTLINE_PATH = os.path.join(WORKDIR, "Plotline.json")
READ_RECORD_PATH = os.path.join(WORKDIR, "Read_record.json")


def load_json(path: str) -> Any:
    try:
        if not os.path.exists(path):
            return None
        # handle empty file or invalid JSON gracefully
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            if not content.strip():
                return None
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return None
    except Exception:
        return None


def save_json(path: str, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def parse_date(s: str) -> Optional[datetime]:
    s = s.strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y-%m"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            continue
    print(f"无法识别的日期格式: {s}，请使用 YYYY-MM-DD 等格式")
    return None


def normalize_list_field(v):
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x) for x in v if x is not None]
    return [str(v)]


def matches_filters(item: Dict[str, Any], filters: Dict[str, Any]) -> bool:
    # date range
    date_s = item.get("date", "").strip()
    item_date = None
    if date_s:
        try:
            item_date = datetime.strptime(date_s[:10], "%Y-%m-%d")
        except Exception:
            item_date = None

    start: Optional[datetime] = filters.get("start")
    end: Optional[datetime] = filters.get("end")
    if start and item_date and item_date < start:
        return False
    if end and item_date and item_date > end:
        return False

    # class types
    types = filters.get("class")
    if types:
        if item.get("class") not in types:
            return False

    # country
    countries = filters.get("country")
    country_mode = filters.get("country_mode", "any")
    if countries:
        item_c = normalize_list_field(item.get("country"))
        if country_mode == "any":
            if not any(c in item_c for c in countries):
                return False
        else:  # all
            if not all(c in item_c for c in countries):
                return False

    # new_operator (search substring)
    op_search = filters.get("new_operator")
    if op_search:
        ops = normalize_list_field(item.get("new_operator"))
        found = any(op_search.lower() in o.lower() for o in ops)
        if not found:
            return False

    # plot_stage
    stages = filters.get("plot_stage")
    if stages:
        try:
            if int(item.get("plot_stage", -999)) not in stages:
                return False
        except Exception:
            return False

    # related_power
    powers = filters.get("related_power")
    power_mode = filters.get("power_mode", "any")
    if powers:
        item_p = normalize_list_field(item.get("related_power"))
        if power_mode == "any":
            if not any(p in item_p for p in powers):
                return False
        else:
            if not all(p in item_p for p in powers):
                return False

    # related_plot
    rplots = filters.get("related_plot")
    rplot_mode = filters.get("rplot_mode", "any")
    if rplots:
        item_r = normalize_list_field(item.get("related_plot"))
        if rplot_mode == "any":
            if not any(r in item_r for r in rplots):
                return False
        else:
            if not all(r in item_r for r in rplots):
                return False

    return True


def input_filters() -> Dict[str, Any]:
    print("输入过滤条件（留空跳过）")
    s = input("开始日期 (YYYY-MM-DD)：").strip()
    start = parse_date(s) if s else None
    s = input("结束日期 (YYYY-MM-DD)：").strip()
    end = parse_date(s) if s else None
    cls = input("剧情类型，逗号分隔（如 main,sidestory,ministory）：").strip()
    classes = [c.strip() for c in cls.split(",") if c.strip()] if cls else []
    country = input("国家，逗号分隔：").strip()
    countries = [c.strip() for c in country.split(",") if c.strip()] if country else []
    nops = input("同时期推出角色（子串搜索）：").strip()
    stage = input("剧情阶段（可多项，逗号分隔）：").strip()
    stages = [int(x) for x in stage.split(",") if x.strip()] if stage else []
    rp = input("相关势力，逗号分隔：").strip()
    rps = [x.strip() for x in rp.split(",") if x.strip()] if rp else []
    rpl = input("相关其他信息，逗号分隔：").strip()
    rpls = [x.strip() for x in rpl.split(",") if x.strip()] if rpl else []

    return {"start": start, "end": end, "class": classes or None, "country": countries or None,
            "new_operator": nops or None, "plot_stage": stages or None,
            "related_power": rps or None, "related_plot": rpls or None}


def select_display_fields() -> Dict[str, bool]:
    defaults = {
        "country": True,
        "plot_stage": True,
        "new_operator": True,
        "related_power": True,
        "related_plot": True,
        "description": True,
    }
    print("选择要在列表中显示的字段（y/N）")
    for k in list(defaults.keys()):
        ans = input(f"显示 {k} ? (y/N) ").strip().lower()
        defaults[k] = ans == "y"
    return defaults


def format_item_for_list(item: Dict[str, Any], fields: Dict[str, bool], read_status: Optional[str]) -> str:
    parts = [f"[{item.get('id')}] {item.get('name')}"]
    if fields.get("country"):
        parts.append("国家:" + ",".join(normalize_list_field(item.get("country"))))
    if fields.get("plot_stage"):
        parts.append("阶段:" + str(item.get("plot_stage", "")))
    if fields.get("new_operator"):
        parts.append("同期角色:" + ",".join(normalize_list_field(item.get("new_operator"))))
    if fields.get("related_power"):
        parts.append("相关势力:" + ",".join(normalize_list_field(item.get("related_power"))))
    if fields.get("related_plot"):
        parts.append("相关剧情:" + ",".join(normalize_list_field(item.get("related_plot"))))
    if fields.get("description"):
        parts.append("描述:" + (item.get("description") or ""))
    if read_status:
        parts.append(f"阅读状态:{read_status}")
    return " | ".join(parts)


def ensure_read_record(plots: List[Dict[str, Any]]) -> Dict[str, str]:
    data = load_json(READ_RECORD_PATH)
    if not data:
        data = {}
    # ensure keys for existing plots
    for p in plots:
        pid = str(p.get("id"))
        if pid not in data:
            data[pid] = "未读"
    save_json(READ_RECORD_PATH, data)
    return data


def set_read_status(records: Dict[str, str], plots_map: Dict[str, Dict[str, Any]]) -> None:
    pid = input("输入要设置状态的剧情 ID：").strip()
    if pid not in plots_map:
        print("未找到该 ID")
        return
    print("可选状态：未读、计划读、正在读、已读")
    st = input("输入状态：").strip()
    if not st:
        print("未修改")
        return
    records[pid] = st
    save_json(READ_RECORD_PATH, records)
    print("已保存")


def view_details(item: Dict[str, Any], read_status: Optional[str]) -> None:
    print("-" * 60)
    print(f"ID: {item.get('id')}")
    print(f"名称: {item.get('name')}")
    print(f"类型: {item.get('class')}")
    print(f"发布日期: {item.get('date')}")
    print(f"国家: {', '.join(normalize_list_field(item.get('country')))}")
    print(f"阶段: {item.get('plot_stage')}")
    print(f"同期角色: {', '.join(normalize_list_field(item.get('new_operator')))}")
    print(f"相关势力: {', '.join(normalize_list_field(item.get('related_power')))}")
    print(f"相关剧情: {', '.join(normalize_list_field(item.get('related_plot')))}")
    print(f"描述: {item.get('description')}")
    if read_status:
        print(f"阅读状态: {read_status}")
    print("-" * 60)


def gui_main():
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox, simpledialog
        import tkinter.font as tkfont
    except Exception:
        print("无法加载 tkinter，请确保 Python 安装包含 tkinter。")
        sys.exit(1)

    plotdata = load_json(PLOTLINE_PATH)
    if not plotdata:
        message = f"未找到或无法解析 Plotline.json，请确保文件存在于 {PLOTLINE_PATH}"
        tk.Tk().withdraw()
        messagebox.showerror("错误", message)
        sys.exit(1)
    plots = plotdata.get("data") or []
    records = ensure_read_record(plots)
    plots_map = {str(p.get("id")): p for p in plots if p.get("id") is not None}

    root = tk.Tk()
    root.title("ArkPlots - 剧情检索器")
    root.geometry("960x640")

    # top toolbar
    toolbar = ttk.Frame(root, relief=tk.RAISED)
    toolbar.pack(side=tk.TOP, fill=tk.X)

    # basic styling / font
    try:
        style = ttk.Style(root)
        style.theme_use('clam')
    except Exception:
        style = None
    try:
        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(size=10, family="Segoe UI")
    except Exception:
        pass
    # list and text font (use 微软雅黑 / Microsoft YaHei when available)
    try:
        yahei_font = tkfont.Font(family="Microsoft YaHei", size=12)
    except Exception:
        yahei_font = tkfont.Font(size=12)

    # Frames
    left = ttk.Frame(root)
    left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    right = ttk.Frame(root)
    right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    # prepare filter options from data
    classes_set = sorted({str(p.get("class")) for p in plots if p.get("class")})
    # map class keys to display labels
    class_label_map = {
        'main': '主线',
        'sidestory': '别传',
        'interlude': '插曲',
        'ministory': '故事集',
        'manga': '漫画',
        'anime': '动画',
        'rougelike': '集成战略',
        'RA': '生息演算',
        'other': '其他'
    }
    countries_set = sorted({c for p in plots for c in normalize_list_field(p.get("country"))})
    stages_set = sorted({str(p.get("plot_stage")) for p in plots if p.get("plot_stage") is not None})
    # map stage numbers to descriptive labels
    stage_label_map = {
        '1': '1（长夜临光和主线第八章前）',
        '2': '2（孤星前）',
        '3': '3（主线14章前）',
        '4': '4（主线14章后）'
    }
    # build stage option labels preserving order of stages_set
    stage_options = [stage_label_map.get(s, s) for s in stages_set]
    powers_set = sorted({pw for p in plots for pw in normalize_list_field(p.get("related_power"))})
    rplots_set = sorted({rp for p in plots for rp in normalize_list_field(p.get("related_plot"))})

    # derive year/month/day options from available dates
    years = set()
    months = set()
    days = set()
    for p in plots:
        d = p.get("date") or ""
        try:
            dt = datetime.strptime(d[:10], "%Y-%m-%d")
            years.add(str(dt.year))
            months.add(str(dt.month).zfill(2))
            days.add(str(dt.day).zfill(2))
        except Exception:
            continue
    years = sorted(years)
    months = [str(i).zfill(2) for i in range(1, 13)] if not months else sorted(months)
    days = [str(i).zfill(2) for i in range(1, 32)] if not days else sorted(days)

    # Filter area (checkbox/list selection style)
    filter_frame = ttk.Frame(left)
    filter_frame.pack(fill=tk.X, padx=5, pady=5)
    # date pickers
    ttk.Label(filter_frame, text="开始日期").grid(row=0, column=0)
    start_year = ttk.Combobox(filter_frame, values=years, width=6)
    start_year.grid(row=0, column=1)
    start_month = ttk.Combobox(filter_frame, values=months, width=4)
    start_month.grid(row=0, column=2)
    start_day = ttk.Combobox(filter_frame, values=days, width=4)
    start_day.grid(row=0, column=3)
    ttk.Label(filter_frame, text="结束日期").grid(row=0, column=4)
    end_year = ttk.Combobox(filter_frame, values=years, width=6)
    end_year.grid(row=0, column=5)
    end_month = ttk.Combobox(filter_frame, values=months, width=4)
    end_month.grid(row=0, column=6)
    end_day = ttk.Combobox(filter_frame, values=days, width=4)
    end_day.grid(row=0, column=7)

    # multi-select lists for other filters
    # helper: create a popup multi-select dialog
    def multi_select_dialog(title: str, options: List[str], initial: Optional[List[str]] = None,
                            show_mode: bool = False, initial_mode: str = "any") -> Dict[str, Any]:
        """弹窗多选（使用复选框），返回 {'values': [...], 'mode': 'any'|'all'}"""
        dlg = tk.Toplevel(root)
        dlg.title(title)
        dlg.transient(root)
        dlg.grab_set()

        # scrollable frame for many checkboxes
        container = ttk.Frame(dlg)
        container.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=canvas.yview)
        scrollable = ttk.Frame(canvas)

        scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set, height=240)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        vars_list: List[tk.BooleanVar] = []
        # populate checkbuttons
        for opt in options:
            var = tk.BooleanVar(value=(opt in (initial or [])))
            cb = ttk.Checkbutton(scrollable, text=opt, variable=var)
            cb.pack(anchor='w', padx=4, pady=2)
            vars_list.append((opt, var))

        # control buttons
        ctrl = ttk.Frame(dlg)
        ctrl.pack(fill=tk.X, pady=4)

        def select_all():
            for _, v in vars_list:
                v.set(True)

        def select_none():
            for _, v in vars_list:
                v.set(False)

        def invert():
            for _, v in vars_list:
                v.set(not v.get())

        ttk.Button(ctrl, text="全选", command=select_all).pack(side=tk.LEFT, padx=4)
        ttk.Button(ctrl, text="全不选", command=select_none).pack(side=tk.LEFT, padx=4)
        ttk.Button(ctrl, text="反选", command=invert).pack(side=tk.LEFT, padx=4)

        mode_var = tk.StringVar(value=initial_mode)
        if show_mode:
            mode_frame = ttk.Frame(dlg)
            mode_frame.pack(fill=tk.X, padx=6)
            ttk.Label(mode_frame, text="匹配方式：").pack(side=tk.LEFT)
            ttk.Radiobutton(mode_frame, text="含任意一个", variable=mode_var, value="any").pack(side=tk.LEFT, padx=6)
            ttk.Radiobutton(mode_frame, text="全部包含", variable=mode_var, value="all").pack(side=tk.LEFT, padx=6)

        res = {"done": False, "values": [], "mode": mode_var.get()}

        def on_ok():
            res["values"] = [opt for opt, v in vars_list if v.get()]
            res["mode"] = mode_var.get()
            res["done"] = True
            dlg.destroy()

        def on_cancel():
            dlg.destroy()

        btnf = ttk.Frame(dlg)
        btnf.pack(fill=tk.X, pady=6)
        ttk.Button(btnf, text="确定", command=on_ok).pack(side=tk.LEFT, padx=6)
        ttk.Button(btnf, text="取消", command=on_cancel).pack(side=tk.LEFT, padx=6)

        root.wait_window(dlg)
        return res

    # store selected lists here (initially empty => no filter)
    class_selected: List[str] = []
    country_selected: List[str] = []
    stage_selected: List[str] = []
    power_selected: List[str] = []
    rplot_selected: List[str] = []
    # match modes for country/power/rplot: 'any' (default) or 'all'
    country_mode = "any"
    power_mode = "any"
    rplot_mode = "any"

    # review fields control which fields shown in details (name always True and not changeable)
    review_fields = {
        'name': True,
        'type': True,
        'date': True,
        'country': True,
        'plot_stage': True,
        'new_operator': True,
        'related_power': True,
        'related_plot': True,
        'description': True,
    }

    def open_selector(kind: str):
        nonlocal class_selected, country_selected, stage_selected, power_selected, rplot_selected
        nonlocal country_mode, power_mode, rplot_mode
        if kind == "class":
            # show labels in dialog, map back to keys
            class_options = [class_label_map.get(c, c) for c in classes_set]
            initial_labels = [class_label_map.get(v, v) for v in class_selected]
            res = multi_select_dialog("选择类型", class_options, initial_labels)
            sel_labels = res.get("values", [])
            label_to_key = {label: key for key, label in class_label_map.items()}
            class_selected = [label_to_key.get(l, l) for l in sel_labels]
            class_btn.config(text=f"类型 ({len(class_selected)})")
        elif kind == "country":
            res = multi_select_dialog("选择国家", countries_set, country_selected, show_mode=True, initial_mode=country_mode)
            country_selected = res.get("values", [])
            country_mode = res.get("mode", country_mode)
            country_btn.config(text=f"国家 ({len(country_selected)})")
        elif kind == "stage":
            # show descriptive labels in dialog, map back to values
            # initial labels
            initial_labels = [stage_label_map.get(v, v) for v in stage_selected]
            res = multi_select_dialog("选择阶段", stage_options, initial_labels)
            sel_labels = res.get("values", [])
            # reverse map labels to values
            label_to_value = {label: val for val, label in stage_label_map.items()}
            stage_selected = [label_to_value.get(l, l) for l in sel_labels]
            stage_btn.config(text=f"阶段 ({len(stage_selected)})")
        elif kind == "power":
            res = multi_select_dialog("选择相关势力", powers_set, power_selected, show_mode=True, initial_mode=power_mode)
            power_selected = res.get("values", [])
            power_mode = res.get("mode", power_mode)
            power_btn.config(text=f"相关势力 ({len(power_selected)})")
        elif kind == "rplot":
            res = multi_select_dialog("选择相关剧情", rplots_set, rplot_selected, show_mode=True, initial_mode=rplot_mode)
            rplot_selected = res.get("values", [])
            rplot_mode = res.get("mode", rplot_mode)
            rplot_btn.config(text=f"相关剧情 ({len(rplot_selected)})")

    ttk.Label(filter_frame, text="类型").grid(row=1, column=0)
    class_btn = ttk.Button(filter_frame, text="类型 (0)", command=lambda: open_selector("class"))
    class_btn.grid(row=2, column=0, sticky=tk.W+tk.E)

    ttk.Label(filter_frame, text="国家").grid(row=1, column=1)
    country_btn = ttk.Button(filter_frame, text="国家 (0)", command=lambda: open_selector("country"))
    country_btn.grid(row=2, column=1, sticky=tk.W+tk.E)

    ttk.Label(filter_frame, text="阶段").grid(row=1, column=2)
    stage_btn = ttk.Button(filter_frame, text="阶段 (0)", command=lambda: open_selector("stage"))
    stage_btn.grid(row=2, column=2, sticky=tk.W+tk.E)

    ttk.Label(filter_frame, text="相关势力").grid(row=3, column=0)
    power_btn = ttk.Button(filter_frame, text="相关势力 (0)", command=lambda: open_selector("power"))
    power_btn.grid(row=4, column=0, columnspan=2, sticky=tk.W+tk.E)

    ttk.Label(filter_frame, text="相关剧情").grid(row=3, column=2)
    rplot_btn = ttk.Button(filter_frame, text="相关剧情 (0)", command=lambda: open_selector("rplot"))
    rplot_btn.grid(row=4, column=2, columnspan=3, sticky=tk.W+tk.E)

    # Items view (改为表格式两行条目，支持多选、高亮、滚动)
    list_frame = ttk.Frame(left)
    list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # 使用 Canvas + 内部 Frame 来实现可滚动的条目列表
    canvas = tk.Canvas(list_frame, borderwidth=0)
    vsb = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=canvas.yview)
    canvas.configure(yscrollcommand=vsb.set)
    vsb.pack(side=tk.RIGHT, fill=tk.Y)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    items_frame = tk.Frame(canvas)
    canvas.create_window((0, 0), window=items_frame, anchor='nw')

    def _on_frame_config(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    items_frame.bind("<Configure>", _on_frame_config)

    # selection state for multi-select behaviour
    selected_indices = set()
    last_selected_index = None

    def clear_selection():
        nonlocal selected_indices
        selected_indices.clear()
        for child in items_frame.winfo_children():
            try:
                child.configure(bg=items_frame.cget('bg'))
                for lbl in child.winfo_children():
                    lbl.configure(bg=items_frame.cget('bg'))
            except Exception:
                pass

    def highlight_index(idx, on=True):
        children = items_frame.winfo_children()
        if idx < 0 or idx >= len(children):
            return
        w = children[idx]
        bg = '#cfe8ff' if on else items_frame.cget('bg')
        try:
            w.configure(bg=bg)
            for lbl in w.winfo_children():
                lbl.configure(bg=bg)
        except Exception:
            pass

    def select_item(event, idx: int):
        nonlocal last_selected_index
        # modifiers: Control (toggle), Shift (range), otherwise single select
        state = event.state
        ctrl = (state & 0x0004) != 0
        shift = (state & 0x0001) != 0
        if shift and last_selected_index is not None:
            start = min(last_selected_index, idx)
            end = max(last_selected_index, idx)
            # add range
            for i in range(start, end + 1):
                selected_indices.add(i)
                highlight_index(i, True)
        elif ctrl:
            if idx in selected_indices:
                selected_indices.remove(idx)
                highlight_index(idx, False)
            else:
                selected_indices.add(idx)
                highlight_index(idx, True)
            last_selected_index = idx
        else:
            # single select
            clear_selection()
            selected_indices.add(idx)
            highlight_index(idx, True)
            last_selected_index = idx
        on_select()

    # Details area
    details = tk.Text(right, wrap=tk.WORD, font=yahei_font)
    details.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    details.configure(state='disabled')

    def refresh_list(filtered: Optional[List[Dict[str, Any]]] = None):
        # 使用两行条目渲染
        for w in items_frame.winfo_children():
            w.destroy()
        items = filtered if filtered is not None else plots
        for idx, p in enumerate(items):
            pid = p.get("id")
            name = p.get("name")
            status = records.get(str(pid), "未读")
            # line1: 状态, ID, 名称, 类型, 日期, 阶段
            line1_parts = []
            line1_parts.append(f"[{status}]")
            line1_parts.append(f"{name}")
            if review_fields.get('type', True):
                c = p.get('class')
                type_label = class_label_map.get(c, c) if c else ''
                if type_label:
                    line1_parts.append(type_label)
            if review_fields.get('date', True):
                if p.get('date'):
                    line1_parts.append(p.get('date'))
            if review_fields.get('plot_stage', True):
                if p.get('plot_stage') is not None:
                    line1_parts.append(f"阶段:{p.get('plot_stage')}")
            line1 = '  |  '.join(line1_parts)

            # line2: 国家, 势力, 相关剧情, 同期角色 (仅在审阅勾选时显示对应项)
            line2_parts = []
            if review_fields.get('country', True):
                cs = ','.join(normalize_list_field(p.get('country')))
                if cs:
                    line2_parts.append(f"国家:{cs}")
            if review_fields.get('related_power', True):
                ps = ','.join(normalize_list_field(p.get('related_power')))
                if ps:
                    line2_parts.append(f"势力:{ps}")
            if review_fields.get('related_plot', True):
                rps = ','.join(normalize_list_field(p.get('related_plot')))
                if rps:
                    line2_parts.append(f"相关剧情:{rps}")
            if review_fields.get('new_operator', True):
                nos = ','.join(normalize_list_field(p.get('new_operator')))
                if nos:
                    line2_parts.append(f"同期角色:{nos}")
            line2 = '  |  '.join(line2_parts)

            # create item frame
            item_f = tk.Frame(items_frame, bd=1, relief=tk.FLAT, padx=8, pady=6)
            lbl1 = tk.Label(item_f, text=line1, anchor='w', justify='left', font=yahei_font)
            lbl1.pack(fill=tk.X)

            # 每一项单独占一行显示
            extra_font = (yahei_font.actual('family'), max(10, yahei_font.actual('size')-1))
            extra_labels = []
            if line2_parts:
                for part in line2_parts:
                    lbl = tk.Label(item_f, text=part, anchor='w', justify='left', font=extra_font)
                    lbl.pack(fill=tk.X, pady=(2,0))
                    extra_labels.append(lbl)
            else:
                spacer = tk.Label(item_f, text='', font=extra_font)
                spacer.pack(fill=tk.X, pady=(2,0))
                extra_labels.append(spacer)

            # spacing / visual separation
            item_f.pack(fill=tk.X, padx=4, pady=6)

            # bind clicks for selection
            def make_handler(i):
                return lambda e: select_item(e, i)

            item_f.bind('<Button-1>', make_handler(idx))
            lbl1.bind('<Button-1>', make_handler(idx))
            for lbl in extra_labels:
                lbl.bind('<Button-1>', make_handler(idx))

        items_frame._items = items
        # reapply selection highlight if any indices are within range
        for i in list(selected_indices):
            if i < 0 or i >= len(items):
                selected_indices.discard(i)
        for i in selected_indices:
            highlight_index(i, True)

    def apply_filters():
        f = {}
        # build start date
        sy = start_year.get().strip()
        sm = start_month.get().strip()
        sd = start_day.get().strip()
        if sy and sm and sd:
            f["start"] = parse_date(f"{sy}-{sm}-{sd}")
        else:
            f["start"] = None
        ey = end_year.get().strip()
        em = end_month.get().strip()
        ed = end_day.get().strip()
        if ey and em and ed:
            f["end"] = parse_date(f"{ey}-{em}-{ed}")
        else:
            f["end"] = None

        # selections from popup-managed lists
        f["class"] = class_selected or None
        f["country"] = country_selected or None
        f["country_mode"] = country_mode
        f["plot_stage"] = [int(x) for x in stage_selected] if stage_selected else None
        f["related_power"] = power_selected or None
        f["power_mode"] = power_mode
        f["related_plot"] = rplot_selected or None
        f["rplot_mode"] = rplot_mode

        matched = [p for p in plots if matches_filters(p, f)]
        refresh_list(matched)

    def on_select(evt=None):
        # show details of first selected item (if any)
        if not hasattr(items_frame, '_items'):
            return
        items = items_frame._items
        if not selected_indices:
            details.configure(state='normal')
            details.delete(1.0, tk.END)
            details.configure(state='disabled')
            return
        idx = min(selected_indices)
        if idx < 0 or idx >= len(items):
            return
        item = items[idx]
        pid = str(item.get("id"))
        details.configure(state='normal')
        details.delete(1.0, tk.END)
        lines = []
        # build detail lines according to review_fields
        if review_fields.get('name', True):
            lines.append(f"名称: {item.get('name')}")
        if review_fields.get('type', True):
            c = item.get('class')
            lines.append(f"类型: {class_label_map.get(c, c)}")
        # always show ID and date (ID useful)
        lines.insert(0, f"ID: {item.get('id')}")
        lines.append(f"发布日期: {item.get('date')}")
        if review_fields.get('country', True):
            lines.append(f"国家: {', '.join(normalize_list_field(item.get('country')))}")
        if review_fields.get('plot_stage', True):
            lines.append(f"阶段: {item.get('plot_stage')}")
        if review_fields.get('new_operator', True):
            lines.append(f"同期角色: {', '.join(normalize_list_field(item.get('new_operator')))}")
        if review_fields.get('related_power', True):
            lines.append(f"相关势力: {', '.join(normalize_list_field(item.get('related_power')))}")
        if review_fields.get('related_plot', True):
            lines.append(f"相关剧情: {', '.join(normalize_list_field(item.get('related_plot')))}")
        if review_fields.get('description', True):
            lines.append(f"描述: {item.get('description')}")
        lines.append(f"阅读状态: {records.get(pid, '未读')}")
        details.insert(tk.END, "\n".join(lines))
        details.configure(state='disabled')

    def set_status():
        if not hasattr(items_frame, '_items'):
            messagebox.showinfo("提示", "没有可用条目")
            return
        if not selected_indices:
            messagebox.showinfo("提示", "请选择一个剧情条目")
            return
        idx = min(selected_indices)
        items = items_frame._items
        item = items[idx]
        pid = str(item.get('id'))
        # use combobox dialog for fixed choices
        dlg = tk.Toplevel(root)
        dlg.title("设置阅读状态")
        ttk.Label(dlg, text=f"ID: {pid} {item.get('name')}").pack(padx=10, pady=5)
        status_cb = ttk.Combobox(dlg, values=["未读", "计划读", "正在读", "已读"])
        status_cb.pack(padx=10, pady=5)

        def apply_and_close():
            val = status_cb.get().strip()
            if val:
                records[pid] = val
                save_json(READ_RECORD_PATH, records)
                refresh_list()
                on_select()
            dlg.destroy()

        ttk.Button(dlg, text="保存", command=apply_and_close).pack(pady=5)

    def batch_set_status():
        if not hasattr(items_frame, '_items'):
            messagebox.showinfo("提示", "没有可用条目")
            return
        if not selected_indices:
            messagebox.showinfo("提示", "请至少选择一个剧情条目（按住 Ctrl/Shift 多选）")
            return
        pids = [str(items_frame._items[i].get('id')) for i in sorted(selected_indices)]
        dlg = tk.Toplevel(root)
        dlg.title("批量设置阅读状态")
        dlg.transient(root)
        dlg.grab_set()
        ttk.Label(dlg, text=f"选中 {len(pids)} 项，设置为：").pack(padx=10, pady=6)
        status_cb = ttk.Combobox(dlg, values=["未读", "计划读", "正在读", "已读"])
        status_cb.pack(padx=10, pady=5)

        def apply_all():
            val = status_cb.get().strip()
            if not val:
                messagebox.showinfo("提示", "请选择状态")
                return
            for pid in pids:
                records[pid] = val
            save_json(READ_RECORD_PATH, records)
            refresh_list()
            # show details of first selected
            on_select()
            dlg.destroy()

        ttk.Button(dlg, text="保存", command=apply_all).pack(pady=6)

    def open_review_dialog():
        dlg = tk.Toplevel(root)
        dlg.title("审阅 - 选择查看项")
        dlg.transient(root)
        dlg.grab_set()
        vars_map = {}
        # name is always shown and disabled
        f = ttk.Frame(dlg)
        f.pack(fill=tk.X, padx=8, pady=6)
        ttk.Label(f, text="以下选项控制在查看剧情详情时显示哪些信息：").pack(anchor='w')
        # name checkbox (disabled)
        name_var = tk.BooleanVar(value=True)
        cb_name = ttk.Checkbutton(dlg, text="剧情名称（不可取消）", variable=name_var)
        cb_name.state(['disabled'])
        cb_name.pack(anchor='w', padx=12, pady=2)
        # other fields
        for key, label in [('type', '类型'), ('date', '发布日期'), ('country', '国家'), ('plot_stage', '阶段'),
                   ('new_operator', '同期角色'), ('related_power', '相关势力'),
                   ('related_plot', '相关剧情'), ('description', '描述')]:
            var = tk.BooleanVar(value=review_fields.get(key, True))
            vars_map[key] = var
            cb = ttk.Checkbutton(dlg, text=label, variable=var)
            cb.pack(anchor='w', padx=12, pady=2)

        def apply_review():
            for k, v in vars_map.items():
                review_fields[k] = bool(v.get())
            dlg.destroy()

        ttk.Button(dlg, text="确定", command=apply_review).pack(pady=8)

    

    btn_frame = ttk.Frame(right)
    btn_frame.pack(fill=tk.X)
    ttk.Button(btn_frame, text="过滤", command=apply_filters).pack(side=tk.LEFT, padx=5, pady=3)
    ttk.Button(btn_frame, text="刷新全部", command=lambda: refresh_list(plots)).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text="设置阅读状态", command=set_status).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text="批量设置", command=lambda: batch_set_status()).pack(side=tk.LEFT, padx=5)
    ttk.Button(toolbar, text="审阅", command=open_review_dialog).pack(side=tk.LEFT, padx=5)

    # selection handled by item click handlers in the custom items_frame

    refresh_list(plots)
    root.mainloop()


if __name__ == "__main__":
    gui_main()
