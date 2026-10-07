#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a Windows installer from app_info.VERSION.

Steps:
  1. Sync ``web/src/version.ts`` from ``app_info.py``
  2. ``npm run build`` in web/
  3. PyInstaller onedir (no UPX) → ``dist/ArkPlots/``
  4. Inno Setup → ``Arkplot_setup_ver{VERSION}.exe``

Usage (from repo root):
  python packaging/build_release.py
  python packaging/build_release.py --skip-web
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app_info import (  # noqa: E402
    APP_NAME,
    EXE_STEM,
    GITHUB_REPO,
    VERSION,
    release_setup_name,
)


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


def parse_version_tuple(version: str) -> tuple[int, int, int, int]:
    parts: list[int] = []
    for piece in version.split("."):
        try:
            parts.append(int(piece))
        except ValueError:
            continue
    while len(parts) < 4:
        parts.append(0)
    return tuple(parts[:4])  # type: ignore[return-value]


def write_version_info() -> Path:
    """Windows VERSIONINFO — clear publisher metadata reduces SmartScreen suspicion."""
    dest = ROOT / "packaging" / "_version_info.txt"
    major, minor, patch, build = parse_version_tuple(VERSION)
    filevers = f"{major}, {minor}, {patch}, {build}"
    company = "ApodidaeDeSwift"
    copyright_ = "Copyright (C) 2024-2026 ApodidaeDeSwift"
    comments = f"Open-source Arknights plot tracker — https://github.com/{GITHUB_REPO}"
    dest.write_text(
        "\n".join(
            [
                "# UTF-8",
                "VSVersionInfo(",
                "  ffi=FixedFileInfo(",
                f"    filevers=({filevers}),",
                f"    prodvers=({filevers}),",
                "    mask=0x3F,",
                "    flags=0x0,",
                "    OS=0x40004,",
                "    fileType=0x1,",
                "    subtype=0x0,",
                "    date=(0, 0),",
                "  ),",
                "  kids=[",
                "    StringFileInfo([",
                "      StringTable('040904B0', [",
                f"        StringStruct('CompanyName', '{company}'),",
                f"        StringStruct('FileDescription', '{APP_NAME}'),",
                f"        StringStruct('FileVersion', '{VERSION}'),",
                f"        StringStruct('InternalName', '{EXE_STEM}'),",
                f"        StringStruct('LegalCopyright', '{copyright_}'),",
                f"        StringStruct('OriginalFilename', '{EXE_STEM}.exe'),",
                f"        StringStruct('ProductName', '{APP_NAME}'),",
                f"        StringStruct('ProductVersion', '{VERSION}'),",
                f"        StringStruct('Comments', '{comments}'),",
                "      ])",
                "    ]),",
                "    VarFileInfo([VarStruct('Translation', [1033, 1200])]),",
                "  ],",
                ")",
                "",
            ]
        ),
        encoding="utf-8",
        newline="\n",
    )
    print(f"wrote {dest.relative_to(ROOT)} for {VERSION}", flush=True)
    return dest


