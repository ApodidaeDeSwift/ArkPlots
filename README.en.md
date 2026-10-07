# ArkPlots

**Arknights Plotline Tracker**

English | [简体中文](README.md)

---

## For regular players

A local tool for browsing, filtering, and tracking *Arknights* story entries (Main Theme, Side Stories, Story Collections, Integrated Strategies, and more). Manage reading progress and get recommendations for what to catch up on—or what you can safely read next.

If you find it useful, a ⭐ on GitHub is always appreciated.

### After you download

1. Open [GitHub Releases](https://github.com/ApodidaeDeSwift/ArkPlots/releases) and download the latest **`Arkplot_setup_ver*.exe`** installer (tags look like `APP_Ver…`).
2. Run the installer. Default path is `%LOCALAPPDATA%\ArkPlots` (changeable); optional desktop shortcut. A fresh install ships `Plotline.json`.
3. Launch from the Start menu or desktop shortcut. A native window titled **ArkPlots** opens (about 1400×900, resizable). There is **no** console window.
4. Closing the window exits the app. Progress is saved as `Read_record.json` in the install folder (upgrades do **not** wipe it).

> The older portable layout (exe + `Plotline.json` in one folder) still works, but new builds are meant to be installed via the setup package.

### Files in the install folder

| File / folder | Notes |
| --- | --- |
| `ArkPlots.exe` and program files | Written by the installer; replaced on upgrade |
| `Plotline.json` | Story data (bundled with the installer) |
| `Read_record.json` | Reading progress; created if missing. On startup, new plot ids missing from the file are added as Unread |

The Web UI is embedded—you do **not** need a separate `web/dist` folder. Windows usually already has Edge WebView2; if the window fails to open, install / repair WebView2.

### What you can do (short)

- Filter by date, type, nation, operators, stage, chapter ownership, factions, related tags, and **read status**
- Set read status: Unread / Planned / Reading / Read (single or batch)
- See required / optional prerequisites and catch-up / continue recommendations
- Open or copy related video links
- **Settings**: toggles for promo art / reasons / prerequisites; in-app **check for updates and one-click upgrade** (needs GitHub access)
- Switch Simplified Chinese / English in the top bar

### Updates

- Settings → Version → “Check for updates” scans GitHub tags matching `APP_Ver*`
- When an installer asset is available, “Update and restart” replaces the program only—**progress is kept**
- Updates currently use GitHub only (may need a VPN outside mainland China)
- If SmartScreen shows **Publisher: Unknown**, the build is unsigned — see [packaging/SIGNING.md](packaging/SIGNING.md)

### About different servers

Dates currently follow the **CN (Mainland China) server**, and recommended videos are mainly from **Bilibili**. If you play on another server and want to help add Global / JP / KR dates or links, please get in touch.

### Author & support

- GitHub: [@ApodidaeDeSwift](https://github.com/ApodidaeDeSwift)
- WeChat: `Quantumaster233` · QQ: `3195582616`
- Bilibili: [space.bilibili.com/281039105](https://space.bilibili.com/281039105)

If ArkPlots helps you, feel free to buy the author a cup of coffee—the same page is also available from in-app Settings:

![Support](coffee.png)

### License & disclaimer

This is a personal learning and organizing tool. *Arknights* and related text/settings belong to Hypergryph and other rights holders. Data and UI in this repo are for study and non-commercial sharing only. Issues and PRs on GitHub are welcome.

---

## For contributors & advanced users

For running from source, editing the frontend / data, or rebuilding the installer.

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
| `chapter` | Chapter / scorebook ownership |
| `related_power` | Related factions |
| `related_plot` | Related tags |
| `description` | Description text |
| `necessary_plot` | Required prerequisites (may include `id`, `reason`, optional `reason_en`) |
| `optional_plot` | Optional prerequisites |
| `Videos` | Related videos |

#### Read_record.json

Keys are story `id`s (strings). Values: `未读` | `计划读` | `正在读` | `已读`.  
These Chinese codes are stable in the data layer. Switching the UI language only changes labels; it does not rewrite the file. On startup, ids present in `Plotline.json` but missing from the record file are added as Unread.

### Internationalization

- Default locale: `zh-CN`; also ships `en-US`. Preference in `localStorage` (`arkplots.locale`)
- UI strings: `web/src/i18n/locales/`; content maps: `web/src/i18n/content/`
- Translations were drafted with Cursor using Moegirl Wiki and **may not be fully accurate**—please open an issue or PR if you spot mistakes

To add a language: add a pack under `locales/` → register in `localeRegistry` in `locales/index.ts` → optionally add `content/` maps → `npm run build`.

### Packaging the installer (no console)

Bump `VERSION` in root `app_info.py`. Requires [Inno Setup 6](https://jrsoftware.org/isinfo.php) (`ISCC.exe`), then:

```bash
pip install -r requirements.txt pyinstaller pillow
cd web && npm install && cd ..
python packaging/build_release.py
```

This syncs version/wizard art, builds the frontend, produces a PyInstaller **onedir** tree at `dist/ArkPlots/` (UPX off), and compiles `Arkplot_setup_ver{VERSION}.exe` via `packaging/ArkPlots.iss`.

- **Fresh install:** default `%LOCALAPPDATA%\ArkPlots`, optional desktop shortcut, ships initial `Plotline.json`
- **Already installed:** confirm, then upgrade the program without deleting `Read_record.json`
- Installer UI follows the in-app teal terminal look (not stock Inno chrome)
- Tag `APP_Ver{VERSION}` on **APP_Release**; Actions attaches **`Arkplot_setup_ver{VERSION}.exe`**

Code signing / SmartScreen: see [`packaging/SIGNING.md`](packaging/SIGNING.md). Set `SIGN_PFX` / `SIGN_PFX_PASSWORD` (or GitHub secrets `SIGN_PFX_BASE64` + `SIGN_PFX_PASSWORD`) before packaging. You can also [submit samples to Microsoft](https://www.microsoft.com/wdsi/filesubmission), but signing is the real fix.

### Project layout

```
ArkPlots/
├── Plotline.json          # Story data
├── Read_record.json       # Reading progress
├── main.py                # Launcher (native window by default; --browser / --tk optional)
├── requirements.txt       # pywebview, etc.
├── server.py              # Local HTTP API + static files
├── updater.py             # In-app updater (APP_Ver* tags)
├── app_info.py            # version / update metadata
├── packaging/ArkPlots.spec # PyInstaller (onedir, console=False)
├── packaging/ArkPlots.iss  # Inno Setup installer
├── packaging/build_release.py
├── packaging/SIGNING.md   # Code-signing notes
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
- `GET /api/update/check` — check newest GitHub `APP_Ver*` release
- `POST /api/update/apply` — download installer and schedule replace/restart (packaged desktop only)
- `GET /api/health` — health check
