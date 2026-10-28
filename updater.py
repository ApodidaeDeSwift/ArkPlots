# -*- coding: utf-8 -*-
"""Check GitHub APP_Ver* tags and apply in-place exe updates.

Update source: tags named ``APP_VerYY.M.D.N`` on ApodidaeDeSwift/ArkPlots
(e.g. ``APP_Ver26.9.26.2`` = 2026-09-26, 2nd build that day). The updater
lists those tags, picks the highest version, and downloads that release's
``.exe`` asset when it is newer than the installed build. If the REST API
is rate-limited or unreachable, the same check falls back to the public
releases feed and asset page, which do not share that API quota.

Only the running executable (and optional stable ``ArkPlots.exe`` twin) is
replaced. User data beside the exe (Plotline.json, Read_record.json, covers,
etc.) is never deleted or overwritten by the updater.
"""
from __future__ import annotations

import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import quote, unquote

from app_info import (
    EXE_STEM,
    GITHUB_REPO,
    UPDATE_TAG_PREFIX,
    VERSION,
    is_packaged,
    release_exe_name,
    release_setup_name,
    version_payload,
)

RELEASES_HTML_URL = f"https://github.com/{GITHUB_REPO}/releases"
RELEASES_ATOM_URL = f"https://github.com/{GITHUB_REPO}/releases.atom"
RELEASES_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
TAGS_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/tags"
_ATOM_NS = "{http://www.w3.org/2005/Atom}"
RELEASE_BY_TAG_API = (
    f"https://api.github.com/repos/{GITHUB_REPO}/releases/tags/{{tag}}"
)

# Shown whenever the user checks / applies updates.
OVERSEAS_SOURCE_WARNING_ZH = (
    "现阶段更新只支持海外源（GitHub）。在没有梯子 / 稳定代理的情况下，"
    "检查与下载未必稳定，请耐心重试或稍后再试。"
)
OVERSEAS_SOURCE_WARNING_EN = (
    "Updates currently use an overseas source (GitHub) only. "
    "Without a VPN / stable proxy, checking or downloading may be unreliable."
)

_USER_AGENT = f"ArkPlots-Updater/{VERSION} (+https://github.com/{GITHUB_REPO})"

# Files / dirs the updater may create. Everything else in the app directory
# (Plotline.json, Read_record.json, covers/, etc.) is left untouched.
_UPDATE_DIR_NAME = "_update"

# Match APP_Ver26.9.26.2 (optional underscore after Ver).
_APP_VER_TAG_RE = re.compile(
    rf"^{re.escape(UPDATE_TAG_PREFIX)}_?(\d+(?:\.\d+){{1,3}})$",
    re.IGNORECASE,
)


def parse_version(text: str | None) -> tuple[int, ...] | None:
    """Extract ``a.b.c.d`` (or shorter) from a tag / release / asset name."""
    if not text:
        return None
    m = re.search(r"(\d+(?:\.\d+){1,3})", str(text))
    if not m:
        return None
    parts = tuple(int(x) for x in m.group(1).split("."))
    padded = parts + (0,) * (4 - len(parts))
    return padded[:4]


def parse_app_ver_tag(tag_name: str | None) -> tuple[int, ...] | None:
    """Parse version only from ``APP_Ver*`` tags; ignore other tags."""
    if not tag_name:
        return None
    m = _APP_VER_TAG_RE.match(str(tag_name).strip())
    if not m:
        return None
    return parse_version(m.group(1))


def version_tuple_to_str(ver: tuple[int, ...]) -> str:
    return ".".join(str(x) for x in ver)


def compare_versions(a: tuple[int, ...], b: tuple[int, ...]) -> int:
    if a < b:
        return -1
    if a > b:
        return 1
    return 0


def _http_json(url: str, timeout: float = 25.0) -> Any:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": _USER_AGENT,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    return json.loads(raw.decode("utf-8"))


