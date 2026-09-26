# -*- coding: utf-8 -*-
"""Check GitHub APP release and apply in-place exe updates.

Update source: release tag ``APP版本`` on ApodidaeDeSwift/ArkPlots.
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
    UPDATE_RELEASE_TAG,
    VERSION,
    release_exe_name,
    version_payload,
)

UPDATE_API_URL = (
    f"https://api.github.com/repos/{GITHUB_REPO}/releases/tags/"
    f"{quote(UPDATE_RELEASE_TAG, safe='')}"
)
UPDATE_HTML_URL = (
    f"https://github.com/{GITHUB_REPO}/releases/tag/"
    f"{quote(UPDATE_RELEASE_TAG, safe='')}"
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


def parse_version(text: str | None) -> tuple[int, ...] | None:
    """Extract ``a.b.c.d`` (or shorter) from a release name / asset name."""
    if not text:
        return None
    m = re.search(r"(\d+(?:\.\d+){1,3})", str(text))
    if not m:
        return None
    parts = tuple(int(x) for x in m.group(1).split("."))
    # Normalize to 4-tuple for comparison
    padded = parts + (0,) * (4 - len(parts))
    return padded[:4]


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


def check_for_update() -> dict[str, Any]:
    """Fetch the floating ``APP版本`` release and compare with local VERSION."""
    local = parse_version(VERSION)
    if local is None:
        return {
            "ok": False,
            "error": "invalid_local_version",
            "message": f"Local version is invalid: {VERSION}",
            "warning": OVERSEAS_SOURCE_WARNING_ZH,
            "warning_en": OVERSEAS_SOURCE_WARNING_EN,
            "current": version_payload(),
            "html_url": UPDATE_HTML_URL,
        }

    try:
        release = _http_json(UPDATE_API_URL)
    except urllib.error.HTTPError as exc:
        return {
            "ok": False,
            "error": "http_error",
            "message": f"GitHub HTTP {exc.code}",
            "warning": OVERSEAS_SOURCE_WARNING_ZH,
            "warning_en": OVERSEAS_SOURCE_WARNING_EN,
            "current": version_payload(),
            "html_url": UPDATE_HTML_URL,
        }
    except Exception as exc:
        return {
            "ok": False,
            "error": "network_error",
            "message": str(exc),
            "warning": OVERSEAS_SOURCE_WARNING_ZH,
            "warning_en": OVERSEAS_SOURCE_WARNING_EN,
            "current": version_payload(),
            "html_url": UPDATE_HTML_URL,
        }

    assets = release.get("assets") or []
    remote_raw = (
        release.get("name")
        or release.get("tag_name")
        or (assets[0].get("name") if assets else None)
    )
    remote = parse_version(str(remote_raw) if remote_raw else None)
    if remote is None:
        return {
            "ok": False,
            "error": "invalid_remote_version",
            "message": f"Could not parse version from release: {remote_raw!r}",
            "warning": OVERSEAS_SOURCE_WARNING_ZH,
            "warning_en": OVERSEAS_SOURCE_WARNING_EN,
            "current": version_payload(),
            "html_url": release.get("html_url") or UPDATE_HTML_URL,
        }

    remote_str = version_tuple_to_str(remote)
    asset = _pick_exe_asset(list(assets), remote_str)
    # Floating tag APP版本 holds the intended Latest; update only when it is
    # newer than the installed build (local ahead of tag => treat as current).
    update_available = compare_versions(local, remote) < 0

    return {
        "ok": True,
        "update_available": update_available,
        "up_to_date": not update_available,
        "current_version": VERSION,
        "remote_version": remote_str,
        "remote_name": release.get("name") or "",
        "asset_name": (asset or {}).get("name"),
        "asset_url": (asset or {}).get("browser_download_url"),
        "asset_size": (asset or {}).get("size"),
        "has_asset": asset is not None,
        "html_url": release.get("html_url") or UPDATE_HTML_URL,
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
    # Escape for batch: use short quotes carefully
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
        # Replace only the running executable path.
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
    # Keep download name predictable and confined under _update/
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
    # Detached so it survives our exit
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
