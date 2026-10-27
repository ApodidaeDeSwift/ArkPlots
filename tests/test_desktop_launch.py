"""Bind the real listening port, and check the window launcher uses that URL."""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request
from unittest.mock import MagicMock, patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from listener import listener_pids, reclaim_arkplots_port  # noqa: E402
from server import (  # noqa: E402
    _bind_server,
    listening_url,
    prepare_server,
    serve_in_background,
    stop_server,
)


class BindUrlTests(unittest.TestCase):
    def test_url_uses_actual_socket_port(self) -> None:
        server, port = _bind_server(0, tries=1)
        try:
            self.assertGreater(port, 0)
            self.assertEqual(server.server_address[1], port)
            self.assertEqual(listening_url(server), f"http://127.0.0.1:{port}/")
        finally:
            stop_server(server)

    def test_busy_port_moves_forward(self) -> None:
        holder = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        holder.bind(("127.0.0.1", 0))
        busy = holder.getsockname()[1]
        holder.listen(1)
        server = None
        try:
            server, port = _bind_server(busy, tries=8)
            self.assertEqual(port, busy + 1)
            url = listening_url(server)
            self.assertEqual(url, f"http://127.0.0.1:{port}/")
            self.assertNotIn(f":{busy}/", url)
        finally:
            if server is not None:
                stop_server(server)
            holder.close()

    def test_second_server_does_not_share_the_port(self) -> None:
        first, port = _bind_server(0, tries=1)
        second = None
        try:
            self.assertFalse(first.allow_reuse_address)
            if sys.platform == "win32":
                self.assertEqual(
                    first.socket.getsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE),
                    1,
                )
                thief = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    thief.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    with self.assertRaises(OSError):
                        thief.bind(("127.0.0.1", port))
                finally:
                    thief.close()
            second, other = _bind_server(port, tries=4)
            self.assertNotEqual(other, port)
        finally:
            if second is not None:
                stop_server(second)
            stop_server(first)


class WindowLaunchTests(unittest.TestCase):
    def test_launch_window_opens_bound_url_and_stops(self) -> None:
        import main

        http = MagicMock()
        url = "http://127.0.0.1:18080/"
        with (
            patch("server.prepare_server", return_value=(http, url)),
            patch("server.serve_in_background") as background,
            patch("server.stop_server") as stop,
            patch("server._install_exit_hooks"),
            patch.object(main, "_wait_until_ready") as wait,
            patch.object(main, "_open_webview") as open_window,
        ):
            main.launch_window(8765)
        background.assert_called_once_with(http)
        wait.assert_called_once_with(url)
        open_window.assert_called_once()
        self.assertEqual(open_window.call_args.args[0], url)
        stop.assert_called_once_with(http)

    def test_launch_window_stops_server_when_window_fails(self) -> None:
        import main

        http = MagicMock()
        url = "http://127.0.0.1:18081/"
        with (
            patch("server.prepare_server", return_value=(http, url)),
            patch("server.serve_in_background"),
            patch("server.stop_server") as stop,
            patch("server._install_exit_hooks"),
            patch.object(main, "_wait_until_ready"),
            patch.object(main, "_open_webview", side_effect=RuntimeError("no gui")),
        ):
            with self.assertRaises(SystemExit):
                main.launch_window(8765)
        stop.assert_called_once_with(http)

    def test_open_webview_targets_given_url(self) -> None:
        import main

        fake = MagicMock()
        with patch.dict(sys.modules, {"webview": fake}):
            main._open_webview("http://127.0.0.1:23456/")
        args, kwargs = fake.create_window.call_args
        self.assertEqual(args[0], "ArkPlots")
        self.assertEqual(args[1], "http://127.0.0.1:23456/")
        self.assertEqual(kwargs.get("width"), 1400)
        self.assertEqual(kwargs.get("height"), 900)
        self.assertTrue(kwargs.get("resizable"))
        self.assertTrue(kwargs.get("text_select"))
        fake.start.assert_called_once()
        icon = fake.start.call_args.kwargs.get("icon", "")
        self.assertTrue(icon.replace("\\", "/").endswith("icon.ico"))


class PackagedDetectionTests(unittest.TestCase):
    def test_meipass_counts_as_packaged_when_frozen_is_false(self) -> None:
        import updater
        from app_info import is_packaged

        with (
            patch.object(sys, "frozen", False, create=True),
            patch.object(sys, "_MEIPASS", r"C:\bundle", create=True),
        ):
            self.assertTrue(is_packaged())
            self.assertEqual(updater._running_exe_path(), os.path.abspath(sys.executable))
            self.assertEqual(
                os.path.normcase(updater._app_dir()),
                os.path.normcase(os.path.dirname(os.path.abspath(sys.executable))),
            )

    def test_source_tree_is_not_packaged(self) -> None:
        import updater
        from app_info import is_packaged

        had_meipass = hasattr(sys, "_MEIPASS")
        saved = getattr(sys, "_MEIPASS", None)
        if had_meipass:
            delattr(sys, "_MEIPASS")
        try:
            with patch.object(sys, "frozen", False, create=True):
                self.assertFalse(is_packaged())
                self.assertIsNone(updater._running_exe_path())
        finally:
            if had_meipass:
                sys._MEIPASS = saved


