# ArkPlots

**Arknights Plotline Tracker** (local Web edition)

English | [简体中文](README.md)

A local tool for browsing, filtering, and tracking *Arknights* story entries (Main Theme, Side Stories, Story Collections, Integrated Strategies, and more). Manage your reading progress and get recommendations for what to catch up on—or what you can safely read next.

If you find it useful, a ⭐ on GitHub is always appreciated.

---

# Regular players — start here

## How to run

### Option A: Packaged EXE (easiest)

If the repo includes an `Arkplot_ver*.exe` (e.g. `Arkplot_ver1.0.4.exe`):

1. Keep the EXE next to `Plotline.json` (you do not need to create a reading-record file yourself)
2. Double-click the EXE
3. Your browser opens the local page (usually `http://127.0.0.1:8765/`)

> The packaged build embeds the UI. You only need `Plotline.json` beside the EXE. `Read_record.json` is created automatically on first run.

### Option B: Minimal source launch

If you have Python and a built `web/dist` folder:

```bash
python main.py
```

This opens your browser at **http://127.0.0.1:8765/**  
If port `8765` is busy, the app picks the next free port (check the terminal).

Keep these files next to the program:

| File | Purpose |
| --- | --- |
| `Plotline.json` | Story data (shipped with the repo) |
| `Read_record.json` | Reading progress (created automatically if missing) |

## Features at a glance

- Three-pane UI: filters & list / detail preview / recommendations
- Filter by date, type, nation, operators, stage, factions, and more; track Unread / Planned / Reading / Read
- Required / optional prerequisites plus catch-up and “read next” suggestions
- Related videos: open or copy links
- Switch **简体中文 / English** from the top bar

## Contact / support / disclaimer

- GitHub: [@ApodidaeDeSwift](https://github.com/ApodidaeDeSwift)
- WeChat: `Quantumaster233` · QQ: `3195582616`
- Bilibili: [space.bilibili.com/281039105](https://space.bilibili.com/281039105)

If ArkPlots helps you, feel free to buy the author a Mixue drink (蜜雪冰城):

![Support](coffee.png)

This is a personal learning and organizing tool. *Arknights* and related text/settings belong to Hypergryph and other rights holders. Data and UI in this repo are for study and non-commercial sharing only.

---

# Contributors & advanced users

## Requirements

| Purpose | Dependency |
| --- | --- |
| Run the Web UI | Python 3.10+ (stdlib only; no extra pip packages) |
| Build / edit the frontend | [Node.js](https://nodejs.org/) 18+ (with npm) |
| Optional: legacy desktop UI | tkinter (usually bundled with Python) |

## Build the frontend & launch

First time, or after changes under `web/`:

```bash
cd web
npm install
npm run build
cd ..
python main.py
```

Output goes to `web/dist/`. If it is missing, the server will remind you to run the commands above.

### Common options

```bash
python main.py --port 8765     # preferred port (default 8765)
python main.py --no-browser    # do not open a browser
python main.py --tk            # legacy tkinter UI
```

Or start the server directly:

```bash
python server.py --port 8765 --no-browser
```

`server.py` serves static files from `web/dist` and exposes:

- `GET /api/plots` — plotline data
- `GET /api/records` / `PUT /api/records` — reading records
- `GET /api/health` — health check

## Development

Run API and Vite separately for hot reload:

```bash
# Terminal 1: API (default port 8765)
python server.py --no-browser

# Terminal 2: Vite (proxies /api → 8765)
cd web
npm run dev
```

## About different servers

Dates currently follow the **CN (Mainland China) server**, and recommended videos are primarily from **Bilibili**. Help adding Global / JP / KR dates or links is welcome—please get in touch.

## Data

### Plotline.json

Story entries in release order. Common fields:

| Field | Description |
| --- | --- |
| `id` | Unique id |
| `name` | Story title (Chinese in the file; display can be localized) |
| `date` | Release date (`YYYY-MM-DD`, CN server) |
| `class` | Type: `main` / `sidestory` / `interlude` / `ministory` / `manga` / `anime` / `rougelike` / `RA` / `other` |
| `country` | Related nation / region |
| `new_operator` | Concurrent operators |
| `plot_stage` | Story stage |
| `related_power` | Related factions |
| `related_plot` | Related tags |
| `description` | Description text |
| `necessary_plot` | Required prerequisites (may include `id`, `reason`, optional `reason_en`) |
| `optional_plot` | Optional prerequisites |
| `Videos` | Related videos |

### Read_record.json

Keys are story `id`s (strings). Values: `未读` | `计划读` | `正在读` | `已读`.  
These Chinese codes are stable in the data layer. Switching the UI language only changes labels; it does not rewrite the file.

## Internationalization

- Default locale: `zh-CN`; also ships `en-US`. Preference in `localStorage` (`arkplots.locale`)
- UI strings: `web/src/i18n/locales/`; content maps: `web/src/i18n/content/`
- **Translations were drafted with Cursor using Moegirl Wiki and may not be fully accurate.** Please open an issue or PR if you spot mistakes.

### Adding a language

1. Add a message pack under `web/src/i18n/locales/` (same shape as `zh-CN.ts`)
2. Register it in `localeRegistry` in `locales/index.ts`
3. Optionally add content maps under `web/src/i18n/content/`
4. Run `npm run build` again

## Project layout

```
ArkPlots/
├── Plotline.json          # Story data
├── Read_record.json       # Reading progress
├── main.py                # Launcher (Web by default; --tk for legacy UI)
├── server.py              # Local HTTP API + static files
├── web/                   # Vite + React + TypeScript frontend
│   ├── src/i18n/          # UI & content i18n
│   └── dist/              # Build output (from npm run build)
├── README.md              # Chinese README
└── README.en.md           # This file
```