def _http_text(url: str, accept: str, timeout: float = 20.0) -> str:
    """GET a public GitHub page. Unlike ``_http_json``, this does not use the API."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": _USER_AGENT,
            "Accept": accept,
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _html_to_notes(fragment: str) -> str:
    """Turn a release-page HTML fragment into text the notes view can show."""
    text = fragment.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"(?is)<br\s*/?>", "\n", text)
    text = re.sub(r"(?is)</p\s*>", "\n\n", text)
    text = re.sub(r"(?is)</h[1-6]\s*>", "\n\n", text)
    text = re.sub(r"(?is)<li[^>]*>", "\n- ", text)
    text = re.sub(r"(?is)</li\s*>", "", text)

    def _link(match: re.Match[str]) -> str:
        href = html.unescape(match.group(1)).strip()
        label = re.sub(r"(?is)<[^>]+>", "", match.group(2))
        label = html.unescape(label).strip()
        if not label or label == href:
            return href
        return f"{label} ({href})"

    text = re.sub(
        r'(?is)<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
        _link,
        text,
    )
    text = re.sub(r"(?is)<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return _clip_notes(text)


def _tag_from_release_link(title: str, link: str) -> str | None:
    if parse_app_ver_tag(title):
        return title.strip()
    marker = "/releases/tag/"
    if marker in link:
        tag = unquote(link.split(marker, 1)[1].split("/", 1)[0].strip())
        if parse_app_ver_tag(tag):
            return tag
    return None


def _assets_from_expanded_page(tag_name: str) -> list[dict[str, Any]]:
    """Installer links from the public expanded-assets fragment."""
    url = (
        f"https://github.com/{GITHUB_REPO}/releases/expanded_assets/"
        f"{quote(tag_name, safe='')}"
    )
    page = _http_text(url, "text/html, */*;q=0.8")
    assets: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw_href in re.findall(r'href="([^"]+\.(?:exe|sha256))"', page, flags=re.IGNORECASE):
        href = html.unescape(raw_href).strip()
        if href.startswith("/"):
            href = "https://github.com" + href
        elif not href.startswith("http"):
            continue
        name = unquote(href.split("?", 1)[0].rstrip("/").rsplit("/", 1)[-1])
        key = href.lower()
        if not name or key in seen:
            continue
        seen.add(key)
        assets.append({"name": name, "browser_download_url": href, "size": None})
    return assets


def _releases_from_public_feed() -> list[tuple[str, tuple[int, ...], dict[str, Any]]]:
    """``APP_Ver*`` entries from the public releases Atom feed (no API quota)."""
    xml = _http_text(
        RELEASES_ATOM_URL,
        "application/atom+xml, application/xml;q=0.9, */*;q=0.8",
    )
    root = ET.fromstring(xml)
    found: list[tuple[str, tuple[int, ...], dict[str, Any]]] = []
    for entry in root.findall(f"{_ATOM_NS}entry"):
        title = (entry.findtext(f"{_ATOM_NS}title") or "").strip()
        link = ""
        for link_el in entry.findall(f"{_ATOM_NS}link"):
            href = link_el.get("href") or ""
            rel = link_el.get("rel") or "alternate"
            if href and rel == "alternate":
                link = href
                break
        tag_name = _tag_from_release_link(title, link)
        ver = parse_app_ver_tag(tag_name)
        if tag_name is None or ver is None:
            continue
        content_el = entry.find(f"{_ATOM_NS}content")
        body = ""
        if content_el is not None:
            body = _html_to_notes("".join(content_el.itertext()))
        html_url = link or (
            f"https://github.com/{GITHUB_REPO}/releases/tag/{quote(tag_name, safe='')}"
        )
        found.append(
            (
                tag_name,
                ver,
                {
                    "tag_name": tag_name,
                    "name": title or tag_name,
                    "body": body,
                    "html_url": html_url,
                    "draft": False,
                    "assets": [],
                },
            )
        )
    return found


def _stable_release_tag() -> str | None:
    """Tag of GitHub's latest non-prerelease, from the ``/releases/latest`` redirect."""
    url = f"https://github.com/{GITHUB_REPO}/releases/latest"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": _USER_AGENT, "Accept": "text/html, */*;q=0.8"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        final = resp.geturl()
    marker = "/releases/tag/"
    if marker not in final:
        return None
    tag = unquote(final.split(marker, 1)[1].split("/", 1)[0].split("?", 1)[0].strip())
    if parse_app_ver_tag(tag) is None:
        return None
    return tag


def _latest_from_public_feed(
    include_prerelease: bool = False,
) -> tuple[str, tuple[int, ...], dict[str, Any]] | None:
    """Newest public ``APP_Ver*`` release, or None if the feed cannot be read.

    ``include_prerelease`` False follows GitHub's latest stable release.
    True uses the highest ``APP_Ver*`` entry in the public feed, pre-releases
    included.
    """
    try:
        found = _releases_from_public_feed()
    except Exception:
        return None
    if not found:
        return None
    if include_prerelease:
        chosen = max(found, key=lambda item: item[1])
    else:
        try:
            stable_tag = _stable_release_tag()
        except Exception:
            return None
        if not stable_tag:
            return None
        matched = [item for item in found if item[0] == stable_tag]
        if matched:
            chosen = matched[0]
        else:
            ver = parse_app_ver_tag(stable_tag)
            if ver is None:
                return None
            chosen = (
                stable_tag,
                ver,
                {
                    "tag_name": stable_tag,
                    "name": stable_tag,
                    "body": "",
                    "html_url": (
                        f"https://github.com/{GITHUB_REPO}/releases/tag/"
                        f"{quote(stable_tag, safe='')}"
                    ),
                    "draft": False,
                    "prerelease": False,
                    "assets": [],
                },
            )
    tag_name, remote, release = chosen
    try:
        release["assets"] = _assets_from_expanded_page(tag_name)
    except Exception:
        release["assets"] = []
    return tag_name, remote, release


def _list_app_ver_from_releases(
    per_page: int = 100, max_pages: int = 10
) -> list[tuple[str, tuple[int, ...], dict[str, Any]]]:
    """Scan published releases whose tag matches ``APP_Ver*``."""
    found: list[tuple[str, tuple[int, ...], dict[str, Any]]] = []
    for page in range(1, max_pages + 1):
        url = f"{RELEASES_API_URL}?per_page={per_page}&page={page}"
        batch = _http_json(url)
        if not isinstance(batch, list) or not batch:
            break
        for item in batch:
            if not isinstance(item, dict):
                continue
            if item.get("draft"):
                continue
            # Pre-release filtering happens in check_for_update so a caller
            # can ask for 测试版 (include) or 正式版 (skip) from the same list.
            tag = str(item.get("tag_name") or "")
            ver = parse_app_ver_tag(tag)
            if ver is not None:
                found.append((tag, ver, item))
        if len(batch) < per_page:
            break
    return found


def _list_app_ver_tags(per_page: int = 100, max_pages: int = 10) -> list[tuple[str, tuple[int, ...]]]:
    """Return ``(tag_name, version_tuple)`` for every ``APP_Ver*`` tag found."""
    found: list[tuple[str, tuple[int, ...]]] = []
    for page in range(1, max_pages + 1):
        url = f"{TAGS_API_URL}?per_page={per_page}&page={page}"
        batch = _http_json(url)
        if not isinstance(batch, list) or not batch:
            break
        for item in batch:
            name = str((item or {}).get("name") or "")
            ver = parse_app_ver_tag(name)
            if ver is not None:
                found.append((name, ver))
        if len(batch) < per_page:
            break
    return found


def _fetch_release_for_tag(tag_name: str) -> dict[str, Any]:
    url = RELEASE_BY_TAG_API.format(tag=quote(tag_name, safe=""))
    return _http_json(url)


def _pick_exe_asset(assets: list[dict[str, Any]], remote_version: str) -> dict[str, Any] | None:
    if not assets:
        return None
    exes = [
        a
        for a in assets
        if str(a.get("name", "")).lower().endswith(".exe") and a.get("browser_download_url")
    ]
    if not exes:
        return None
    preferred_setup = release_setup_name(remote_version).lower()
    for a in exes:
        if str(a.get("name", "")).lower() == preferred_setup:
            return a
    for a in exes:
        name = str(a.get("name", "")).lower()
        if "setup" in name and name.startswith("arkplot"):
            return a
    preferred = release_exe_name(remote_version).lower()
    for a in exes:
        if str(a.get("name", "")).lower() == preferred:
            return a
    for a in exes:
        name = str(a.get("name", "")).lower()
        if name.startswith("arkplot_ver") or name == f"{EXE_STEM.lower()}.exe":
            return a
    return exes[0]


def _asset_is_installer(name: str) -> bool:
    n = name.lower()
    return "setup" in n or n.startswith("arkplot_setup")


_CHECKSUM_ASSET_NAMES = ("checksums.txt", "checksums.sha256", "sha256sums.txt")


def _find_checksum(
    assets: list[dict[str, Any]], asset_name: str
) -> dict[str, Any] | None:
    """The ``<exe>.sha256`` asset published beside the installer, or a checksums.txt.

    Releases without any checksum asset keep working (verification is skipped),
    so old releases stay updatable.
    """
    if not asset_name:
        return None
    wanted = f"{asset_name.lower()}.sha256"
    checksums: dict[str, Any] | None = None
    for asset in assets:
        name = str(asset.get("name", "")).lower()
        url = asset.get("browser_download_url")
        if not url:
            continue
        if name == wanted:
            return asset
        if name in _CHECKSUM_ASSET_NAMES and checksums is None:
            checksums = asset
    return checksums


def _extract_sha256(text: str, asset_name: str) -> str | None:
    """First 64-hex digest in a checksum file, preferring the asset's own line."""
    wanted = asset_name.lower()
    fallback: str | None = None
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.search(r"\b([0-9a-fA-F]{64})\b", line)
        if not m:
            continue
        digest = m.group(1).lower()
        if wanted in line.lower():
            return digest
        if fallback is None:
            fallback = digest
    return fallback


def _fetch_checksum_hex(url: str, asset_name: str, timeout: float = 20.0) -> str | None:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": _USER_AGENT, "Accept": "text/plain, */*;q=0.8"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        text = resp.read(64 * 1024).decode("utf-8", errors="replace")
    return _extract_sha256(text, asset_name)


