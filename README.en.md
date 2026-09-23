# ArkPlots

**Arknights Plotline Tracker**

English | [简体中文](README.md)

---

## For regular players

A local tool for browsing, filtering, and tracking *Arknights* story entries (Main Theme, Side Stories, Story Collections, Integrated Strategies, and more). Manage reading progress and get recommendations for what to catch up on—or what you can safely read next.

If you find it useful, a ⭐ on GitHub is always appreciated.

### After you download

1. Keep **`Arkplot_ver26.9.23.2.exe`** and **`Plotline.json`** (story data) in the **same folder**.
2. Double-click the exe. It opens a native window titled **ArkPlots** (about 1400×900, resizable). There is **no** console / command-line window, and it does **not** force open your system browser.
3. Closing the window exits the app. Progress is saved to `Read_record.json` in that same folder.

### Files next to the exe

| File | Notes |
| --- | --- |
| `Plotline.json` | **Required.** Story entries; must sit beside the exe |
| `Read_record.json` | Reading progress; created automatically if missing |

The Web UI is embedded in the exe—you do **not** need a separate `web/dist` folder. Windows usually already has Edge WebView2; if the window fails to open, install / repair WebView2.

### What you can do (short)

- Filter by date, type, nation, operators, stage, factions, related tags, and more
- Set read status: Unread / Planned / Reading / Read (single or batch)
- See required / optional prerequisites and catch-up / continue recommendations
- Open or copy related video links
- Switch Simplified Chinese / English in the top bar; promo art may appear in details when available

### About different servers

Dates currently follow the **CN (Mainland China) server**, and recommended videos are mainly from **Bilibili**. If you play on another server and want to help add Global / JP / KR dates or links, please get in touch.

### Author & support

- GitHub: [@ApodidaeDeSwift](https://github.com/ApodidaeDeSwift)
- WeChat: `Quantumaster233` · QQ: `3195582616`
- Bilibili: [space.bilibili.com/281039105](https://space.bilibili.com/281039105)

If ArkPlots helps you, feel free to buy the author a Mixue drink (蜜雪冰城):

![Support](coffee.png)

### License & disclaimer

This is a personal learning and organizing tool. *Arknights* and related text/settings belong to Hypergryph and other rights holders. Data and UI in this repo are for study and non-commercial sharing only. Issues and PRs on GitHub are welcome.

---

## For contributors & advanced users

For running from source, editing the frontend / data, or rebuilding the executable.

### Requirements

| Purpose | Dependency |
| --- | --- |
| Standalone window (default) | Python 3.10+ and [pywebview](https://pywebview.flowrl.com/) (`pip install -r requirements.txt`); Windows uses Edge WebView2 |
| Frontend build | [Node.js](https://nodejs.org/) 18+ (with npm) |
| Optional: system browser | `python main.py --browser` |
| Optional: legacy desktop UI | tkinter (usually bundled with Python), `python main.py --tk` |

Keep data beside the program: `Plotline.json` (required), `Read_record.json` (auto-created if missing).

### Build the frontend

First time, or after changes under `web/`:

```bash
cd web
npm install
npm run build
cd ..
```

Output goes to `web/dist/`. Source launches will remind you if it is missing.

### Launch from source

```bash
pip install -r requirements.txt
python main.py
```

By default this opens a **pywebview** window (no system browser). Preferred port is `8765`; if taken, the next free port is used and the window loads the **actually bound** URL. Closing the window stops the local server.

Options (as implemented in `main.py`):

```bash
python main.py --port 8765     # preferred port
python main.py --browser       # system browser instead of native window
python main.py --no-browser    # server only (for Vite hot reload)
python main.py --tk            # legacy tkinter UI
```

Or start the server directly (still opens a browser unless you pass `--no-browser`):

```bash
python server.py --port 8765 --no-browser
```

`server.py` only accepts `--port` and `--no-browser`.

### Development

```bash
# Terminal 1: API (default 8765)
python server.py --no-browser

# Terminal 2: Vite (proxies /api → 8765)
cd web
npm run dev
```

### Data fields

#### Plotline.json

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

#### Read_record.json

Keys are story `id`s (strings). Values: `未读` | `计划读` | `正在读` | `已读`.  
These Chinese codes are stable in the data layer. Switching the UI language only changes labels; it does not rewrite the file.

### Internationalization

- Default locale: `zh-CN`; also ships `en-US`. Preference in `localStorage` (`arkplots.locale`)
- UI strings: `web/src/i18n/locales/`; content maps: `web/src/i18n/content/`
- Translations were drafted with Cursor using Moegirl Wiki and **may not be fully accurate**—please open an issue or PR if you spot mistakes

To add a language: add a pack under `locales/` → register in `localeRegistry` in `locales/index.ts` → optionally add `content/` maps → `npm run build`.

### Packaging the exe (no console)

Bump `VERSION` in root `app_info.py`, then:

```bash
pip install -r requirements.txt pyinstaller
cd web && npm install && cd ..
python packaging/build_release.py
```

This syncs `web/src/version.ts`, builds the UI, runs `packaging/ArkPlots.spec` to produce stable `dist/ArkPlots.exe`, and copies the distribution alias `Arkplot_ver{VERSION}.exe`.

`Plotline.json` / `Read_record.json` are **not** bundled. No console window (`console=False`). Edge WebView2 required.

For future auto-updates: set `app_info.UPDATE_MANIFEST_URL`; clients can read `GET /api/version`.

### Project layout

```
ArkPlots/
├── Plotline.json          # Story data
├── Read_record.json       # Reading progress
├── main.py                # Launcher (native window by default; --browser / --tk optional)
├── requirements.txt       # pywebview, etc.
├── server.py              # Local HTTP API + static files
├── app_info.py            # version / update metadata
├── packaging/ArkPlots.spec # PyInstaller (console=False)
├── packaging/build_release.py
├── web/                   # Vite + React + TypeScript
│   ├── src/i18n/          # UI & content i18n
│   └── dist/              # Build output
├── README.md              # Chinese README
└── README.en.md           # This file
```

API sketch:

- `GET /api/plots` — plotline data
- `GET /api/records` / `PUT /api/records` — reading records
- `GET /api/version` — version / update metadata
- `GET /api/health` — health check
