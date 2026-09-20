"""Bind the real listening port, and check the window launcher uses that URL."""
from __future__ import annotations

import os
import socket
import sys
import unittest
from unittest.mock import MagicMock, patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from server import _bind_server, listening_url, stop_server  # noqa: E402


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


class WindowLaunchTests(unittest.TestCase):
    def test_launch_window_opens_bound_url_and_stops(self) -> None:
        import main

        http = MagicMock()
        url = "http://127.0.0.1:18080/"
        with (
            patch("server.prepare_server", return_value=(http, url)),
            patch("server.serve_in_background") as background,
            patch("server.stop_server") as stop,
            patch.object(main, "_wait_until_ready") as wait,
            patch.object(main, "_open_webview") as open_window,
        ):
            main.launch_window(8765)
        background.assert_called_once_with(http)
        wait.assert_called_once_with(url)
        open_window.assert_called_once_with(url)
        stop.assert_called_once_with(http)

    def test_launch_window_stops_server_when_window_fails(self) -> None:
        import main

        http = MagicMock()
        url = "http://127.0.0.1:18081/"
        with (
            patch("server.prepare_server", return_value=(http, url)),
            patch("server.serve_in_background"),
            patch("server.stop_server") as stop,
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


if __name__ == "__main__":
    unittest.main()