def _sha256_file(path: str, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _discard_download(path: str) -> None:
    for victim in (path, path + ".partial"):
        try:
            if os.path.isfile(victim):
                os.remove(victim)
        except OSError:
            pass


_NOTES_LIMIT = 100_000
_update_exit_armed = False


def _clip_notes(text: str) -> str:
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff").strip()
    if len(cleaned) > _NOTES_LIMIT:
        cleaned = cleaned[:_NOTES_LIMIT].rstrip() + "\n…"
    return cleaned


def _release_notes_text(release: dict[str, Any] | None) -> str:
    """GitHub release ``body`` (Markdown), or an empty string."""
    if not isinstance(release, dict):
        return ""
    body = release.get("body")
    if not isinstance(body, str):
        return ""
    return _clip_notes(body)


_UPDATE_MD_NAME = "Update.md"


def update_markdown_path() -> str | None:
    """Local ``Update.md``: frozen bundle, then the directory next to the program."""
    candidates: list[str] = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(os.path.join(meipass, _UPDATE_MD_NAME))
    candidates.append(os.path.join(_app_dir(), _UPDATE_MD_NAME))
    here = os.path.join(os.path.dirname(os.path.abspath(__file__)), _UPDATE_MD_NAME)
    if here not in candidates:
        candidates.append(here)
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


_VERSION_MARK = "{{VERSION}}"


def render_update_markdown(text: str, version: str | None = None) -> str:
    """Fill ``{{VERSION}}`` so Update.md does not store the version number."""
    ver = (version or VERSION).strip()
    return text.replace(_VERSION_MARK, ver)


def read_local_update_markdown() -> str:
    path = update_markdown_path()
    if not path:
        return ""
    try:
        with open(path, encoding="utf-8") as handle:
            return _clip_notes(render_update_markdown(handle.read()))
    except OSError:
        return ""


def fetch_tagged_update_markdown(tag_name: str | None) -> str:
    """``Update.md`` committed on a GitHub tag, or an empty string."""
    tag = (tag_name or "").strip()
    if not tag:
        return ""
    url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{quote(tag, safe='')}/Update.md"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": _USER_AGENT,
            "Accept": "text/plain, text/markdown;q=0.9, */*;q=0.8",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read()
    except Exception:
        return ""
    text = raw.decode("utf-8", errors="replace")
    parsed = parse_version(tag)
    version = ".".join(str(part) for part in parsed) if parsed else None
    return _clip_notes(render_update_markdown(text, version))


def update_announcement(tag_name: str | None = None) -> str:
    """Post-update notice: ``Update.md`` on that tag, otherwise the local file."""
    remote = fetch_tagged_update_markdown(tag_name)
    if remote:
        return remote
    return read_local_update_markdown()


def _base_error(error: str, message: str, **extra: Any) -> dict[str, Any]:
    return {
        "ok": False,
        "error": error,
        "message": message,
        "warning": OVERSEAS_SOURCE_WARNING_ZH,
        "warning_en": OVERSEAS_SOURCE_WARNING_EN,
        "current": version_payload(),
        "html_url": RELEASES_HTML_URL,
        **extra,
    }


def _accept_release(release: dict[str, Any], include_prerelease: bool) -> bool:
    """正式版 skips GitHub Pre-release. 测试版 keeps both."""
    if release.get("draft"):
        return False
    if release.get("prerelease") and not include_prerelease:
        return False
    return True


def _no_release_in_channel(include_prerelease: bool) -> dict[str, Any]:
    channel = "preview" if include_prerelease else "release"
    return {
        "ok": True,
        "update_available": False,
        "up_to_date": True,
        "current_version": VERSION,
        "remote_version": VERSION,
        "remote_tag": "",
        "remote_name": "",
        "asset_name": None,
        "asset_url": None,
        "asset_size": None,
        "asset_sha256_url": None,
        "has_asset": False,
        "html_url": RELEASES_HTML_URL,
        "release_notes": "",
        "channel": channel,
        "warning": OVERSEAS_SOURCE_WARNING_ZH,
        "warning_en": OVERSEAS_SOURCE_WARNING_EN,
        "frozen": is_packaged(),
    }


def check_for_update(*, include_prerelease: bool = False) -> dict[str, Any]:
    """Find the newest ``APP_Ver*`` release and compare with local VERSION.

    ``include_prerelease`` False is 正式版: ignore GitHub releases marked
    Pre-release. True is 测试版: a pre-release can win when its version is
    higher. A newer stable release is still offered on the test channel.
    """
    local = parse_version(VERSION)
    if local is None:
        return _base_error("invalid_local_version", f"Local version is invalid: {VERSION}")

    release: dict[str, Any] | None = None
    tag_name = ""
    remote: tuple[int, ...] | None = None
    channel = "preview" if include_prerelease else "release"

    try:
        from_releases = _list_app_ver_from_releases()
        usable = [
            item
            for item in from_releases
            if _accept_release(item[2], include_prerelease)
        ]
        if usable:
            tag_name, remote, release = max(usable, key=lambda item: item[1])
        elif from_releases:
            return _no_release_in_channel(include_prerelease)
        else:
            # Fallback: tags may exist before a Release is published.
            tags = _list_app_ver_tags()
            latest = max(tags, key=lambda item: item[1]) if tags else None
            if latest is None:
                return _base_error(
                    "no_app_ver_tags",
                    f"No tags matching {UPDATE_TAG_PREFIX}* were found on GitHub",
                )
            tag_name, remote = latest
            try:
                release = _fetch_release_for_tag(tag_name)
            except urllib.error.HTTPError as exc:
                if exc.code != 404:
                    raise
                release = None
            if release is not None and not _accept_release(release, include_prerelease):
                return _no_release_in_channel(include_prerelease)
    except urllib.error.HTTPError as exc:
        fallback = _latest_from_public_feed(include_prerelease)
        exc.close()
        if fallback is None:
            return _base_error("http_error", f"GitHub HTTP {exc.code}")
        tag_name, remote, release = fallback
    except Exception as exc:
        fallback = _latest_from_public_feed(include_prerelease)
        if fallback is None:
            return _base_error("network_error", str(exc))
        tag_name, remote, release = fallback

    assert remote is not None
    remote_str = version_tuple_to_str(remote)
    update_available = compare_versions(local, remote) < 0
    html_fallback = (
        f"https://github.com/{GITHUB_REPO}/releases/tag/{quote(tag_name, safe='')}"
    )

    if release is None:
        return {
            "ok": True,
            "update_available": update_available,
            "up_to_date": not update_available,
            "current_version": VERSION,
            "remote_version": remote_str,
            "remote_tag": tag_name,
            "remote_name": tag_name,
            "asset_name": None,
            "asset_url": None,
            "asset_size": None,
            "asset_sha256_url": None,
            "has_asset": False,
            "html_url": html_fallback,
            "release_notes": "",
            "warning": OVERSEAS_SOURCE_WARNING_ZH,
            "warning_en": OVERSEAS_SOURCE_WARNING_EN,
            "channel": channel,
            "frozen": is_packaged(),
            "error": "no_release",
            "message": f"Tag {tag_name} has no GitHub Release yet",
        }

    assets = release.get("assets") or []
    asset = _pick_exe_asset(list(assets), remote_str)
    checksum_asset = _find_checksum(list(assets), str((asset or {}).get("name") or ""))

    return {
        "ok": True,
        "update_available": update_available,
        "up_to_date": not update_available,
        "current_version": VERSION,
        "remote_version": remote_str,
        "remote_tag": tag_name,
        "remote_name": release.get("name") or tag_name,
        "asset_name": (asset or {}).get("name"),
        "asset_url": (asset or {}).get("browser_download_url"),
        "asset_size": (asset or {}).get("size"),
        "asset_sha256_url": (checksum_asset or {}).get("browser_download_url"),
        "has_asset": asset is not None,
        "html_url": release.get("html_url") or html_fallback,
        "release_notes": _release_notes_text(release),
        "channel": channel,
        "warning": OVERSEAS_SOURCE_WARNING_ZH,
        "warning_en": OVERSEAS_SOURCE_WARNING_EN,
        "frozen": is_packaged(),
    }


def _app_dir() -> str:
    if is_packaged():
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def _running_exe_path() -> str | None:
    if is_packaged():
        return os.path.abspath(sys.executable)
    return None


# A generous ceiling for the installer download; guards against a corrupt or
# hostile mirror streaming an endless body onto the disk.
_MAX_DOWNLOAD_BYTES = 1024 * 1024 * 1024


def _download_file(
    url: str, dest: str, timeout: float = 120.0, max_bytes: int = _MAX_DOWNLOAD_BYTES
) -> None:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": _USER_AGENT,
            "Accept": "application/octet-stream",
        },
    )
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    partial = dest + ".partial"
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp, open(partial, "wb") as out:
            total = 0
            while True:
                chunk = resp.read(1024 * 256)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise ValueError(
                        f"download exceeded {max_bytes} bytes (bad mirror or corrupt asset?)"
                    )
                out.write(chunk)
        os.replace(partial, dest)
    finally:
        if os.path.isfile(partial):
            try:
                os.remove(partial)
            except OSError:
                pass


