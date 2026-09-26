# -*- coding: utf-8 -*-
"""ArkPlots application identity and release metadata.

Single source of truth for packaging and runtime (``/api/version``).
Bump ``VERSION`` when shipping. In-app updates scan GitHub tags matching
``APP_Ver*`` (e.g. ``APP_Ver26.9.26.2``) and pick the newest version.
"""
from __future__ import annotations

from typing import Any

# Display / product name (window title, about text).
APP_NAME = "ArkPlots"

# Stable executable stem used by PyInstaller (in-place updater replaces this file).
EXE_STEM = "ArkPlots"

# Semver-like calendar build: YY.M.D.build  (e.g. 26.9.26.2 = 2026-09-26 #2)
VERSION = "26.9.26.2"

# Release channel label.
CHANNEL = "release"

# GitHub repo + APP desktop tag prefix used by the in-app updater.
GITHUB_REPO = "ApodidaeDeSwift/ArkPlots"
UPDATE_TAG_PREFIX = "APP_Ver"


def release_exe_name(version: str | None = None) -> str:
    """Distribution filename shown to users / GitHub releases."""
    ver = version or VERSION
    return f"Arkplot_ver{ver}.exe"


def app_ver_tag(version: str | None = None) -> str:
    """GitHub release tag for an APP build, e.g. ``APP_Ver26.9.26.2``."""
    return f"{UPDATE_TAG_PREFIX}{version or VERSION}"


def version_payload() -> dict[str, Any]:
    """JSON body for GET /api/version (and update checks)."""
    return {
        "name": APP_NAME,
        "version": VERSION,
        "channel": CHANNEL,
        "exe_stem": EXE_STEM,
        "release_exe": release_exe_name(),
        "github_repo": GITHUB_REPO,
        "update_tag_prefix": UPDATE_TAG_PREFIX,
        "update_tag": app_ver_tag(),
        "update_html_url": f"https://github.com/{GITHUB_REPO}/releases",
    }
