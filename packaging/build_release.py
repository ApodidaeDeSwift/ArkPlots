#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a release exe from app_info.VERSION.

Steps:
  1. Sync ``web/src/version.ts`` from ``app_info.py``
  2. ``npm run build`` in web/
  3. PyInstaller via ``packaging/ArkPlots.spec`` → ``dist/ArkPlots.exe``
  4. Copy distribution alias ``Arkplot_ver{VERSION}.exe`` to repo root

Usage (from repo root):
  python packaging/build_release.py
  python packaging/build_release.py --skip-web
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app_info import EXE_STEM, VERSION, release_exe_name  # noqa: E402


def _run(cmd: list[str], cwd: Path) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.check_call(cmd, cwd=str(cwd))


def sync_frontend_version() -> None:
    path = ROOT / "web" / "src" / "version.ts"
    content = (
        "/** App release version — generated/synced from app_info.py by build_release.py. */\n"
        f"export const APP_VERSION = '{VERSION}'\n"
    )
    path.write_text(content, encoding="utf-8", newline="\n")
    print(f"synced {path.relative_to(ROOT)} -> {VERSION}", flush=True)


def build_web() -> None:
    web = ROOT / "web"
    npm = shutil.which("npm")
    if not npm:
        raise SystemExit("npm not found on PATH")
    _run([npm, "run", "build"], cwd=web)


def find_pyinstaller() -> list[str]:
    """Prefer ``python -m PyInstaller`` from the current interpreter."""
    return [sys.executable, "-m", "PyInstaller"]


def build_exe() -> Path:
    spec = ROOT / "packaging" / "ArkPlots.spec"
    if not spec.is_file():
        raise SystemExit(f"missing spec: {spec}")
    dist_dir = ROOT / "dist"
    work_dir = ROOT / "build"
    _run(
        [
            *find_pyinstaller(),
            "--noconfirm",
            "--clean",
            f"--distpath={dist_dir}",
            f"--workpath={work_dir}",
            str(spec),
        ],
        cwd=ROOT,
    )
    built = dist_dir / f"{EXE_STEM}.exe"
    if not built.is_file():
        raise SystemExit(f"PyInstaller finished but {built} is missing")
    return built


def publish_release_alias(built: Path) -> Path:
    alias = ROOT / release_exe_name()
    shutil.copy2(built, alias)
    print(f"release alias -> {alias.name} ({alias.stat().st_size} bytes)", flush=True)
    return alias


def main() -> None:
    parser = argparse.ArgumentParser(description="Build ArkPlots release exe")
    parser.add_argument(
        "--skip-web",
        action="store_true",
        help="Skip npm run build (use existing web/dist)",
    )
    args = parser.parse_args()

    print(f"ArkPlots release build VERSION={VERSION}", flush=True)
    sync_frontend_version()
    if not args.skip_web:
        build_web()
    elif not (ROOT / "web" / "dist" / "index.html").is_file():
        raise SystemExit("web/dist missing; run without --skip-web")
    built = build_exe()
    publish_release_alias(built)
    print("done.", flush=True)


if __name__ == "__main__":
    main()