class ListenerLifecycleTests(unittest.TestCase):
    def test_listener_pid_is_this_process(self) -> None:
        holder = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        holder.bind(("127.0.0.1", 0))
        port = holder.getsockname()[1]
        holder.listen(1)
        try:
            self.assertIn(os.getpid(), listener_pids("127.0.0.1", port))
        finally:
            holder.close()

    def test_stop_releases_the_port_immediately(self) -> None:
        first, port = _bind_server(0, tries=1)
        stop_server(first)
        second, again = _bind_server(port, tries=1)
        try:
            self.assertEqual(again, port)
        finally:
            stop_server(second)

    def test_foreign_listener_is_not_ours_to_close(self) -> None:
        holder = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        holder.bind(("127.0.0.1", 0))
        port = holder.getsockname()[1]
        holder.listen(1)
        try:
            reclaim_arkplots_port("127.0.0.1", port, timeout=0.4)
            self.assertTrue(os.getpid() in listener_pids("127.0.0.1", port))
        finally:
            holder.close()

    def test_reclaim_closes_a_previous_listener_in_process(self) -> None:
        previous = os.environ.get("ARKPLOTS_EXIT_ON_SHUTDOWN")
        os.environ["ARKPLOTS_EXIT_ON_SHUTDOWN"] = "0"
        handle = tempfile.NamedTemporaryFile(prefix="arkplots-instance-", delete=False)
        handle.close()
        os.environ["ARKPLOTS_INSTANCE_FILE"] = handle.name
        first = None
        second = None
        try:
            first, _url = prepare_server(0)
            port = int(first.server_address[1])
            serve_in_background(first)
            self._wait_health(port)
            reclaim_arkplots_port("127.0.0.1", port, timeout=3.0)
            self.assertFalse(self._accepts(port), "previous listener still has the port")
            second, again = _bind_server(port, tries=1)
            self.assertEqual(again, port)
        finally:
            if second is not None:
                stop_server(second)
            if first is not None:
                stop_server(first)
            if previous is None:
                os.environ.pop("ARKPLOTS_EXIT_ON_SHUTDOWN", None)
            else:
                os.environ["ARKPLOTS_EXIT_ON_SHUTDOWN"] = previous
            os.environ.pop("ARKPLOTS_INSTANCE_FILE", None)
            try:
                os.remove(handle.name)
            except OSError:
                pass

    def test_new_process_replaces_a_leftover_listener(self) -> None:
        instance = tempfile.NamedTemporaryFile(prefix="arkplots-instance-", delete=False)
        instance.close()
        env = os.environ.copy()
        env["ARKPLOTS_INSTANCE_FILE"] = instance.name
        env["ARKPLOTS_EXIT_ON_SHUTDOWN"] = "1"
        env["ARKPLOTS_ROOT"] = ROOT
        env["PYTHONIOENCODING"] = "utf-8"
        child = subprocess.Popen(
            [sys.executable, "-c", _LEFTOVER_SERVER],
            cwd=ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        taken = None
        try:
            assert child.stdout is not None
            port = 0
            deadline = time.monotonic() + 8
            while time.monotonic() < deadline and child.poll() is None:
                line = child.stdout.readline().strip()
                if line.isdigit():
                    port = int(line)
                    break
            self.assertGreater(port, 0, "leftover server did not report its port")
            self._wait_health(port)
            os.environ["ARKPLOTS_INSTANCE_FILE"] = instance.name
            reclaim_arkplots_port("127.0.0.1", port, timeout=4.0)
            child.wait(timeout=5)
            self.assertFalse(self._accepts(port))
            taken, again = _bind_server(port, tries=1)
            self.assertEqual(again, port)
        finally:
            if taken is not None:
                stop_server(taken)
            if child.poll() is None:
                child.kill()
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
            if child.stdout is not None:
                child.stdout.close()
            os.environ.pop("ARKPLOTS_INSTANCE_FILE", None)
            try:
                os.remove(instance.name)
            except OSError:
                pass

    def _accepts(self, port: int) -> bool:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.3):
                return True
        except OSError:
            return False

    def _wait_health(self, port: int) -> None:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            try:
                with opener.open(f"http://127.0.0.1:{port}/api/health", timeout=0.3) as resp:
                    if resp.status == 200:
                        return
            except OSError:
                time.sleep(0.05)
        self.fail(f"server on {port} did not become ready")


_LEFTOVER_SERVER = """
import os, sys, time
sys.path.insert(0, os.environ["ARKPLOTS_ROOT"])
import server
http, _url = server.prepare_server(0)
server.serve_in_background(http)
print(http.server_address[1], flush=True)
time.sleep(20)
"""


if __name__ == "__main__":
    unittest.main()
