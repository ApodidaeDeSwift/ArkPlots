"""SHA-256 verification of the downloaded update (fail-closed when published)."""
from __future__ import annotations

import os
import sys
import unittest
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import updater  # noqa: E402
from updater import _extract_sha256, _find_checksum, apply_update  # noqa: E402

GOOD = "a" * 64
BAD = "b" * 64


def _assets(*names: str) -> list[dict]:
    return [
        {"name": name, "browser_download_url": f"https://example.invalid/{name}"}
        for name in names
    ]


class ExtractSha256Tests(unittest.TestCase):
    def test_sidecar_format(self) -> None:
        text = f"{GOOD}  Arkplot_setup_ver99.0.0.1.exe\n"
        self.assertEqual(_extract_sha256(text, "Arkplot_setup_ver99.0.0.1.exe"), GOOD)

    def test_checksums_file_prefers_own_asset_line(self) -> None:
        text = (
            f"{BAD}  other.exe\n"
            f"{GOOD}  Arkplot_setup_ver99.0.0.1.exe\n"
        )
        self.assertEqual(
            _extract_sha256(text, "Arkplot_setup_ver99.0.0.1.exe"), GOOD
        )
        self.assertEqual(_extract_sha256(text, "other.exe"), BAD)

    def test_uppercase_hex_is_lowered(self) -> None:
        self.assertEqual(_extract_sha256(GOOD.upper() + "  x.exe", "x.exe"), GOOD)

    def test_no_digest_returns_none(self) -> None:
        self.assertIsNone(_extract_sha256("# comment\nnothing here\n", "x.exe"))


class FindChecksumTests(unittest.TestCase):
    def test_prefers_exact_sidecar(self) -> None:
        assets = _assets(
            "Arkplot_setup_ver99.0.0.1.exe",
            "Arkplot_setup_ver99.0.0.1.exe.sha256",
            "checksums.txt",
        )
        found = _find_checksum(assets, "Arkplot_setup_ver99.0.0.1.exe")
        self.assertEqual(
            found["name"], "Arkplot_setup_ver99.0.0.1.exe.sha256"
        )

    def test_falls_back_to_checksums_txt(self) -> None:
        found = _find_checksum(_assets("x.exe", "checksums.txt"), "x.exe")
        self.assertEqual(found["name"], "checksums.txt")

    def test_none_when_release_has_no_checksum(self) -> None:
        self.assertIsNone(_find_checksum(_assets("x.exe"), "x.exe"))
        self.assertIsNone(_find_checksum(_assets("x.exe"), ""))


class ApplyUpdateChecksumTests(unittest.TestCase):
    """apply_update verifies SHA-256 before anything is executed."""

    CHECK = {
        "ok": True,
        "update_available": True,
        "has_asset": True,
        "asset_url": "https://example.invalid/setup.exe",
        "asset_name": "Arkplot_setup_ver99.0.0.1.exe",
        "asset_sha256_url": "https://example.invalid/setup.exe.sha256",
        "remote_version": "99.0.0.1",
        "remote_tag": "APP_Ver99.0.0.1",
    }

    def _patch_common(self):
        return (
            patch("updater.check_for_update", return_value=dict(self.CHECK)),
            patch("updater._running_exe_path", return_value=r"C:\ArkPlots\ArkPlots.exe"),
            patch("updater._download_file"),
            patch("updater.os.makedirs"),
            patch("updater.os.path.isfile", return_value=True),
            patch("updater.os.path.getsize", return_value=200_000),
            patch("updater._write_installer_runner", return_value=r"C:\ArkPlots\_update\ui.ps1"),
            patch("updater.subprocess.Popen"),
            patch("updater._schedule_process_exit"),
            patch("updater.update_announcement", return_value=""),
        )

    def test_matching_checksum_applies(self) -> None:
        patches = self._patch_common()
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], \
                patches[6], patches[7] as popen, patches[8], patches[9], \
                patch("updater._fetch_checksum_hex", return_value=GOOD), \
                patch("updater._sha256_file", return_value=GOOD):
            result = apply_update(restart=True, defer_exit=False)
        self.assertTrue(result["applied"])
        self.assertEqual(result.get("error"), None)
        popen.assert_called_once()

    def test_mismatching_checksum_aborts_and_discards(self) -> None:
        patches = self._patch_common()
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], \
                patches[6], patches[7] as popen, patches[8], patches[9], \
                patch("updater._fetch_checksum_hex", return_value=GOOD), \
                patch("updater._sha256_file", return_value=BAD), \
                patch("updater.os.remove") as remove:
            result = apply_update(restart=True, defer_exit=False)
        self.assertFalse(result["applied"])
        self.assertEqual(result["error"], "checksum_mismatch")
        popen.assert_not_called()
        remove.assert_called()

    def test_unreadable_checksum_fails_closed(self) -> None:
        patches = self._patch_common()
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], \
                patches[6], patches[7] as popen, patches[8], patches[9], \
                patch("updater._fetch_checksum_hex", side_effect=OSError("no route")), \
                patch("updater.os.remove"):
            result = apply_update(restart=True, defer_exit=False)
        self.assertFalse(result["applied"])
        self.assertEqual(result["error"], "checksum_unavailable")
        popen.assert_not_called()

    def test_release_without_checksum_keeps_updating(self) -> None:
        check = dict(self.CHECK, asset_sha256_url=None)
        patches = self._patch_common()
        with patch("updater.check_for_update", return_value=check), \
                patches[1], patches[2], patches[3], patches[4], patches[5], \
                patches[6], patches[7] as popen, patches[8], patches[9], \
                patch("updater._fetch_checksum_hex") as fetch:
            result = apply_update(restart=True, defer_exit=False)
        self.assertTrue(result["applied"])
        fetch.assert_not_called()
        popen.assert_called_once()


if __name__ == "__main__":
    unittest.main()
