#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Write web/src/version.ts from app_info.VERSION and app_info.CHANNEL."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app_info import CHANNEL, VERSION  # noqa: E402

_CHANNELS = ("release", "preview")


def frontend_version_ts() -> str:
    if CHANNEL not in _CHANNELS:
        raise SystemExit(
            f"app_info.CHANNEL must be one of {_CHANNELS}, got {CHANNEL!r}"
        )
    return (
        "/** Generated from app_info.py. Do not edit. */\n"
        f"export const APP_VERSION = '{VERSION}'\n"
        "export const APP_CHANNEL: 'release' | 'preview' = "
        f"'{CHANNEL}'\n"
    )


def sync_frontend_version(dest: Path | None = None) -> Path:
    path = dest or (ROOT / "web" / "src" / "version.ts")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(frontend_version_ts(), encoding="utf-8", newline="\n")
    return path


if __name__ == "__main__":
    written = sync_frontend_version()
    print(f"synced {written.relative_to(ROOT)} -> {VERSION} {CHANNEL}", flush=True)
