# -*- mode: python ; coding: utf-8 -*-
"""Stable PyInstaller spec for ArkPlots (APP_Release).

- Builds ``ArkPlots.exe`` (stable name for future in-place updates).
- ``console=False`` → no console window.
- Version / product metadata come from ``app_info.py`` (repo root).
- ``Plotline.json`` / ``Read_record.json`` are NOT bundled.

Prefer: ``python scripts/build_release.py``
"""

import os
import sys

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

# SPECPATH is injected by PyInstaller: directory containing this .spec file.
_ROOT = os.path.abspath(os.path.join(SPECPATH, os.pardir))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from app_info import EXE_STEM  # noqa: E402


def _dynlibs(package: str):
    try:
        return collect_dynamic_libs(package)
    except Exception:
        return []


binaries = _dynlibs("webview") + _dynlibs("pythonnet") + _dynlibs("clr_loader")
datas = [
    (os.path.join(_ROOT, "web", "dist"), "web/dist"),
    (os.path.join(_ROOT, "icon.ico"), "."),
]
datas += collect_data_files("webview", subdir="lib")
datas += collect_data_files("webview", subdir="js")

hiddenimports = [
    "server",
    "app_info",
    "updater",
    "clr",
    "pythonnet",
    "clr_loader",
] + collect_submodules("webview")

a = Analysis(
    [os.path.join(_ROOT, "main.py")],
    pathex=[_ROOT],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=EXE_STEM,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[os.path.join(_ROOT, "icon.ico")],
)
