# -*- coding: utf-8 -*-
"""ArkPlots application identity and release metadata.

Single source of truth for packaging and runtime (``/api/version``).
Bump ``VERSION`` when shipping; leave update URL empty until the updater is ready.
"""
from __future__ import annotations

from typing import Any

# Display / product name (window title, about text).
APP_NAME = "ArkPlots"

# Stable executable stem used by PyInstaller (future in-place updater replaces this file).
EXE_STEM = "ArkPlots"

# Semver-like calendar build: YY.M.D.build  (e.g. 26.9.23.2)
VERSION = "26.9.23.2"

# Release channel label for future update manifests.
CHANNEL = "release"

# When non-empty, clients may fetch a JSON manifest for updates.
# Example shape (future): {"version":"...","url":"...","sha256":"...","notes":"..."}
UPDATE_MANIFEST_URL = ""


def release_exe_name(version: str | None = None) -> str:
    """Distribution filename shown to users / GitHub releases."""
    ver = version or VERSION
    return f"Arkplot_ver{ver}.exe"


def version_payload() -> dict[str, Any]:
    """JSON body for GET /api/version (and future update checks)."""
    return {
        "name": APP_NAME,
        "version": VERSION,
        "channel": CHANNEL,
        "exe_stem": EXE_STEM,
        "release_exe": release_exe_name(),
        "update_manifest_url": UPDATE_MANIFEST_URL or None,
    }
