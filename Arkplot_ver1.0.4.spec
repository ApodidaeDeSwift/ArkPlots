# -*- mode: python ; coding: utf-8 -*-
# No console window: console=False below is what PyInstaller uses.
# When this .spec is passed, CLI flags --noconsole / --windowed are ignored.
# Equivalent command:
#   pyinstaller --noconsole --windowed Arkplot_ver1.0.4.spec
#
# Plotline.json / Read_record.json are NOT bundled; runtime reads them from
# the directory containing the .exe (see get_app_dir in main.py / server.py).

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules


def _dynlibs(package: str):
    try:
        return collect_dynamic_libs(package)
    except Exception:
        return []


binaries = _dynlibs("webview") + _dynlibs("pythonnet") + _dynlibs("clr_loader")
datas = [
    ("web/dist", "web/dist"),
    ("icon.ico", "."),
]
datas += collect_data_files("webview", subdir="lib")
datas += collect_data_files("webview", subdir="js")

hiddenimports = ["server", "clr", "pythonnet", "clr_loader"] + collect_submodules("webview")

a = Analysis(
    ["main.py"],
    pathex=[],
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
    name="Arkplot_ver1.0.4",
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
    icon=["icon.ico"],
)
