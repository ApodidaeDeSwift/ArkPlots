# -*- coding: utf-8 -*-
"""Check GitHub APP_Ver* tags and apply in-place exe updates.

Update source: tags named ``APP_VerYY.M.D.N`` on ApodidaeDeSwift/ArkPlots
(e.g. ``APP_Ver26.9.26.2`` = 2026-09-26, 2nd build that day). The updater
lists those tags, picks the highest version, and downloads that release's
``.exe`` asset when it is newer than the installed build.

Only the running executable (and optional stable ``ArkPlots.exe`` twin) is
replaced. User data beside the exe (Plotline.json, Read_record.json, covers,
etc.) is never deleted or overwritten by the updater.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import quote

from app_info import (
    EXE_STEM,
    GITHUB_REPO,
    UPDATE_TAG_PREFIX,
    VERSION,
    release_exe_name,
    version_payload,
)

RELEASES_HTML_URL = f"https://github.com/{GITHUB_REPO}/releases"
RELEASES_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
TAGS_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/tags"
RELEASE_BY_TAG_API = (
    f"https://api.github.com/repos/{GITHUB_REPO}/releases/tags/{{tag}}"
)

# Shown whenever the user checks / applies updates.
OVERSEAS_SOURCE_WARNING_ZH = (
    "现阶段更新只支持海外源（GitHub）。在没有梯子 / 稳定代理的情况下，"
    "检查与下载未必稳定，请耐心重试或稍后再试。"
)
OVERSEAS_SOURCE_WARNING_EN = (
    "Updates currently use an overseas source (GitHub) only. "
    "Without a VPN / stable proxy, checking or downloading may be unreliable."
)

_USER_AGENT = f"ArkPlots-Updater/{VERSION} (+https://github.com/{GITHUB_REPO})"

# Files / dirs the updater may create. Everything else in the app directory
# (Plotline.json, Read_record.json, covers/, etc.) is left untouched.
_UPDATE_DIR_NAME = "_update"

# Match APP_Ver26.9.26.2 (optional underscore after Ver).
_APP_VER_TAG_RE = re.compile(
    rf"^{re.escape(UPDATE_TAG_PREFIX)}_?(\d+(?:\.\d+){{1,3}})$",
    re.IGNORECASE,
)


def parse_version(text: str | None) -> tuple[int, ...] | None:
    """Extract ``a.b.c.d`` (or shorter) from a tag / release / asset name."""
    if not text:
        return None
    m = re.search(r"(\d+(?:\.\d+){1,3})", str(text))
    if not m:
        return None
    parts = tuple(int(x) for x in m.group(1).split("."))
    padded = parts + (0,) * (4 - len(parts))
    return padded[:4]


def parse_app_ver_tag(tag_name: str | None) -> tuple[int, ...] | None:
    """Parse version only from ``APP_Ver*`` tags; ignore other tags."""
    if not tag_name:
        return None
    m = _APP_VER_TAG_RE.match(str(tag_name).strip())
    if not m:
        return None
    return parse_version(m.group(1))


def version_tuple_to_str(ver: tuple[int, ...]) -> str:
    return ".".join(str(x) for x in ver)


def compare_versions(a: tuple[int, ...], b: tuple[int, ...]) -> int:
    if a < b:
        return -1
    if a > b:
        return 1
    return 0


def _http_json(url: str, timeout: float = 25.0) -> Any:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": _USER_AGENT,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    return json.loads(raw.decode("utf-8"))


def _list_app_ver_from_releases(
    per_page: int = 100, max_pages: int = 10
) -> list[tuple[str, tuple[int, ...], dict[str, Any]]]:
    """Scan published releases whose tag matches ``APP_Ver*``."""
    found: list[tuple[str, tuple[int, ...], dict[str, Any]]] = []
    for page in range(1, max_pages + 1):
        url = f"{RELEASES_API_URL}?per_page={per_page}&page={page}"
        batch = _http_json(url)
        if not isinstance(batch, list) or not batch:
            break
        for item in batch:
            if not isinstance(item, dict):
                continue
            if item.get("draft"):
                continue
            tag = str(item.get("tag_name") or "")
            ver = parse_app_ver_tag(tag)
            if ver is not None:
                found.append((tag, ver, item))
        if len(batch) < per_page:
            break
    return found


def _list_app_ver_tags(per_page: int = 100, max_pages: int = 10) -> list[tuple[str, tuple[int, ...]]]:
    """Return ``(tag_name, version_tuple)`` for every ``APP_Ver*`` tag found."""
    found: list[tuple[str, tuple[int, ...]]] = []
    for page in range(1, max_pages + 1):
        url = f"{TAGS_API_URL}?per_page={per_page}&page={page}"
        batch = _http_json(url)
        if not isinstance(batch, list) or not batch:
            break
        for item in batch:
            name = str((item or {}).get("name") or "")
            ver = parse_app_ver_tag(name)
            if ver is not None:
                found.append((name, ver))
        if len(batch) < per_page:
            break
    return found


def _fetch_release_for_tag(tag_name: str) -> dict[str, Any]:
    url = RELEASE_BY_TAG_API.format(tag=quote(tag_name, safe=""))
    return _http_json(url)


def _pick_exe_asset(assets: list[dict[str, Any]], remote_version: str) -> dict[str, Any] | None:
    if not assets:
        return None
    exes = [
        a
        for a in assets
        if str(a.get("name", "")).lower().endswith(".exe") and a.get("browser_download_url")
    ]
    if not exes:
        return None
    preferred = release_exe_name(remote_version).lower()
    for a in exes:
        if str(a.get("name", "")).lower() == preferred:
            return a
    for a in exes:
        name = str(a.get("name", "")).lower()
        if name.startswith("arkplot_ver") or name == f"{EXE_STEM.lower()}.exe":
            return a
    return exes[0]


def _base_error(error: str, message: str, **extra: Any) -> dict[str, Any]:
    return {
        "ok": False,
        "error": error,
        "message": message,
        "warning": OVERSEAS_SOURCE_WARNING_ZH,
        "warning_en": OVERSEAS_SOURCE_WARNING_EN,
        "current": version_payload(),
        "html_url": RELEASES_HTML_URL,
        **extra,
    }


def check_for_update() -> dict[str, Any]:
    """Find the newest ``APP_Ver*`` tag/release and compare with local VERSION."""
    local = parse_version(VERSION)
    if local is None:
        return _base_error("invalid_local_version", f"Local version is invalid: {VERSION}")

    release: dict[str, Any] | None = None
    tag_name = ""
    remote: tuple[int, ...] | None = None

    try:
        from_releases = _list_app_ver_from_releases()
        if from_releases:
            tag_name, remote, release = max(from_releases, key=lambda item: item[1])
        else:
            # Fallback: tags may exist before a Release is published.
            tags = _list_app_ver_tags()
            latest = max(tags, key=lambda item: item[1]) if tags else None
            if latest is None:
                return _base_error(
                    "no_app_ver_tags",
                    f"No tags matching {UPDATE_TAG_PREFIX}* were found on GitHub",
                )
            tag_name, remote = latest
            try:
                release = _fetch_release_for_tag(tag_name)
            except urllib.error.HTTPError as exc:
                if exc.code != 404:
                    raise
                release = None
    except urllib.error.HTTPError as exc:
        return _base_error("http_error", f"GitHub HTTP {exc.code}")
    except Exception as exc:
        return _base_error("network_error", str(exc))

    assert remote is not None
    remote_str = version_tuple_to_str(remote)
    update_available = compare_versions(local, remote) < 0
    html_fallback = (
        f"https://github.com/{GITHUB_REPO}/releases/tag/{quote(tag_name, safe='')}"
    )

    if release is None:
        return {
            "ok": True,
            "update_available": update_available,
            "up_to_date": not update_available,
            "current_version": VERSION,
            "remote_version": remote_str,
            "remote_tag": tag_name,
            "remote_name": tag_name,
            "asset_name": None,
            "asset_url": None,
            "asset_size": None,
            "has_asset": False,
            "html_url": html_fallback,
            "warning": OVERSEAS_SOURCE_WARNING_ZH,
            "warning_en": OVERSEAS_SOURCE_WARNING_EN,
            "frozen": bool(getattr(sys, "frozen", False)),
            "error": "no_release",
            "message": f"Tag {tag_name} has no GitHub Release yet",
        }

    assets = release.get("assets") or []
    asset = _pick_exe_asset(list(assets), remote_str)

    return {
        "ok": True,
        "update_available": update_available,
        "up_to_date": not update_available,
        "current_version": VERSION,
        "remote_version": remote_str,
        "remote_tag": tag_name,
        "remote_name": release.get("name") or tag_name,
        "asset_name": (asset or {}).get("name"),
        "asset_url": (asset or {}).get("browser_download_url"),
        "asset_size": (asset or {}).get("size"),
        "has_asset": asset is not None,
        "html_url": release.get("html_url") or html_fallback,
        "warning": OVERSEAS_SOURCE_WARNING_ZH,
        "warning_en": OVERSEAS_SOURCE_WARNING_EN,
        "frozen": bool(getattr(sys, "frozen", False)),
    }


def _app_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def _running_exe_path() -> str | None:
    if getattr(sys, "frozen", False):
        return os.path.abspath(sys.executable)
    return None


def _download_file(url: str, dest: str, timeout: float = 120.0) -> None:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": _USER_AGENT,
            "Accept": "application/octet-stream",
        },
    )
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    partial = dest + ".partial"
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp, open(partial, "wb") as out:
            shutil.copyfileobj(resp, out, length=1024 * 256)
        os.replace(partial, dest)
    finally:
        if os.path.isfile(partial):
            try:
                os.remove(partial)
            except OSError:
                pass


def _write_windows_swapper(
    *,
    pid: int,
    new_exe: str,
    target_exe: str,
    optional_stable: str | None,
    restart: bool,
) -> str:
    """Batch file: wait for PID, replace exe only, then optionally restart."""
    update_dir = os.path.dirname(new_exe)
    bat_path = os.path.join(update_dir, "apply_update.bat")
    lines = [
        "@echo off",
        "setlocal EnableExtensions",
        f"set \"PID={pid}\"",
        f"set \"NEW={new_exe}\"",
        f"set \"DST={target_exe}\"",
        ":waitloop",
        "tasklist /FI \"PID eq %PID%\" | findstr /I \"%PID%\" >nul",
        "if not errorlevel 1 (",
        "  timeout /t 1 /nobreak >nul",
        "  goto waitloop",
        ")",
        "timeout /t 1 /nobreak >nul",
        "copy /Y \"%NEW%\" \"%DST%\" >nul",
        "if errorlevel 1 (",
        "  echo UPDATE_FAILED> \"%~dp0update_failed.txt\"",
        "  exit /b 1",
        ")",
    ]
    if optional_stable and os.path.normcase(optional_stable) != os.path.normcase(target_exe):
        lines.append(f"set \"STABLE={optional_stable}\"")
        lines.append("if exist \"%STABLE%\" copy /Y \"%NEW%\" \"%STABLE%\" >nul")
    if restart:
        lines.append("start \"\" \"%DST%\"")
    lines.extend(
        [
            "del /F /Q \"%NEW%\" >nul 2>&1",
            "del /F /Q \"%~f0\" >nul 2>&1",
            "exit /b 0",
        ]
    )
    with open(bat_path, "w", encoding="gbk", errors="replace", newline="\r\n") as f:
        f.write("\r\n".join(lines) + "\r\n")
    return bat_path


def _schedule_process_exit(delay: float = 1.2) -> None:
    def _exit() -> None:
        time.sleep(delay)
        try:
            import webview

            for win in list(getattr(webview, "windows", []) or []):
                try:
                    win.destroy()
                except Exception:
                    pass
        except Exception:
            pass
        os._exit(0)

    threading.Thread(target=_exit, name="arkplots-update-exit", daemon=True).start()


def apply_update(*, restart: bool = True) -> dict[str, Any]:
    """Download the remote exe and schedule a safe replace of the running binary."""
    check = check_for_update()
    if not check.get("ok"):
        return check
    if not check.get("update_available"):
        return {
            **check,
            "applied": False,
            "message": "already_up_to_date",
        }
    if not check.get("has_asset") or not check.get("asset_url"):
        return {
            **check,
            "applied": False,
            "error": "no_asset",
            "message": "Release has no .exe asset to download",
        }

    exe_path = _running_exe_path()
    if not exe_path:
        return {
            **check,
            "applied": False,
            "error": "not_frozen",
            "message": "Updates can only be applied to the packaged .exe build",
        }

    app_dir = _app_dir()
    update_dir = os.path.join(app_dir, _UPDATE_DIR_NAME)
    os.makedirs(update_dir, exist_ok=True)
    asset_name = str(check.get("asset_name") or "ArkPlots_update.exe")
    safe_name = re.sub(r"[^\w.\-]+", "_", asset_name) or "update.exe"
    download_path = os.path.join(update_dir, safe_name)

    try:
        _download_file(str(check["asset_url"]), download_path)
    except Exception as exc:
        return {
            **check,
            "applied": False,
            "error": "download_failed",
            "message": str(exc),
            "warning": OVERSEAS_SOURCE_WARNING_ZH,
            "warning_en": OVERSEAS_SOURCE_WARNING_EN,
        }

    if not os.path.isfile(download_path) or os.path.getsize(download_path) < 1024 * 100:
        return {
            **check,
            "applied": False,
            "error": "download_invalid",
            "message": "Downloaded file is missing or too small",
        }

    stable_twin = os.path.join(app_dir, f"{EXE_STEM}.exe")
    optional_stable = stable_twin if os.path.isfile(stable_twin) else None

    bat = _write_windows_swapper(
        pid=os.getpid(),
        new_exe=download_path,
        target_exe=exe_path,
        optional_stable=optional_stable,
        restart=restart,
    )
    creationflags = 0
    if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
        creationflags |= subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
    if hasattr(subprocess, "DETACHED_PROCESS"):
        creationflags |= subprocess.DETACHED_PROCESS  # type: ignore[attr-defined]
    subprocess.Popen(
        ["cmd.exe", "/c", bat],
        cwd=update_dir,
        close_fds=True,
        creationflags=creationflags,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
    )
    _schedule_process_exit()
    return {
        **check,
        "applied": True,
        "will_restart": restart,
        "message": "update_scheduled",
        "target_exe": exe_path,
        "note": "User data files are not modified; only the executable is replaced.",
    }
