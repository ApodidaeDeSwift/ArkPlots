# -*- coding: utf-8 -*-
"""ArkPlots application identity and release metadata.

Single source of truth for packaging and runtime (``/api/version``).
Bump ``VERSION`` when shipping. In-app updates scan GitHub tags matching
``APP_Ver*`` (e.g. ``APP_Ver26.9.26.2``) and pick the newest version.
"""
from __future__ import annotations

import sys
from typing import Any

# Display / product name (window title, about text).
APP_NAME = "ArkPlots"

# Stable executable stem used by PyInstaller (in-place updater replaces this file).
EXE_STEM = "ArkPlots"

# Semver-like calendar build: YY.M.D.build  (e.g. 26.10.5.1 = 2026-10-05 #1)
# 改版本只改这一处。web/src/version.ts 在前端构建和打包时自动生成。
# Update.md 里写 {{VERSION}}，显示更新公告时会换成这个版本号。
VERSION = "26.10.28.11"

# 发布通道。只改这里。前端默认更新通道会跟着生成。
# 打上 APP_Ver 标签后，GitHub Actions 会按这里设置 Pre-release：
# release 为正式版（不勾选），preview 为测试版（勾选，且不标成 Latest）。
#
# 正式版：
#   CHANNEL = "release"
#   设置里选「正式版」的用户只会收到这种 Release。
#
# 测试版：
#   CHANNEL = "preview"
#   只有在设置里选「测试版」的用户才会收到。比它新的正式版仍会提示更新。
CHANNEL = "preview"

# GitHub repo + APP desktop tag prefix used by the in-app updater.
# Stable AppId for Inno Setup (detect existing installs / upgrades).
INNO_APP_ID = "{E8B3C4A1-7D2F-4E9B-A6C1-1F2E3D4C5B6A}"
GITHUB_REPO = "ApodidaeDeSwift/ArkPlots"
UPDATE_TAG_PREFIX = "APP_Ver"


def release_exe_name(version: str | None = None) -> str:
    """Portable exe filename (internal PyInstaller output alias)."""
    ver = version or VERSION
    return f"Arkplot_ver{ver}.exe"


def release_setup_name(version: str | None = None) -> str:
    """Installer filename published on GitHub Releases."""
    ver = version or VERSION
    return f"Arkplot_setup_ver{ver}.exe"


def app_ver_tag(version: str | None = None) -> str:
    """GitHub release tag for an APP build, e.g. ``APP_Ver26.9.26.2``."""
    return f"{UPDATE_TAG_PREFIX}{version or VERSION}"


def is_packaged() -> bool:
    """True when this process is the PyInstaller executable.

    The bootloader always sets ``sys._MEIPASS``. ``sys.frozen`` is set later,
    and only when it is not already present, so a falsy ``sys.frozen`` must
    not be treated as a source checkout. That false negative made one-click
    update tell packaged users they were in development mode.
    """
    if getattr(sys, "frozen", False):
        return True
    return hasattr(sys, "_MEIPASS")


def version_payload() -> dict[str, Any]:
    """JSON body for GET /api/version (and update checks)."""
    return {
        "name": APP_NAME,
        "version": VERSION,
        "channel": CHANNEL,
        "exe_stem": EXE_STEM,
        "release_exe": release_exe_name(),
        "release_setup": release_setup_name(),
        "github_repo": GITHUB_REPO,
        "update_tag_prefix": UPDATE_TAG_PREFIX,
        "update_tag": app_ver_tag(),
        "update_html_url": f"https://github.com/{GITHUB_REPO}/releases",
    }
