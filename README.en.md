# ArkPlots

**Arknights Plotline Tracker**

English | [简体中文](README.md)

A local tool for browsing, filtering, and tracking *Arknights* story entries (Main Theme, Side Stories, Story Collections, Integrated Strategies, and more). Manage your reading progress and get recommendations for what to catch up on—or what you can safely read next.

If you find it useful, a ⭐ on GitHub is always appreciated.

---

## Features

- **Web “intel desk” UI**: three-pane layout (filters & list / detail preview / recommendations)
- **Rich filters**: date range, story type, nation/region, concurrent operators (substring), stage, factions, related plot tags; some filters support match-any / match-all
- **Read status**: Unread / Planned / Reading / Read; single or batch updates, stored in `Read_record.json`
- **Details & prerequisites**: required / optional prereqs, jump links, preview history back / forward
- **Recommendations**: urgent catch-up, recommended catch-up, recommended next, readable next
- **Related videos**: open links or copy to clipboard
- **i18n**: UI and display names in Simplified Chinese / English (switcher in the top bar)

---

## About different servers

All dates currently follow the **CN (Mainland China) server**, and recommended videos are primarily from **Bilibili**. If you play on another server and would like to help add Global / JP / KR release dates or links, please get in touch.

---

## Requirements

| Purpose | Dependency |
| --- | --- |
| Run the Web UI | Python 3.10+ (stdlib only; no extra pip packages) |
| First-time frontend build | [Node.js](https://nodejs.org/) 18+ (with npm) |
| Optional: legacy desktop UI | tkinter (usually bundled with Python) |

Keep these data files next to the program:

- `Plotline.json` — story entries (included in the repo)
- `Read_record.json` — reading progress (created automatically if missing)

---

## Quick start (recommended)

### 1. Build the frontend (first time, or after changes under `web/`)

```bash
cd web
npm install
npm run build
cd ..
```

Output goes to `web/dist/`. If it is missing, the server will remind you to run the commands above.

### 2. Launch

```bash
python main.py
```

Opens a browser at: `http://127.0.0.1:8765/`  
If port `8765` is already in use, the app automatically tries the next free ports.

### 3. Common options

```bash
python main.py --port 8765     # preferred port
python main.py --no-browser    # do not open a browser
python main.py --tk            # legacy tkinter UI
```

You can also start the server directly:

```bash
python server.py --port 8765 --no-browser
```

### Packaged executable

If you use the bundled EXE:

```bash
./Arkplot_ver1.0.3.exe
```

Keep `Plotline.json` in the same folder. The Web UI is embedded in the EXE; for source runs you still need `web/dist` from `npm run build`.

---

## Development

Run API and Vite separately for hot reload:

```bash
# Terminal 1: API (default port 8765)
python server.py --no-browser

# Terminal 2: Vite (proxies /api → 8765)
cd web
npm run dev
```

---

## Data

### Plotline.json

Story entries in release order. Common fields:

| Field | Description |
| --- | --- |
| `id` | Unique id |
| `name` | Story title (Chinese in the file; display can be localized) |
| `date` | Release date (`YYYY-MM-DD`, CN server) |
| `class` | Type code: `main` / `sidestory` / `interlude` / `ministory` / `manga` / `anime` / `rougelike` / `RA` / `other` |
| `country` | Related nation / region |
| `new_operator` | Concurrent operators |
| `plot_stage` | Story stage |
| `related_power` | Related factions |
| `related_plot` | Related tags (e.g. Originium, Feranmut) |
| `description` | Description text |
| `necessary_plot` | Required prerequisites (may include `id`, `reason`, optional `reason_en`) |
| `optional_plot` | Optional prerequisites |
| `Videos` | Related videos |

### Read_record.json

Keys are story `id`s (strings). Values are read-status codes: `未读` | `计划读` | `正在读` | `已读`.  
**Note:** These Chinese codes are stable in the data layer. Switching the UI language only changes labels; it does not rewrite the file.

---

## Internationalization

- Default locale: `zh-CN`; also ships `en-US`
- Preference is stored in `localStorage` (`arkplots.locale`)
- UI strings: `web/src/i18n/locales/`
- Content maps (plot titles, nations, factions, operators, related tags): `web/src/i18n/content/`
- **Translations were drafted with Cursor using Moegirl Wiki and may not be fully accurate.** Please open an issue or PR if you spot mistakes.

### Adding a language

1. Add a message pack under `web/src/i18n/locales/` (same shape as `zh-CN.ts`)
2. Register it in `localeRegistry` in `locales/index.ts`
3. Optionally add content maps under `web/src/i18n/content/`
4. Run `npm run build` again

The language switcher lists registered locales automatically.

---

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

API sketch:

- `GET /api/plots` — plotline data
- `GET /api/records` / `PUT /api/records` — reading records

---

## Author & contact

- GitHub: [@ApodidaeDeSwift](https://github.com/ApodidaeDeSwift)
- WeChat: `Quantumaster233`
- QQ: `3195582616`
- Bilibili: [space.bilibili.com/281039105](https://space.bilibili.com/281039105)

---

## Support

If ArkPlots helps you, feel free to buy the author a Mixue drink (蜜雪冰城):

![Support](coffee.png)

Thank you!

---

## License & disclaimer

This is a personal learning and organizing tool. *Arknights* and related text/settings belong to Hypergryph and other rights holders. Data and UI in this repo are for study and non-commercial sharing only. Issues and PRs on GitHub are welcome.
