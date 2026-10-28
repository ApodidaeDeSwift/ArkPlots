"""Release notes travel with update checks, and exit waits for the UI."""
from __future__ import annotations
 
import json
import os
import subprocess
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

    def test_api_rate_limit_uses_public_release_feed(self) -> None:
        atom = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Release notes from ArkPlots</title>
  <entry>
    <title>APP_Ver1.2.0.0</title>
    <link rel="alternate" href="https://github.com/ApodidaeDeSwift/ArkPlots/releases/tag/APP_Ver1.2.0.0"/>
    <content type="html">&lt;p&gt;旧版本&lt;/p&gt;</content>
  </entry>
  <entry>
    <title>桌面版</title>
    <link rel="alternate" href="https://github.com/ApodidaeDeSwift/ArkPlots/releases/tag/APP_Ver99.0.0.1"/>
    <content type="html">&lt;ul&gt;&lt;li&gt;修复空白页&lt;/li&gt;&lt;li&gt;&lt;a href="https://example.com/notes"&gt;说明&lt;/a&gt;&lt;/li&gt;&lt;/ul&gt;</content>
  </entry>
</feed>
"""
        page = (
            '<a href="/ApodidaeDeSwift/ArkPlots/releases/download/'
            'APP_Ver99.0.0.1/Arkplot_setup_ver99.0.0.1.exe">'
            "Arkplot_setup_ver99.0.0.1.exe</a>"
        )

        def http_text(url: str, accept: str, timeout: float = 20.0) -> str:
            del accept, timeout
            if url.endswith("/releases.atom"):
                return atom
            self.assertIn("/releases/expanded_assets/APP_Ver99.0.0.1", url)
            return page

        err = HTTPError(
            "https://api.github.com/repos/ApodidaeDeSwift/ArkPlots/releases",
            403,
            "rate limit exceeded",
            hdrs=None,
            fp=None,
        )
        with (
            patch("updater.VERSION", "1.0.0.0"),
            patch("updater._list_app_ver_from_releases", side_effect=err),
            patch("updater._http_text", side_effect=http_text),
        ):
            result = check_for_update(include_prerelease=True)
        self.assertTrue(result["ok"])
        self.assertTrue(result["update_available"])
        self.assertEqual(result["remote_tag"], "APP_Ver99.0.0.1")
        self.assertEqual(result["remote_version"], "99.0.0.1")
        self.assertEqual(result["asset_name"], "Arkplot_setup_ver99.0.0.1.exe")
        self.assertEqual(
            result["asset_url"],
            "https://github.com/ApodidaeDeSwift/ArkPlots/releases/download/"
            "APP_Ver99.0.0.1/Arkplot_setup_ver99.0.0.1.exe",
        )
        self.assertIn("修复空白页", result["release_notes"])
        self.assertIn("https://example.com/notes", result["release_notes"])
        self.assertNotIn("旧版本", result["release_notes"])

    def test_update_window_script_is_a_rounded_deep_blue_card(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = updater._write_update_ui_ps1(
                pid=1,
                installer=os.path.join(tmp, "setup.exe"),
                app_dir=tmp,
                target_exe=os.path.join(tmp, "ArkPlots.exe"),
                restart=False,
                remote_version="26.10.22.1",
            )
            with open(path, encoding="utf-8-sig") as handle:
                text = handle.read()
        self.assertIn("FromArgb(11, 18, 25)", text)
        self.assertIn("AddArc", text)
        self.assertIn("正在更新", text)
        self.assertIn("阅读进度和本地数据会保留", text)
        self.assertNotIn("ProgressBar", text)
        self.assertNotIn("SYSTEM  UPDATE", text)
        self.assertNotIn("Add_DoWork", text)
        self.assertNotIn("RunWorkerAsync", text)
        self.assertIn("Invoke-ArkUpdate", text)
        self.assertIn("DoEvents", text)

    def test_update_window_runs_the_installer_on_the_ui_thread(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            marker = os.path.join(tmp, "ran.txt")
            setup = os.path.join(tmp, "setup.cmd")
            with open(setup, "w", encoding="ascii", newline="\r\n") as handle:
                handle.write(f'@echo off\r\necho ok>"%s"\r\nexit /b 0\r\n' % marker)
            path = updater._write_update_ui_ps1(
                pid=2**31 - 1,
                installer=setup,
                app_dir=tmp,
                target_exe=os.path.join(tmp, "ArkPlots.exe"),
                restart=False,
                remote_version="26.10.28.8",
            )
            result = subprocess.run(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    path,
                ],
                cwd=tmp,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
            )
            combined = (result.stdout or "") + (result.stderr or "")
            self.assertNotIn("运行空间", combined)
            self.assertNotIn("Runspace", combined)
            self.assertEqual(result.returncode, 0, combined)
            self.assertTrue(os.path.isfile(marker), combined)

    def test_failed_installer_stays_open_without_a_runspace_error(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            marker = os.path.join(tmp, "ran.txt")
            setup = os.path.join(tmp, "setup.cmd")
            with open(setup, "w", encoding="ascii", newline="\r\n") as handle:
                handle.write('@echo off\r\necho bad>"%s"\r\nexit /b 3\r\n' % marker)
            path = updater._write_update_ui_ps1(
                pid=2**31 - 1,
                installer=setup,
                app_dir=tmp,
                target_exe=os.path.join(tmp, "ArkPlots.exe"),
                restart=False,
                remote_version="26.10.28.8",
            )
            proc = subprocess.Popen(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    path,
                ],
                cwd=tmp,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            try:
                deadline = time.time() + 20
                while time.time() < deadline and not os.path.isfile(marker):
                    if proc.poll() is not None:
                        break
                    time.sleep(0.2)
                self.assertTrue(os.path.isfile(marker))
                time.sleep(0.8)
                self.assertIsNone(proc.poll())
            finally:
                if proc.poll() is None:
                    proc.kill()
                output = proc.communicate(timeout=10)[0].decode("utf-8", "replace")
            self.assertNotIn("运行空间", output)
            self.assertNotIn("Runspace", output)

    def test_public_feed_failure_keeps_the_api_error(self) -> None:
        err = HTTPError(
            "https://api.github.com/repos/ApodidaeDeSwift/ArkPlots/releases",
            403,
            "rate limit exceeded",
            hdrs=None,
            fp=None,
        )
        with (
            patch("updater.VERSION", "1.0.0.0"),
            patch("updater._list_app_ver_from_releases", side_effect=err),
            patch("updater._http_text", side_effect=urllib.error.URLError("timed out")),
        ):
            result = check_for_update()
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "http_error")

    def test_api_success_does_not_read_the_public_feed(self) -> None:
        found = [("APP_Ver99.0.0.1", (99, 0, 0, 1), _release())]
        with (
            patch("updater.VERSION", "1.0.0.0"),
            patch("updater._list_app_ver_from_releases", return_value=found),
            patch("updater._latest_from_public_feed") as feed,
        ):
            result = check_for_update()
        self.assertTrue(result["ok"])
        feed.assert_not_called()

    def test_current_release_notes_when_already_up_to_date(self) -> None:
        found = [("APP_Ver1.0.0.0", (1, 0, 0, 0), _release("当前版本说明"))]
        with (
            patch("updater.VERSION", "1.0.0.0"),
            patch("updater._list_app_ver_from_releases", return_value=found),
        ):
            result = check_for_update()
        self.assertFalse(result["update_available"])
        self.assertEqual(result["release_notes"], "当前版本说明")

    def test_frontend_version_file_follows_app_info(self) -> None:
        import importlib.util

        path = os.path.join(ROOT, "packaging", "sync_frontend_version.py")
        spec = importlib.util.spec_from_file_location("sync_frontend_version", path)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        text = module.frontend_version_ts()
        self.assertIn(f"export const APP_VERSION = '{module.VERSION}'", text)
        self.assertIn(
            f"export const APP_CHANNEL: 'release' | 'preview' = '{module.CHANNEL}'",
            text,
        )
        self.assertNotIn("as const", text)

    def test_local_update_markdown_is_the_project_file(self) -> None:
        text = read_local_update_markdown()
        self.assertIn("更新公告", text)
        self.assertIn(updater.VERSION, text)
        self.assertNotIn("{{VERSION}}", text)
        path = os.path.join(ROOT, "Update.md")
        with open(path, encoding="utf-8") as handle:
            raw = handle.read().strip()
        self.assertEqual(text, raw.replace("{{VERSION}}", updater.VERSION))

    def test_tagged_markdown_fills_its_own_version(self) -> None:
        payload = "# 更新公告\n\n## Ver{{VERSION}}\n".encode("utf-8")

        class _Resp:
            def read(self) -> bytes:
                return payload

            def __enter__(self) -> "_Resp":
                return self

            def __exit__(self, *_args: object) -> None:
                return None

        with patch("updater.urllib.request.urlopen", return_value=_Resp()):
            text = fetch_tagged_update_markdown("APP_Ver26.10.21.1")
        self.assertIn("Ver26.10.21.1", text)
        self.assertNotIn("{{VERSION}}", text)

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
            patch("updater._open_helper_log", return_value=subprocess.DEVNULL),
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
            flags = popen.call_args.kwargs["creationflags"]
            self.assertEqual(flags, updater._helper_creationflags())
            detached = getattr(subprocess, "DETACHED_PROCESS", 0)
            self.assertFalse(flags & detached)
            self.assertTrue(updater._update_exit_armed)

            early = request_update_exit()
            self.assertTrue(early["ok"])
            schedule.assert_called_once()
            self.assertFalse(updater._update_exit_armed)

            blocked = request_update_exit()
            self.assertFalse(blocked["ok"])
            self.assertEqual(blocked["error"], "not_ready")
            schedule.assert_called_once()

    def test_stable_channel_skips_a_newer_prerelease(self) -> None:
        preview = _release()
        preview["prerelease"] = True
        stable = _release("正式版说明")
        stable["tag_name"] = "APP_Ver2.0.0.0"
        stable["prerelease"] = False
        stable["assets"] = [
            {
                "name": "Arkplot_setup_ver2.0.0.0.exe",
                "browser_download_url": "https://example.invalid/stable.exe",
                "size": 4096,
            }
        ]
        found = [
            ("APP_Ver99.0.0.1", (99, 0, 0, 1), preview),
            ("APP_Ver2.0.0.0", (2, 0, 0, 0), stable),
        ]
        with (
            patch("updater.VERSION", "1.0.0.0"),
            patch("updater._list_app_ver_from_releases", return_value=found),
        ):
            stable_result = check_for_update(include_prerelease=False)
            preview_result = check_for_update(include_prerelease=True)
        self.assertEqual(stable_result["remote_version"], "2.0.0.0")
        self.assertEqual(stable_result["channel"], "release")
        self.assertEqual(preview_result["remote_version"], "99.0.0.1")
        self.assertEqual(preview_result["channel"], "preview")

    def test_stable_channel_is_quiet_when_only_prereleases_exist(self) -> None:
        preview = _release()
        preview["prerelease"] = True
        found = [("APP_Ver99.0.0.1", (99, 0, 0, 1), preview)]
        with (
            patch("updater.VERSION", "1.0.0.0"),
            patch("updater._list_app_ver_from_releases", return_value=found),
        ):
            result = check_for_update(include_prerelease=False)
        self.assertTrue(result["ok"])
        self.assertFalse(result["update_available"])

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