def _write_update_ui_ps1(
    *,
    pid: int,
    installer: str,
    app_dir: str,
    target_exe: str,
    restart: bool,
    remote_version: str,
) -> str:
    """Borderless deep-blue update window. The system progress bar is not used."""
    update_dir = os.path.dirname(installer)
    ps1_path = os.path.join(update_dir, "apply_update_ui.ps1")

    def q(s: str) -> str:
        return s.replace("'", "''")

    restart_line = (
        f"    try {{ Start-Process -FilePath '{q(target_exe)}' }} catch {{ }}\n"
        if restart
        else ""
    )
    script = f"""# ArkPlots update UI — auto-generated, do not edit
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

Add-Type -TypeDefinition @"
using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Runtime.InteropServices;
using System.Windows.Forms;

public static class ArkChrome {{
  public static void Round(Control control, int radius) {{
    if (control.Width < 2 || control.Height < 2) return;
    int d = Math.Max(2, radius * 2);
    using (var path = new GraphicsPath()) {{
      path.AddArc(0, 0, d, d, 180, 90);
      path.AddArc(control.Width - d - 1, 0, d, d, 270, 90);
      path.AddArc(control.Width - d - 1, control.Height - d - 1, d, d, 0, 90);
      path.AddArc(0, control.Height - d - 1, d, d, 90, 90);
      path.CloseFigure();
      control.Region = new Region(path);
    }}
  }}
}}

public static class ArkNative {{
  [DllImport("user32.dll")] public static extern bool ReleaseCapture();
  [DllImport("user32.dll")] public static extern IntPtr SendMessage(IntPtr hWnd, int msg, int wParam, int lParam);
}}
"@ -ReferencedAssemblies System.Windows.Forms, System.Drawing

$pidWait = {pid}
$setup = '{q(installer)}'
$appDir = '{q(app_dir)}'
$remote = '{q(remote_version)}'

$bg = [System.Drawing.Color]::FromArgb(11, 18, 25)
$card = [System.Drawing.Color]::FromArgb(22, 34, 48)
$header = [System.Drawing.Color]::FromArgb(27, 43, 58)
$track = [System.Drawing.Color]::FromArgb(36, 56, 74)
$accent = [System.Drawing.Color]::FromArgb(110, 184, 232)
$text = [System.Drawing.Color]::FromArgb(215, 230, 239)
$muted = [System.Drawing.Color]::FromArgb(138, 160, 178)
$danger = [System.Drawing.Color]::FromArgb(214, 106, 106)

$form = New-Object System.Windows.Forms.Form
$form.Text = 'ArkPlots 更新'
$form.FormBorderStyle = 'None'
$form.StartPosition = 'CenterScreen'
$form.Size = New-Object System.Drawing.Size(520, 300)
$form.BackColor = $bg
$form.ForeColor = $text
$form.TopMost = $true
$form.ShowInTaskbar = $true
$form.Font = New-Object System.Drawing.Font('Microsoft YaHei UI', 9)
[ArkChrome]::Round($form, 22)

$cardBox = New-Object System.Windows.Forms.Panel
$cardBox.Location = New-Object System.Drawing.Point(16, 16)
$cardBox.Size = New-Object System.Drawing.Size(488, 268)
$cardBox.BackColor = $card
$form.Controls.Add($cardBox)
[ArkChrome]::Round($cardBox, 18)

$accentBar = New-Object System.Windows.Forms.Panel
$accentBar.Location = New-Object System.Drawing.Point(28, 26)
$accentBar.Size = New-Object System.Drawing.Size(42, 4)
$accentBar.BackColor = $accent
$cardBox.Controls.Add($accentBar)
[ArkChrome]::Round($accentBar, 2)

$kicker = New-Object System.Windows.Forms.Label
$kicker.Text = 'ArkPlots'
$kicker.Font = New-Object System.Drawing.Font('Segoe UI', 10, [System.Drawing.FontStyle]::Bold)
$kicker.ForeColor = $accent
$kicker.BackColor = $card
$kicker.Location = New-Object System.Drawing.Point(28, 40)
$kicker.AutoSize = $true
$cardBox.Controls.Add($kicker)

$title = New-Object System.Windows.Forms.Label
$title.Text = '正在更新'
$title.Font = New-Object System.Drawing.Font('Microsoft YaHei UI', 20, [System.Drawing.FontStyle]::Bold)
$title.ForeColor = $text
$title.BackColor = $card
$title.Location = New-Object System.Drawing.Point(26, 64)
$title.AutoSize = $true
$cardBox.Controls.Add($title)

$versionChip = New-Object System.Windows.Forms.Label
$versionChip.Text = "  版本  $remote  "
$versionChip.Font = New-Object System.Drawing.Font('Microsoft YaHei UI', 9)
$versionChip.ForeColor = $text
$versionChip.BackColor = $header
$versionChip.AutoSize = $true
$versionChip.Location = New-Object System.Drawing.Point(28, 112)
$cardBox.Controls.Add($versionChip)
[ArkChrome]::Round($versionChip, 8)

$status = New-Object System.Windows.Forms.Label
$status.Text = '正在准备更新…'
$status.Font = New-Object System.Drawing.Font('Microsoft YaHei UI', 11)
$status.ForeColor = $text
$status.BackColor = $card
$status.Location = New-Object System.Drawing.Point(28, 148)
$status.Size = New-Object System.Drawing.Size(432, 28)
$cardBox.Controls.Add($status)

$detail = New-Object System.Windows.Forms.Label
$detail.Text = '只会替换程序本身。阅读进度和本地数据会保留。'
$detail.Font = New-Object System.Drawing.Font('Microsoft YaHei UI', 9)
$detail.ForeColor = $muted
$detail.BackColor = $card
$detail.Location = New-Object System.Drawing.Point(28, 178)
$detail.Size = New-Object System.Drawing.Size(432, 22)
$cardBox.Controls.Add($detail)

$trackBar = New-Object System.Windows.Forms.Panel
$trackBar.Location = New-Object System.Drawing.Point(28, 214)
$trackBar.Size = New-Object System.Drawing.Size(432, 8)
$trackBar.BackColor = $track
$cardBox.Controls.Add($trackBar)
[ArkChrome]::Round($trackBar, 4)

$fill = New-Object System.Windows.Forms.Panel
$fill.Location = New-Object System.Drawing.Point(-120, 0)
$fill.Size = New-Object System.Drawing.Size(140, 8)
$fill.BackColor = $accent
$trackBar.Controls.Add($fill)

$closeBtn = New-Object System.Windows.Forms.Label
$closeBtn.Text = '关闭'
$closeBtn.TextAlign = 'MiddleCenter'
$closeBtn.Font = New-Object System.Drawing.Font('Microsoft YaHei UI', 9, [System.Drawing.FontStyle]::Bold)
$closeBtn.ForeColor = $bg
$closeBtn.BackColor = $accent
$closeBtn.Location = New-Object System.Drawing.Point(360, 214)
$closeBtn.Size = New-Object System.Drawing.Size(100, 32)
$closeBtn.Visible = $false
$closeBtn.Cursor = [System.Windows.Forms.Cursors]::Hand
$cardBox.Controls.Add($closeBtn)
[ArkChrome]::Round($closeBtn, 12)
$closeBtn.Add_Click({{ $form.Close() }})

$script:marquee = 0
$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = 16
$timer.Add_Tick({{
  $script:marquee += 6
  if ($script:marquee -gt ($trackBar.Width + $fill.Width)) {{ $script:marquee = 0 }}
  $fill.Left = -$fill.Width + $script:marquee
}})

function Start-WindowDrag {{
  [void][ArkNative]::ReleaseCapture()
  [void][ArkNative]::SendMessage($form.Handle, 0xA1, 2, 0)
}}
foreach ($control in @($form, $cardBox, $kicker, $title, $status, $detail, $versionChip)) {{
  $control.Add_MouseDown({{
    param($sender, $e)
    if ($e.Button -eq [System.Windows.Forms.MouseButtons]::Left) {{ Start-WindowDrag }}
  }})
}}

function Invoke-ArkUpdate {{
  # Stay on the UI thread. A BackgroundWorker script block runs on a pool
  # thread with no PowerShell runspace and fails before the installer starts
  # ("There is no Runspace available to run scripts in this thread.").
  $status.Text = '正在关闭当前窗口…'
  [System.Windows.Forms.Application]::DoEvents()
  while ($true) {{
    try {{
      $null = Get-Process -Id $pidWait -ErrorAction Stop
    }} catch {{
      break
    }}
    Start-Sleep -Milliseconds 200
    [System.Windows.Forms.Application]::DoEvents()
  }}
  Start-Sleep -Milliseconds 800
  $status.Text = '正在写入新版本…'
  [System.Windows.Forms.Application]::DoEvents()
  $setupArgs = @('/VERYSILENT', '/NORESTART', '/CLOSEAPPLICATIONS', "/DIR=`"$appDir`"")
  $proc = Start-Process -FilePath $setup -ArgumentList $setupArgs -PassThru
  while (-not $proc.HasExited) {{
    Start-Sleep -Milliseconds 200
    [System.Windows.Forms.Application]::DoEvents()
  }}
  $proc.Refresh()
  if ($proc.ExitCode -ne 0) {{
    throw "安装程序退出码 $($proc.ExitCode)"
  }}
  $status.Text = '更新完成，正在打开…'
  [System.Windows.Forms.Application]::DoEvents()
  Start-Sleep -Milliseconds 500
{restart_line}  try {{ Remove-Item -LiteralPath $setup -Force -ErrorAction SilentlyContinue }} catch {{ }}
}}

$form.Add_Shown({{
  if ($script:updateStarted) {{ return }}
  $script:updateStarted = $true
  [ArkChrome]::Round($versionChip, 10)
  $form.Activate()
  $timer.Start()
  try {{
    Invoke-ArkUpdate
    $timer.Stop()
    $form.Close()
  }} catch {{
    $timer.Stop()
    $status.Text = '更新没有完成'
    $detail.Text = $_.Exception.Message
    $detail.ForeColor = $danger
    $detail.Location = New-Object System.Drawing.Point(28, 184)
    $detail.Size = New-Object System.Drawing.Size(432, 36)
    $trackBar.Visible = $false
    $closeBtn.Visible = $true
    $form.TopMost = $false
  }}
}})

[System.Windows.Forms.Application]::EnableVisualStyles()
[void]$form.ShowDialog()
try {{ Remove-Item -LiteralPath $PSCommandPath -Force -ErrorAction SilentlyContinue }} catch {{ }}
"""
    with open(ps1_path, "w", encoding="utf-8-sig", newline="\n") as f:
        f.write(script)
    return ps1_path


