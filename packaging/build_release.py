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
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

# GitHub Actions Windows runners often use cp1252 for stdout; avoid UnicodeEncodeError.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except Exception:
        pass

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app_info import (  # noqa: E402
    APP_NAME,
    CHANNEL,
    EXE_STEM,
    GITHUB_REPO,
    VERSION,
    release_setup_name,
)


def _run(cmd: list[str], cwd: Path) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.check_call(cmd, cwd=str(cwd))


def sync_frontend_version() -> None:
    from sync_frontend_version import sync_frontend_version as write_version_ts

    path = write_version_ts()
    print(f"synced {path.relative_to(ROOT)} -> {VERSION} {CHANNEL}", flush=True)


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


def _blend_radial_glow(
    img,
    cx: float,
    cy: float,
    radius: float,
    color: tuple[int, int, int],
    strength: float = 0.22,
) -> None:
    """Soft radial wash matching the in-app background glows."""
    from PIL import Image, ImageDraw

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    steps = max(12, int(radius / 18))
    for i in range(steps, 0, -1):
        t = i / steps
        a = int(255 * strength * (t**2))
        r = radius * t
        draw.ellipse(
            [cx - r, cy - r, cx + r, cy + r],
            fill=(color[0], color[1], color[2], a),
        )
    img.alpha_composite(overlay)


def _load_wizard_fonts():
    from PIL import ImageFont

    def load(path: str, size: int, index: int = 0):
        return ImageFont.truetype(path, size, index=index)

    pairs = [
        ("C:/Windows/Fonts/msyhbd.ttc", "C:/Windows/Fonts/msyh.ttc"),
        ("msyhbd.ttc", "msyh.ttc"),
    ]
    for bold, regular in pairs:
        try:
            return load(bold, 28), load(regular, 16), load(regular, 14)
        except OSError:
            continue
    fallback = ImageFont.load_default()
    return fallback, fallback, fallback


def sync_wizard_images() -> tuple[Path, Path, Path]:
    """Generate the installer's side and header art as deep-blue rounded cards."""
    from PIL import Image, ImageDraw

    pack = ROOT / "packaging"
    side_path = pack / "wizard_side.png"
    top_path = pack / "wizard_top.png"
    back_path = pack / "wizard_back.png"
    brand = _load_brand_icon_rgba()

    bg0 = (11, 18, 25)
    bg1 = (17, 27, 36)
    panel = (22, 34, 48, 255)
    header = (27, 43, 58, 255)
    accent = (110, 184, 232, 255)
    text = (215, 230, 239, 255)
    text_dim = (138, 160, 178, 255)
    font_title, font_body, font_tiny = _load_wizard_fonts()

    side = Image.new("RGBA", (240, 480), (*bg0, 255))
    _fill_vertical_gradient(side, bg0, bg1)
    _blend_radial_glow(side, 36, -10, 200, (110, 184, 232), 0.22)
    _blend_radial_glow(side, 210, 120, 160, (62, 140, 196), 0.16)
    draw = ImageDraw.Draw(side)
    draw.rounded_rectangle([18, 28, 222, 452], radius=28, fill=panel)
    draw.rounded_rectangle([36, 52, 204, 220], radius=24, fill=header)
    icon = brand.resize((112, 112), Image.Resampling.LANCZOS)
    side.paste(icon, (64, 80), icon)
    draw.rounded_rectangle([36, 244, 78, 248], radius=2, fill=accent)
    draw.text((36, 264), "ArkPlots", fill=text, font=font_title)
    draw.text((36, 308), "剧情情报站", fill=accent, font=font_body)
    draw.text((36, 338), f"版本  {VERSION}", fill=text_dim, font=font_tiny)
    draw.text((36, 392), "阅读进度会留在", fill=text, font=font_tiny)
    draw.text((36, 414), "安装目录里", fill=text, font=font_tiny)
    side.save(side_path, format="PNG")

    top = Image.new("RGBA", (110, 110), (*bg0, 255))
    _fill_vertical_gradient(top, bg0, bg1)
    _blend_radial_glow(top, 20, 8, 80, (110, 184, 232), 0.24)
    tdraw = ImageDraw.Draw(top)
    tdraw.rounded_rectangle([8, 8, 102, 102], radius=22, fill=panel)
    small = brand.resize((68, 68), Image.Resampling.LANCZOS)
    top.paste(small, (21, 21), small)
    top.save(top_path, format="PNG")

    back = Image.new("RGBA", (640, 480), (*bg0, 255))
    _fill_vertical_gradient(back, bg0, (14, 23, 32))
    _blend_radial_glow(back, 80, -40, 420, (110, 184, 232), 0.16)
    _blend_radial_glow(back, 560, 40, 360, (62, 140, 196), 0.12)
    bdraw = ImageDraw.Draw(back)
    bdraw.rounded_rectangle([16, 16, 624, 464], radius=28, outline=accent, width=2)
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

    Without a certificate, SmartScreen shows publisher unknown.
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
    print(f"+ signtool sign ... {path.name}", flush=True)
    subprocess.check_call(cmd, cwd=str(ROOT))
    print(f"signed {path.name}", flush=True)
    return True


def sha256_of(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_checksum_sidecar(path: Path) -> Path:
    """``<file>.sha256`` next to the artifact; the in-app updater verifies it."""
    sidecar = path.with_name(path.name + ".sha256")
    sidecar.write_text(f"{sha256_of(path)}  {path.name}\n", encoding="ascii", newline="\n")
    print(f"checksum -> {sidecar.name}", flush=True)
    return sidecar


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
            "Unsigned builds show SmartScreen publisher unknown.",
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
    # Checksum is computed after signing so it always matches the shipped bytes.
    write_checksum_sidecar(setup)
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
