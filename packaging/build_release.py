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


def _draw_hazard_stripe_band(
    draw,
    box: tuple[int, int, int, int],
    *,
    color_a=(255, 159, 26, 255),
    color_b=(18, 18, 18, 255),
    stripe_w: int = 10,
) -> None:
    """Diagonal hazard stripes (Arknights / industrial look)."""
    x0, y0, x1, y1 = box
    # Cover the band with alternating diagonals.
    for offset in range(-((y1 - y0) + (x1 - x0)), (x1 - x0) + (y1 - y0), stripe_w * 2):
        points = [
            (x0 + offset, y0),
            (x0 + offset + stripe_w, y0),
            (x0 + offset + stripe_w - (y1 - y0), y1),
            (x0 + offset - (y1 - y0), y1),
        ]
        draw.polygon(points, fill=color_a)
        points_b = [
            (x0 + offset + stripe_w, y0),
            (x0 + offset + stripe_w * 2, y0),
            (x0 + offset + stripe_w * 2 - (y1 - y0), y1),
            (x0 + offset + stripe_w - (y1 - y0), y1),
        ]
        draw.polygon(points_b, fill=color_b)
    # Clip visually with outer frame redraw by caller if needed.


def _draw_corner_brackets(draw, box: tuple[int, int, int, int], color, arm: int = 18, thick: int = 2) -> None:
    x0, y0, x1, y1 = box
    # Top-left
    draw.rectangle([x0, y0, x0 + arm, y0 + thick], fill=color)
    draw.rectangle([x0, y0, x0 + thick, y0 + arm], fill=color)
    # Top-right
    draw.rectangle([x1 - arm, y0, x1, y0 + thick], fill=color)
    draw.rectangle([x1 - thick, y0, x1, y0 + arm], fill=color)
    # Bottom-left
    draw.rectangle([x0, y1 - thick, x0 + arm, y1], fill=color)
    draw.rectangle([x0, y1 - arm, x0 + thick, y1], fill=color)
    # Bottom-right
    draw.rectangle([x1 - arm, y1 - thick, x1, y1], fill=color)
    draw.rectangle([x1 - thick, y1 - arm, x1, y1], fill=color)


def sync_wizard_images() -> tuple[Path, Path, Path]:
    """Generate industrial (Arknights-like) Inno Setup wizard art."""
    from PIL import Image, ImageDraw, ImageFont

    pack = ROOT / "packaging"
    side_path = pack / "wizard_side.png"
    top_path = pack / "wizard_top.png"
    back_path = pack / "wizard_back.png"
    brand = _load_brand_icon_rgba()

    amber = (255, 159, 26, 255)
    amber_dim = (180, 100, 20, 255)
    ink = (10, 12, 16, 255)
    panel = (22, 24, 28, 255)
    text = (245, 245, 245, 255)
    text_dim = (200, 200, 200, 255)

    try:
        font_title = ImageFont.truetype("segoeuib.ttf", 26)
        font_sub = ImageFont.truetype("consola.ttf", 13)
        font_tiny = ImageFont.truetype("consola.ttf", 11)
    except OSError:
        try:
            font_title = ImageFont.truetype("segoeui.ttf", 26)
            font_sub = ImageFont.truetype("consola.ttf", 13)
            font_tiny = font_sub
        except OSError:
            font_title = ImageFont.load_default()
            font_sub = font_title
            font_tiny = font_title

    # --- Side panel (welcome / finished) ---
    side = Image.new("RGBA", (240, 480), ink)
    _fill_vertical_gradient(side, (10, 12, 16), (28, 30, 34))
    draw = ImageDraw.Draw(side)
    # Hazard band at top
    draw.rectangle([0, 0, 240, 22], fill=(18, 18, 18, 255))
    _draw_hazard_stripe_band(draw, (0, 0, 240, 22), stripe_w=9)
    # Metal panel behind icon
    draw.rectangle([24, 48, 216, 248], fill=panel)
    _draw_corner_brackets(draw, (24, 48, 216, 248), amber, arm=16, thick=2)
    icon = brand.resize((132, 132), Image.Resampling.LANCZOS)
    side.paste(icon, (54, 82), icon)
    # Caption block
    draw.rectangle([24, 268, 216, 272], fill=amber)
    draw.text((28, 288), "ArkPlots", fill=text, font=font_title)
    draw.text((28, 324), "INDUSTRIAL  DEPLOY", fill=amber, font=font_sub)
    draw.text((28, 350), f"BUILD  {VERSION}", fill=text_dim, font=font_tiny)
    draw.text((28, 380), "PLOTLINE / LOCAL", fill=text_dim, font=font_tiny)
    # Bottom hazard strip
    draw.rectangle([0, 458, 240, 480], fill=(18, 18, 18, 255))
    _draw_hazard_stripe_band(draw, (0, 458, 240, 480), stripe_w=9)
    side.save(side_path, format="PNG")

    # --- Small header image ---
    top = Image.new("RGBA", (110, 110), ink)
    _fill_vertical_gradient(top, (10, 12, 16), (30, 32, 36))
    tdraw = ImageDraw.Draw(top)
    tdraw.rectangle([0, 0, 110, 14], fill=(18, 18, 18, 255))
    _draw_hazard_stripe_band(tdraw, (0, 0, 110, 14), stripe_w=7)
    _draw_corner_brackets(tdraw, (8, 22, 102, 102), amber, arm=12, thick=2)
    small = brand.resize((68, 68), Image.Resampling.LANCZOS)
    top.paste(small, (21, 28), small)
    top.save(top_path, format="PNG")

    # --- Soft page background (grid + faint stripes) ---
    back = Image.new("RGBA", (640, 480), (10, 12, 16, 255))
    bdraw = ImageDraw.Draw(back)
    for x in range(0, 640, 32):
        bdraw.line([(x, 0), (x, 480)], fill=(40, 42, 46, 255))
    for y in range(0, 480, 32):
        bdraw.line([(0, y), (640, y)], fill=(40, 42, 46, 255))
    # Faint amber corner marks
    _draw_corner_brackets(bdraw, (12, 12, 628, 468), amber_dim, arm=28, thick=2)
    back.save(back_path, format="PNG")

    print(
        f"synced wizard images -> {side_path.name}, {top_path.name}, {back_path.name}",
        flush=True,
    )
    return side_path, top_path, back_path


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


