"""Static responses stay executable when Windows maps scripts to text/plain."""
from __future__ import annotations

import os
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from server import (  # noqa: E402
    _bind_server,
    serve_in_background,
    static_content_type,
    stop_server,
)


class StaticContentTypeTests(unittest.TestCase):
    def test_known_types_ignore_registry(self) -> None:
        def fail(*_args, **_kwargs):
            raise AssertionError("known web types must not consult mimetypes")

        cases = {
            r"E:\dist\assets\index-Ab12.js": "text/javascript; charset=utf-8",
            r"E:\foo.bar\模块\app.JS": "text/javascript; charset=utf-8",
            "app.mjs": "text/javascript; charset=utf-8",
            "app.cjs": "text/javascript; charset=utf-8",
            "theme.css": "text/css; charset=utf-8",
            "index.html": "text/html; charset=utf-8",
            "index.htm": "text/html; charset=utf-8",
            "favicon.svg": "image/svg+xml",
            "mod.wasm": "application/wasm",
            "covers/covers.json": "application/json; charset=utf-8",
            "assets/index.js.map": "application/json; charset=utf-8",
            "readme.txt": "text/plain; charset=utf-8",
            "coffee.png": "image/png",
            "cover.jpg": "image/jpeg",
            "cover.jpeg": "image/jpeg",
            "anim.gif": "image/gif",
            "cover.webp": "image/webp",
            "favicon.ico": "image/x-icon",
            "font.woff": "font/woff",
            "font.woff2": "font/woff2",
        }
        with patch("server.mimetypes.guess_type", side_effect=fail):
            for path, expected in cases.items():
                self.assertEqual(static_content_type(path), expected, path)

    def test_text_plain_registry_cannot_relabel_scripts(self) -> None:
        with patch("server.mimetypes.guess_type", return_value=("text/plain", None)):
            for name in ("app.js", "app.mjs", "app.cjs", "theme.css", "index.html"):
                ctype = static_content_type(name)
                self.assertNotEqual(ctype, "text/plain", name)
                self.assertFalse(ctype.startswith("text/plain"), name)

    def test_unknown_extension_uses_guess(self) -> None:
        with patch(
            "server.mimetypes.guess_type",
            return_value=("application/x-custom", None),
        ) as guess:
            self.assertEqual(static_content_type("data.bin"), "application/x-custom")
        guess.assert_called()

    def test_unknown_extension_without_guess_is_octet_stream(self) -> None:
        with patch("server.mimetypes.guess_type", return_value=(None, None)):
            self.assertEqual(
                static_content_type("data.bin"),
                "application/octet-stream",
            )


class StaticResponseMimeTests(unittest.TestCase):
    """GET/HEAD headers when guess_type mimics the broken Windows registry."""

    index_body = b"<!doctype html><div id=root>shell</div>"
    js_body = b"console.log('js')"
    mjs_body = b"export const flag = 'ok'\n"

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = self.tmp.name
        files = {
            "index.html": self.index_body,
            "assets/app.js": self.js_body,
            "assets/app.mjs": self.mjs_body,
            "assets/app.css": b"body{color:red}",
            "assets/app.wasm": b"\x00asm",
            "favicon.svg": b"<svg xmlns='http://www.w3.org/2000/svg'></svg>",
            "covers/covers.json": b'{"1":"covers/1.png"}',
            "coffee.png": b"\x89PNG\r\n\x1a\n",
            "readme.txt": "说明".encode("utf-8"),
            "data.bin": b"\x00\x01",
        }
        for rel, body in files.items():
            path = os.path.join(root, *rel.split("/"))
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as handle:
                handle.write(body)

        self.static_patch = patch("server.STATIC_DIR", root)
        self.mime_patch = patch(
            "server.mimetypes.guess_type",
            return_value=("text/plain", None),
        )
        self.static_patch.start()
        self.mime_patch.start()
        self.addCleanup(self.mime_patch.stop)
        self.addCleanup(self.static_patch.stop)

        self.server, self.port = _bind_server(0, tries=1)
        self.addCleanup(lambda: stop_server(self.server))
        serve_in_background(self.server)

    def _fetch(self, path: str, method: str = "GET") -> tuple[str, bytes]:
        url = f"http://127.0.0.1:{self.port}{path}"
        req = urllib.request.Request(url, method=method)
        deadline = time.time() + 3
        last: Exception | None = None
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(req, timeout=1) as resp:
                    ctype = resp.headers.get("Content-Type", "")
                    return ctype, resp.read()
            except urllib.error.HTTPError as exc:
                try:
                    body = exc.read()
                finally:
                    exc.close()
                return exc.headers.get("Content-Type", ""), body
            except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
                last = exc
                time.sleep(0.05)
        raise AssertionError(f"{method} {path} failed: {last}")

    def test_module_scripts_are_javascript_despite_registry(self) -> None:
        js_type, js_body = self._fetch("/assets/app.js")
        mjs_type, mjs_body = self._fetch("/assets/app.mjs")
        self.assertEqual(js_type, "text/javascript; charset=utf-8")
        self.assertEqual(js_body, self.js_body)
        self.assertEqual(mjs_type, "text/javascript; charset=utf-8")
        self.assertEqual(mjs_body, self.mjs_body)

    def test_head_uses_the_same_script_type(self) -> None:
        ctype, body = self._fetch("/assets/app.js", method="HEAD")
        self.assertEqual(ctype, "text/javascript; charset=utf-8")
        self.assertEqual(body, b"")

    def test_style_document_svg_wasm_and_json(self) -> None:
        css_type, _css = self._fetch("/assets/app.css")
        html_type, html_body = self._fetch("/")
        index_type, index_body = self._fetch("/index.html")
        svg_type, _svg = self._fetch("/favicon.svg")
        wasm_type, _wasm = self._fetch("/assets/app.wasm")
        json_type, _json = self._fetch("/covers/covers.json")
        png_type, _png = self._fetch("/coffee.png")
        txt_type, txt_body = self._fetch("/readme.txt")
        self.assertEqual(css_type, "text/css; charset=utf-8")
        self.assertEqual(html_type, "text/html; charset=utf-8")
        self.assertEqual(html_body, self.index_body)
        self.assertEqual(index_type, "text/html; charset=utf-8")
        self.assertEqual(index_body, self.index_body)
        self.assertEqual(svg_type, "image/svg+xml")
        self.assertEqual(wasm_type, "application/wasm")
        self.assertEqual(json_type, "application/json; charset=utf-8")
        self.assertEqual(png_type, "image/png")
        self.assertEqual(txt_type, "text/plain; charset=utf-8")
        self.assertEqual(txt_body.decode("utf-8"), "说明")

    def test_missing_script_falls_back_to_html(self) -> None:
        ctype, body = self._fetch("/assets/missing.js")
        self.assertEqual(ctype, "text/html; charset=utf-8")
        self.assertEqual(body, self.index_body)
        route_type, route_body = self._fetch("/plots/12")
        self.assertEqual(route_type, "text/html; charset=utf-8")
        self.assertEqual(route_body, self.index_body)

    def test_unknown_extension_still_follows_guess(self) -> None:
        ctype, body = self._fetch("/data.bin")
        self.assertEqual(ctype, "text/plain")
        self.assertEqual(body, b"\x00\x01")

    def test_api_json_is_unchanged(self) -> None:
        ctype, body = self._fetch("/api/health")
        self.assertEqual(ctype, "application/json; charset=utf-8")
        self.assertIn(b'"ok"', body)


if __name__ == "__main__":
    unittest.main()