def _load_brand_icon_rgba():
    from PIL import Image

    src = ROOT / "icon.jpg"
    if not src.is_file():
        raise SystemExit("missing icon.jpg")
    img = Image.open(src).convert("RGBA")
    side = max(img.size)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(img, ((side - img.width) // 2, (side - img.height) // 2))
    return canvas


def sync_icon_ico() -> Path:
    """Rebuild icon.ico from icon.jpg so the exe uses the current artwork."""
    dest = ROOT / "icon.ico"
    try:
        canvas = _load_brand_icon_rgba()
    except SystemExit:
        if dest.is_file():
            return dest
        raise
    except ImportError as exc:
        if dest.is_file():
            print("Pillow missing; keeping existing icon.ico", flush=True)
            return dest
        raise SystemExit("Pillow is required to build icon.ico from icon.jpg") from exc

    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    canvas.save(dest, format="ICO", sizes=sizes)
    print(f"synced {dest.name} from icon.jpg", flush=True)
    return dest


def _fill_vertical_gradient(img, top_rgb: tuple[int, int, int], bottom_rgb: tuple[int, int, int]) -> None:
    """Draw a vertical gradient onto an RGB/RGBA image (in place)."""
    from PIL import ImageDraw

    draw = ImageDraw.Draw(img)
    w, h = img.size
    for y in range(h):
        t = y / max(h - 1, 1)
        r = int(top_rgb[0] * (1 - t) + bottom_rgb[0] * t)
        g = int(top_rgb[1] * (1 - t) + bottom_rgb[1] * t)
        b = int(top_rgb[2] * (1 - t) + bottom_rgb[2] * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b, 255) if img.mode == "RGBA" else (r, g, b))


def sync_wizard_images() -> tuple[Path, Path]:
    """Generate Inno Setup side/top images in the app dark-cyan look."""
    from PIL import Image, ImageDraw, ImageFont

    pack = ROOT / "packaging"
    side_path = pack / "wizard_side.png"
    top_path = pack / "wizard_top.png"
    brand = _load_brand_icon_rgba()

    # Large welcome/finish panel (modern wizard).
    side = Image.new("RGBA", (240, 480), (11, 18, 25, 255))
    _fill_vertical_gradient(side, (11, 18, 25), (22, 52, 58))
    draw = ImageDraw.Draw(side)
    # Accent bar
    draw.rectangle([0, 0, 4, 480], fill=(62, 199, 199, 255))
    # Soft glow circle behind icon
    draw.ellipse([28, 70, 212, 254], fill=(30, 70, 78, 90))
    icon = brand.resize((140, 140), Image.Resampling.LANCZOS)
    side.paste(icon, (50, 92), icon)
    try:
        font_title = ImageFont.truetype("segoeui.ttf", 28)
        font_sub = ImageFont.truetype("consola.ttf", 14)
    except OSError:
        font_title = ImageFont.load_default()
        font_sub = font_title
    draw.text((28, 280), "ArkPlots", fill=(215, 230, 239, 255), font=font_title)
    draw.text((28, 318), "PLOT TRACKER", fill=(62, 199, 199, 255), font=font_sub)
    draw.text((28, 350), f"v{VERSION}", fill=(138, 160, 178, 255), font=font_sub)
    draw.rectangle([28, 390, 100, 392], fill=(62, 199, 199, 255))
    side.save(side_path, format="PNG")

    # Small header image.
    top = Image.new("RGBA", (110, 110), (11, 18, 25, 255))
    _fill_vertical_gradient(top, (17, 27, 36), (22, 52, 58))
    tdraw = ImageDraw.Draw(top)
    tdraw.rectangle([0, 0, 110, 3], fill=(62, 199, 199, 255))
    small = brand.resize((78, 78), Image.Resampling.LANCZOS)
    top.paste(small, (16, 18), small)
    top.save(top_path, format="PNG")

    print(f"synced wizard images -> {side_path.name}, {top_path.name}", flush=True)
    return side_path, top_path


def find_pyinstaller() -> list[str]:
    """Prefer ``python -m PyInstaller`` from the current interpreter."""
    return [sys.executable, "-m", "PyInstaller"]


def build_exe() -> Path:
    """Build onedir payload at ``dist/ArkPlots/ArkPlots.exe`` (no UPX, not onefile)."""
    spec = ROOT / "packaging" / "ArkPlots.spec"
    if not spec.is_file():
        raise SystemExit(f"missing spec: {spec}")
    dist_dir = ROOT / "dist"
    work_dir = ROOT / "build"
    # Remove stale onefile leftovers from older packaging so the installer
    # cannot accidentally pick up a packed single-file exe.
    stale_onefile = dist_dir / f"{EXE_STEM}.exe"
    if stale_onefile.is_file():
        stale_onefile.unlink()
    # UPX is disabled inside ArkPlots.spec (upx=False). Do not pass --noupx
    # here: PyInstaller rejects makespec flags when a .spec file is given.
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
    built = dist_dir / EXE_STEM / f"{EXE_STEM}.exe"
    if not built.is_file():
        raise SystemExit(f"PyInstaller finished but {built} is missing")
    return built


def find_iscc() -> Path:
    """Locate Inno Setup compiler (ISCC.exe)."""
    which = shutil.which("iscc") or shutil.which("ISCC")
    if which:
        return Path(which)
    pf = os.environ.get("ProgramFiles(x86)") or os.environ.get("ProgramFiles") or ""
    pf64 = os.environ.get("ProgramFiles") or ""
    candidates = [
        Path(pf) / "Inno Setup 6" / "ISCC.exe",
        Path(pf64) / "Inno Setup 6" / "ISCC.exe",
        Path(pf) / "Inno Setup 5" / "ISCC.exe",
    ]
    for path in candidates:
        if path.is_file():
            return path
    raise SystemExit(
        "Inno Setup compiler (ISCC.exe) not found. Install Inno Setup 6 "
        "(https://jrsoftware.org/isinfo.php) or `choco install innosetup`."
    )


def build_installer() -> Path:
    plotline = ROOT / "Plotline.json"
    if not plotline.is_file():
        raise SystemExit("Plotline.json missing; installer needs it for first-time installs")
    payload_dir = ROOT / "dist" / EXE_STEM
    if not (payload_dir / f"{EXE_STEM}.exe").is_file():
        raise SystemExit(f"missing onedir payload: {payload_dir}")
    spec = ROOT / "packaging" / "ArkPlots.iss"
    if not spec.is_file():
        raise SystemExit(f"missing installer script: {spec}")
    iscc = find_iscc()
    _run(
        [
            str(iscc),
            f"/DMyAppVersion={VERSION}",
            str(spec),
        ],
        cwd=ROOT,
    )
    setup = ROOT / release_setup_name()
    if not setup.is_file():
        raise SystemExit(f"Inno Setup finished but {setup.name} is missing")
    print(f"installer -> {setup.name} ({setup.stat().st_size} bytes)", flush=True)
    print(
        "Note: unsigned installers may still trigger SmartScreen until the "
        "build has reputation or is code-signed. Submit false positives at "
        "https://www.microsoft.com/wdsi/filesubmission",
        flush=True,
    )
    return setup


def main() -> None:
    parser = argparse.ArgumentParser(description="Build ArkPlots Windows installer")
    parser.add_argument(
        "--skip-web",
        action="store_true",
        help="Skip npm run build (use existing web/dist)",
    )
    args = parser.parse_args()

    print(f"ArkPlots release build VERSION={VERSION}", flush=True)
    if VERSION.startswith("1.0."):
        raise SystemExit(
            f"Refusing to pack VERSION={VERSION}. Use the calendar build in app_info.py "
            "(e.g. 26.10.5.1), not a leftover 1.0.x from the old main-branch exe."
        )
    sync_frontend_version()
    write_version_info()
    sync_icon_ico()
    sync_wizard_images()
    if not args.skip_web:
        build_web()
    elif not (ROOT / "web" / "dist" / "index.html").is_file():
        raise SystemExit("web/dist missing; run without --skip-web")
    built = build_exe()
    print(f"payload exe -> {built}", flush=True)
    setup = build_installer()
    print("done.", flush=True)


if __name__ == "__main__":
    main()