def find_signtool() -> Path | None:
    which = shutil.which("signtool") or shutil.which("signtool.exe")
    if which:
        return Path(which)
    kits = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Windows Kits" / "10" / "bin"
    if kits.is_dir():
        candidates = sorted(kits.glob("*/x64/signtool.exe"), reverse=True)
        if candidates:
            return candidates[0]
    return None


def sign_file(path: Path) -> bool:
    """Authenticode-sign ``path`` when SIGN_PFX / SIGN_PFX_PASSWORD are set.

    Without a certificate, SmartScreen will keep showing「发布者未知」.
    See packaging/SIGNING.md.
    """
    pfx = os.environ.get("SIGN_PFX", "").strip()
    password = os.environ.get("SIGN_PFX_PASSWORD", "")
    if not pfx:
        return False
    pfx_path = Path(pfx)
    if not pfx_path.is_file():
        raise SystemExit(f"SIGN_PFX not found: {pfx_path}")
    signtool = find_signtool()
    if signtool is None:
        raise SystemExit(
            "signtool.exe not found. Install Windows SDK Signing Tools, "
            "or put signtool on PATH."
        )
    cmd = [
        str(signtool),
        "sign",
        "/fd",
        "SHA256",
        "/tr",
        os.environ.get("SIGN_TIMESTAMP_URL", "http://timestamp.digicert.com"),
        "/td",
        "SHA256",
        "/f",
        str(pfx_path),
    ]
    if password:
        cmd.extend(["/p", password])
    cmd.append(str(path))
    # Avoid echoing the password in logs.
    print(f"+ signtool sign … {path.name}", flush=True)
    subprocess.check_call(cmd, cwd=str(ROOT))
    print(f"signed {path.name}", flush=True)
    return True


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

    # Sign payload exe first so installed files show a publisher when cert is present.
    payload_exe = payload_dir / f"{EXE_STEM}.exe"
    if not sign_file(payload_exe):
        print(
            "skip code-sign (set SIGN_PFX + SIGN_PFX_PASSWORD to enable). "
            "Unsigned builds show SmartScreen「发布者未知」.",
            flush=True,
        )

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
    sign_file(setup)
    print(f"installer -> {setup.name} ({setup.stat().st_size} bytes)", flush=True)
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