def _write_installer_runner(
    *,
    pid: int,
    installer: str,
    app_dir: str,
    target_exe: str,
    restart: bool,
    remote_version: str = "",
) -> str:
    """Write branded PowerShell update UI (fallback: hidden bat)."""
    return _write_update_ui_ps1(
        pid=pid,
        installer=installer,
        app_dir=app_dir,
        target_exe=target_exe,
        restart=restart,
        remote_version=remote_version or "latest",
    )


def _write_windows_swapper(
    *,
    pid: int,
    new_exe: str,
    target_exe: str,
    optional_stable: str | None,
    restart: bool,
) -> str:
    """Batch file: wait for PID, replace exe only, then optionally restart."""
    update_dir = os.path.dirname(new_exe)
    bat_path = os.path.join(update_dir, "apply_update.bat")
    lines = [
        "@echo off",
        "setlocal EnableExtensions",
        f"set \"PID={pid}\"",
        f"set \"NEW={new_exe}\"",
        f"set \"DST={target_exe}\"",
        ":waitloop",
        "tasklist /FI \"PID eq %PID%\" | findstr /I \"%PID%\" >nul",
        "if not errorlevel 1 (",
        "  timeout /t 1 /nobreak >nul",
        "  goto waitloop",
        ")",
        "timeout /t 1 /nobreak >nul",
        "copy /Y \"%NEW%\" \"%DST%\" >nul",
        "if errorlevel 1 (",
        "  echo UPDATE_FAILED> \"%~dp0update_failed.txt\"",
        "  exit /b 1",
        ")",
    ]
    if optional_stable and os.path.normcase(optional_stable) != os.path.normcase(target_exe):
        lines.append(f"set \"STABLE={optional_stable}\"")
        lines.append("if exist \"%STABLE%\" copy /Y \"%NEW%\" \"%STABLE%\" >nul")
    if restart:
        lines.append("start \"\" \"%DST%\"")
    lines.extend(
        [
            "del /F /Q \"%NEW%\" >nul 2>&1",
            "del /F /Q \"%~f0\" >nul 2>&1",
            "exit /b 0",
        ]
    )
    with open(bat_path, "w", encoding="gbk", errors="replace", newline="\r\n") as f:
        f.write("\r\n".join(lines) + "\r\n")
    return bat_path


