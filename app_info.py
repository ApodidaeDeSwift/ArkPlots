# -*- coding: utf-8 -*-
"""ArkPlots application identity and release metadata.

Single source of truth for packaging and runtime (``/api/version``).
Bump ``VERSION`` when shipping. In-app updates read the floating GitHub
release tag ``UPDATE_RELEASE_TAG`` (``APP版本``).
"""
from __future__ import annotations

from typing import Any

# Display / product name (window title, about text).
APP_NAME = "ArkPlots"

# Stable executable stem used by PyInstaller (in-place updater replaces this file).
EXE_STEM = "ArkPlots"

# Semver-like calendar build: YY.M.D.build  (e.g. 26.9.23.2)
VERSION = "26.9.26.1"

# Release channel label for update manifests / GitHub floating tag.
CHANNEL = "release"

# Floating GitHub release tag used by the in-app updater (APP desktop builds).
GITHUB_REPO = "ApodidaeDeSwift/ArkPlots"
UPDATE_RELEASE_TAG = "APP版本"


def release_exe_name(version: str | None = None) -> str:
    """Distribution filename shown to users / GitHub releases."""
    ver = version or VERSION
    return f"Arkplot_ver{ver}.exe"


def version_payload() -> dict[str, Any]:
    """JSON body for GET /api/version (and update checks)."""
    return {
        "name": APP_NAME,
        "version": VERSION,
        "channel": CHANNEL,
        "exe_stem": EXE_STEM,
        "release_exe": release_exe_name(),
        "github_repo": GITHUB_REPO,
        "update_release_tag": UPDATE_RELEASE_TAG,
        "update_html_url": (
            f"https://github.com/{GITHUB_REPO}/releases/tag/{UPDATE_RELEASE_TAG}"
        ),
    }
