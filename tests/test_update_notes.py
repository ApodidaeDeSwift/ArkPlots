"""Release notes travel with update checks, and exit waits for the UI."""
from __future__ import annotations

import json
import os
import sys
import time
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch
from urllib.error import HTTPError

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import updater  # noqa: E402
from server import _bind_server, serve_in_background, stop_server  # noqa: E402
from updater import (  # noqa: E402
    _release_notes_text,
    apply_update,
    check_for_update,
    fetch_tagged_update_markdown,
    read_local_update_markdown,
    request_update_exit,
    update_announcement,
)


NOTES = "## 更新\n\n- 修复空白页\n- **说明**见 [页面](https://example.com)\n"


def _release(body: object = NOTES) -> dict:
    return {
        "tag_name": "APP_Ver99.0.0.1",
        "name": "Ninety",
        "body": body,
        "html_url": "https://github.com/ApodidaeDeSwift/ArkPlots/releases/tag/APP_Ver99.0.0.1",
        "draft": False,
        "assets": [
            {
                "name": "Arkplot_setup_ver99.0.0.1.exe",
                "browser_download_url": "https://example.invalid/setup.exe",
                "size": 4096,
            }
        ],
    }


class ReleaseNotesTests(unittest.TestCase):
    def tearDown(self) -> None:
        updater._update_exit_armed = False

    def test_check_includes_markdown_body(self) -> None:
        found = [("APP_Ver99.0.0.1", (99, 0, 0, 1), _release())]
        with (
            patch("updater.VERSION", "1.0.0.0"),
            patch("updater._list_app_ver_from_releases", return_value=found),
        ):
            result = check_for_update()
        self.assertTrue(result["ok"])
        self.assertTrue(result["update_available"])
        self.assertEqual(result["release_notes"], NOTES.strip())
        self.assertEqual(result["remote_version"], "99.0.0.1")

    def test_missing_body_is_empty_string(self) -> None:
        self.assertEqual(_release_notes_text({"body": None}), "")
        self.assertEqual(_release_notes_text({"body": "  \n"}), "")
        self.assertEqual(_release_notes_text(None), "")
        found = [("APP_Ver99.0.0.1", (99, 0, 0, 1), _release(body=None))]
        with (
            patch("updater.VERSION", "1.0.0.0"),
            patch("updater._list_app_ver_from_releases", return_value=found),
        ):
            result = check_for_update()
        self.assertEqual(result["release_notes"], "")

    def test_notes_are_capped(self) -> None:
        text = _release_notes_text({"body": "a" * (updater._NOTES_LIMIT + 20)})
        self.assertLessEqual(len(text), updater._NOTES_LIMIT + 2)
        self.assertTrue(text.endswith("\n…"))

    def test_no_release_still_has_notes_field(self) -> None:
        err = HTTPError("https://example.invalid", 404, "missing", hdrs=None, fp=None)
        with (
            patch("updater.VERSION", "1.0.0.0"),
            patch("updater._list_app_ver_from_releases", return_value=[]),
            patch("updater._list_app_ver_tags", return_value=[("APP_Ver2.0.0.0", (2, 0, 0, 0))]),
            patch("updater._fetch_release_for_tag", side_effect=err),
        ):
            result = check_for_update()
        self.assertEqual(result["release_notes"], "")
        self.assertEqual(result["error"], "no_release")
        self.assertTrue(result["update_available"])

    def test_current_release_notes_when_already_up_to_date(self) -> None:
        found = [("APP_Ver1.0.0.0", (1, 0, 0, 0), _release("当前版本说明"))]
        with (
            patch("updater.VERSION", "1.0.0.0"),
            patch("updater._list_app_ver_from_releases", return_value=found),
        ):
            result = check_for_update()
        self.assertFalse(result["update_available"])
        self.assertEqual(result["release_notes"], "当前版本说明")

    def test_local_update_markdown_is_the_project_file(self) -> None:
        text = read_local_update_markdown()
        self.assertIn("更新公告", text)
        path = os.path.join(ROOT, "Update.md")
        with open(path, encoding="utf-8") as handle:
            self.assertEqual(text, handle.read().strip())

    def test_announcement_prefers_tagged_update_md(self) -> None:
        remote = "# 新版本\n\n- 来自标签上的 Update.md"
        with patch("updater.fetch_tagged_update_markdown", return_value=remote):
            self.assertEqual(update_announcement("APP_Ver99.0.0.1"), remote)

    def test_announcement_falls_back_to_local_file(self) -> None:
        with patch("updater.fetch_tagged_update_markdown", return_value=""):
            self.assertIn("更新公告", update_announcement("APP_Ver99.0.0.1"))

    def test_tagged_fetch_reads_markdown_body(self) -> None:
        payload = "# 更新公告\n\n- 保留阅读进度\n".encode("utf-8")

        class _Resp:
            def read(self) -> bytes:
                return payload

            def __enter__(self) -> "_Resp":
                return self

            def __exit__(self, *_args: object) -> None:
                return None

        with patch("updater.urllib.request.urlopen", return_value=_Resp()):
            text = fetch_tagged_update_markdown("APP_Ver26.10.21.1")
        self.assertEqual(text, payload.decode("utf-8").strip())

    def test_deferred_exit_waits_for_the_ui(self) -> None:
        check = {
            "ok": True,
            "update_available": True,
            "has_asset": True,
            "asset_url": "https://example.invalid/setup.exe",
            "asset_name": "Arkplot_setup_ver99.0.0.1.exe",
            "remote_version": "99.0.0.1",
            "release_notes": NOTES.strip(),
        }
        with (
            patch("updater.check_for_update", return_value=check),
            patch("updater._running_exe_path", return_value=r"C:\ArkPlots\ArkPlots.exe"),
            patch("updater._download_file"),
            patch("updater.os.makedirs"),
            patch("updater.os.path.isfile", return_value=True),
            patch("updater.os.path.getsize", return_value=200_000),
            patch("updater._write_installer_runner", return_value=r"C:\ArkPlots\_update\ui.ps1"),
            patch("updater.subprocess.Popen") as popen,
            patch("updater._schedule_process_exit") as schedule,
            patch("updater.update_announcement", return_value="# 更新公告\n\n来自 Update.md"),
        ):
            deferred = apply_update(restart=True, defer_exit=True)
            self.assertTrue(deferred["applied"])
            self.assertTrue(deferred["exit_deferred"])
            self.assertEqual(deferred["release_notes"], NOTES.strip())
            self.assertEqual(deferred["update_notes"], "# 更新公告\n\n来自 Update.md")
            schedule.assert_not_called()
            popen.assert_called_once()
            self.assertTrue(updater._update_exit_armed)

            early = request_update_exit()
            self.assertTrue(early["ok"])
            schedule.assert_called_once()
            self.assertFalse(updater._update_exit_armed)

            blocked = request_update_exit()
            self.assertFalse(blocked["ok"])
            self.assertEqual(blocked["error"], "not_ready")
            schedule.assert_called_once()

    def test_exit_route_is_not_ready_before_an_update(self) -> None:
        updater._update_exit_armed = False
        server, port = _bind_server(0, tries=1)
        serve_in_background(server)
        try:
            url = f"http://127.0.0.1:{port}/api/update/exit"
            deadline = time.time() + 3
            last: Exception | None = None
            while time.time() < deadline:
                try:
                    req = urllib.request.Request(url, data=b"{}", method="POST")
                    with urllib.request.urlopen(req, timeout=1) as resp:
                        self.fail(f"expected 409, got {resp.status}")
                except urllib.error.HTTPError as exc:
                    try:
                        body = json.loads(exc.read().decode("utf-8"))
                    finally:
                        exc.close()
                    self.assertEqual(exc.code, 409)
                    self.assertFalse(body["ok"])
                    self.assertEqual(body["error"], "not_ready")
                    return
                except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
                    last = exc
                    time.sleep(0.05)
            self.fail(f"exit route did not answer: {last}")
        finally:
            stop_server(server)


if __name__ == "__main__":
    unittest.main()