_before_process_exit: list[Any] = []


def register_before_process_exit(callback: Any) -> None:
    """Run while the process is still alive, before an update calls ``os._exit``."""
    if callback not in _before_process_exit:
        _before_process_exit.append(callback)


def _close_webview_windows() -> None:
    try:
        import webview

        for win in list(getattr(webview, "windows", []) or []):
            try:
                win.destroy()
            except Exception:
                pass
    except Exception:
        pass


def _schedule_process_exit(delay: float = 1.2) -> None:
    def _exit() -> None:
        time.sleep(delay)
        for callback in list(_before_process_exit):
            try:
                callback()
            except Exception:
                pass
        _close_webview_windows()
        os._exit(0)

    threading.Thread(target=_exit, name="arkplots-update-exit", daemon=True).start()


def request_update_exit() -> dict[str, Any]:
    """Quit after the UI has shown post-update release notes.

    ``apply_update(defer_exit=True)`` leaves the process running so the notes
    stay on screen. This arms the same delayed exit the swapper already waits on.
    """
    global _update_exit_armed
    if not _update_exit_armed:
        return {"ok": False, "error": "not_ready"}
    _update_exit_armed = False
    _schedule_process_exit(0.35)
    return {"ok": True, "will_restart": True}


def _helper_creationflags() -> int:
    """Process flags for the program that applies an update after we exit.

    ``DETACHED_PROCESS`` is intentionally absent. With that flag, Windows
    PowerShell returns exit code 0 without executing ``-File``, so the
    installer never runs.
    """
    flags = 0
    if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
        flags |= subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
    # 0x01000000 — present as a constant on Windows CPython.
    flags |= getattr(subprocess, "CREATE_BREAKAWAY_FROM_JOB", 0x01000000)
    # 0x08000000 — hide the console. A WinForms window is unaffected.
    flags |= getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    detached = getattr(subprocess, "DETACHED_PROCESS", 0)
    if detached:
        flags &= ~detached
    return flags


def _open_helper_log(update_dir: str):
    """Overwrite the helper log. Callers close the handle after ``Popen``."""
    path = os.path.join(update_dir, "apply_update.log")
    try:
        handle = open(path, "w", encoding="utf-8")
    except OSError:
        return subprocess.DEVNULL
    handle.write("launch helper\n")
    handle.flush()
    return handle


def apply_update(
    *,
    restart: bool = True,
    defer_exit: bool = False,
    include_prerelease: bool = False,
) -> dict[str, Any]:
    """Download the remote exe and schedule a safe replace of the running binary.

    When ``defer_exit`` is true, the process stays up until ``request_update_exit``
    so the UI can show this version's release notes before restarting.
    """
    global _update_exit_armed
    check = check_for_update(include_prerelease=include_prerelease)
    if not check.get("ok"):
        return check
    if not check.get("update_available"):
        return {
            **check,
            "applied": False,
            "message": "already_up_to_date",
        }
    if not check.get("has_asset") or not check.get("asset_url"):
        return {
            **check,
            "applied": False,
            "error": "no_asset",
            "message": "Release has no .exe asset to download",
        }

    exe_path = _running_exe_path()
    if not exe_path:
        return {
            **check,
            "applied": False,
            "error": "not_frozen",
            "message": "Updates can only be applied to the packaged .exe build",
        }

    app_dir = _app_dir()
    update_dir = os.path.join(app_dir, _UPDATE_DIR_NAME)
    os.makedirs(update_dir, exist_ok=True)
    asset_name = str(check.get("asset_name") or "ArkPlots_update.exe")
    safe_name = re.sub(r"[^\w.\-]+", "_", asset_name) or "update.exe"
    download_path = os.path.join(update_dir, safe_name)

    try:
        _download_file(str(check["asset_url"]), download_path)
    except Exception as exc:
        return {
            **check,
            "applied": False,
            "error": "download_failed",
            "message": str(exc),
            "warning": OVERSEAS_SOURCE_WARNING_ZH,
            "warning_en": OVERSEAS_SOURCE_WARNING_EN,
        }

    if not os.path.isfile(download_path) or os.path.getsize(download_path) < 1024 * 100:
        return {
            **check,
            "applied": False,
            "error": "download_invalid",
            "message": "Downloaded file is missing or too small",
        }

    # Verify SHA-256 when the release publishes a checksum. Fail closed: a
    # published-but-unreadable checksum aborts the update rather than running
    # an unverified binary. Releases without checksum assets keep working.
    checksum_url = check.get("asset_sha256_url")
    if checksum_url:
        checksum_error = ""
        try:
            expected = _fetch_checksum_hex(str(checksum_url), asset_name)
        except Exception as exc:
            expected = None
            checksum_error = str(exc)
        if expected is None:
            _discard_download(download_path)
            return {
                **check,
                "applied": False,
                "error": "checksum_unavailable",
                "message": checksum_error
                or "Could not read the published SHA-256 checksum",
                "warning": OVERSEAS_SOURCE_WARNING_ZH,
                "warning_en": OVERSEAS_SOURCE_WARNING_EN,
            }
        actual = _sha256_file(download_path)
        if actual != expected:
            _discard_download(download_path)
            return {
                **check,
                "applied": False,
                "error": "checksum_mismatch",
                "message": f"SHA-256 mismatch: expected {expected}, got {actual}",
                "warning": OVERSEAS_SOURCE_WARNING_ZH,
                "warning_en": OVERSEAS_SOURCE_WARNING_EN,
            }

    # DETACHED_PROCESS makes Windows PowerShell exit 0 without running -File,
    # so the installer never starts and the app only closes. CREATE_NO_WINDOW
    # hides the console host; the WinForms progress window still appears.
    # Breakaway keeps the helper alive after this process calls os._exit.
    creationflags = _helper_creationflags()

    if _asset_is_installer(asset_name):
        ui_script = _write_installer_runner(
            pid=os.getpid(),
            installer=download_path,
            app_dir=app_dir,
            target_exe=exe_path,
            restart=restart,
            remote_version=str(check.get("remote_version") or ""),
        )
        # Hidden console host; WinForms UI is shown by the script itself.
        log_handle = _open_helper_log(update_dir)
        try:
            subprocess.Popen(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-WindowStyle",
                    "Hidden",
                    "-File",
                    ui_script,
                ],
                cwd=update_dir,
                close_fds=True,
                creationflags=creationflags,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
            )
        finally:
            if log_handle is not subprocess.DEVNULL:
                log_handle.close()
        note = "Installer upgrades the program only; Read_record.json is not modified."
    else:
        stable_twin = os.path.join(app_dir, f"{EXE_STEM}.exe")
        optional_stable = stable_twin if os.path.isfile(stable_twin) else None
        bat = _write_windows_swapper(
            pid=os.getpid(),
            new_exe=download_path,
            target_exe=exe_path,
            optional_stable=optional_stable,
            restart=restart,
        )
        log_handle = _open_helper_log(update_dir)
        try:
            subprocess.Popen(
                ["cmd.exe", "/c", bat],
                cwd=update_dir,
                close_fds=True,
                creationflags=creationflags,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
            )
        finally:
            if log_handle is not subprocess.DEVNULL:
                log_handle.close()
        note = "User data files are not modified; only the executable is replaced."

    if defer_exit:
        _update_exit_armed = True
    else:
        _update_exit_armed = False
        _schedule_process_exit()
    return {
        **check,
        "applied": True,
        "will_restart": restart,
        "exit_deferred": defer_exit,
        "message": "update_scheduled",
        "target_exe": exe_path,
        "note": note,
        "update_notes": update_announcement(str(check.get("remote_tag") or "")),
    }
