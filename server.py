#!/usr/bin/env python3
"""ArkPlots local HTTP server (stdlib only).

Serves:
  GET  /api/plots     -> Plotline.json
  GET  /api/records   -> Read_record.json
  PUT  /api/records   -> write Read_record.json (JSON body)
  static files from web/dist (production UI)
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List
from urllib.parse import urlparse


def get_app_dir() -> str:
    """Directory for user data (Plotline.json / Read_record.json).

    When frozen, this is the folder containing the .exe so data stays editable
    next to the binary.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def get_static_dir() -> str:
    """Directory for the built Web UI (web/dist).

    When frozen, prefer the bundle extracted under ``sys._MEIPASS``; fall back
    to ``<exe_dir>/web/dist`` for side-by-side installs.
    """
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            bundled = os.path.join(meipass, "web", "dist")
            if os.path.isdir(bundled):
                return bundled
        return os.path.join(get_app_dir(), "web", "dist")
    return os.path.join(get_app_dir(), "web", "dist")


WORKDIR = get_app_dir()
PLOTLINE_PATH = os.path.join(WORKDIR, "Plotline.json")
READ_RECORD_PATH = os.path.join(WORKDIR, "Read_record.json")
STATIC_DIR = get_static_dir()
DEFAULT_PORT = 8765


def load_json(path: str) -> Any:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        if not content.strip():
            return None
        return json.loads(content)


def save_json(path: str, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def ensure_read_record(plots: List[Dict[str, Any]]) -> Dict[str, str]:
    data = load_json(READ_RECORD_PATH)
    if not isinstance(data, dict):
        data = {}
    changed = False
    for p in plots:
        pid = p.get("id")
        if pid is None:
            continue
        key = str(pid)
        if key not in data:
            data[key] = "未读"
            changed = True
    if changed or not os.path.exists(READ_RECORD_PATH):
        save_json(READ_RECORD_PATH, data)
    return {str(k): str(v) for k, v in data.items()}


class ArkPlotsHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send_json(self, code: int, payload: Any) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, PUT, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return b""
        return self.rfile.read(length)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, PUT, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/plots":
            data = load_json(PLOTLINE_PATH)
            if data is None:
                self._send_json(404, {"error": f"Plotline.json not found at {PLOTLINE_PATH}"})
                return
            self._send_json(200, data)
            return

        if path == "/api/records":
            plotdata = load_json(PLOTLINE_PATH) or {}
            plots = plotdata.get("data") or []
            records = ensure_read_record(plots if isinstance(plots, list) else [])
            self._send_json(200, records)
            return

        if path == "/api/health":
            self._send_json(200, {"ok": True})
            return

        # SPA fallback: serve index.html for non-file routes when dist exists
        if not os.path.isdir(STATIC_DIR):
            self._send_json(
                503,
                {
                    "error": "UI not built",
                    "hint": "Run: cd web && npm install && npm run build",
                },
            )
            return

        # map / to index.html; try file first
        rel = path.lstrip("/") or "index.html"
        candidate = os.path.normpath(os.path.join(STATIC_DIR, rel))
        if not candidate.startswith(os.path.normpath(STATIC_DIR)):
            self.send_error(403)
            return
        if os.path.isdir(candidate):
            candidate = os.path.join(candidate, "index.html")
        if not os.path.isfile(candidate):
            candidate = os.path.join(STATIC_DIR, "index.html")
        if not os.path.isfile(candidate):
            self.send_error(404)
            return

        ctype = mimetypes.guess_type(candidate)[0] or "application/octet-stream"
        try:
            with open(candidate, "rb") as f:
                body = f.read()
        except OSError:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_PUT(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/records":
            self.send_error(404)
            return
        try:
            raw = self._read_body()
            data = json.loads(raw.decode("utf-8"))
            if not isinstance(data, dict):
                self._send_json(400, {"error": "body must be a JSON object"})
                return
            clean = {str(k): str(v) for k, v in data.items()}
            save_json(READ_RECORD_PATH, clean)
            self._send_json(200, clean)
        except json.JSONDecodeError:
            self._send_json(400, {"error": "invalid JSON"})
        except Exception as e:
            self._send_json(500, {"error": str(e)})


def run_server(port: int = DEFAULT_PORT, open_browser: bool = True) -> ThreadingHTTPServer:
    # ensure records exist
    plotdata = load_json(PLOTLINE_PATH) or {}
    plots = plotdata.get("data") or []
    if isinstance(plots, list):
        ensure_read_record(plots)

    server, bound_port = _bind_server(port)
    url = f"http://127.0.0.1:{bound_port}/"
    if bound_port != port:
        print(
            f"Port {port} is unavailable; using {bound_port} instead.\n"
            f"端口 {port} 不可用，已自动改用 {bound_port}。"
        )
    print(f"ArkPlots server at {url}")
    if not os.path.isdir(STATIC_DIR):
        print(
            "WARNING: web/dist missing. Build UI with: "
            "cd web && npm install && npm run build"
        )
    if open_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server.server_close()
    return server


def _bind_server(
    preferred_port: int,
    host: str = "127.0.0.1",
    tries: int = 30,
) -> tuple[ThreadingHTTPServer, int]:
    """Bind to preferred_port, or the next free ports if it is busy/blocked."""
    last_error: OSError | None = None
    for offset in range(max(1, tries)):
        port = preferred_port + offset
        if port > 65535:
            break
        try:
            server = ThreadingHTTPServer((host, port), ArkPlotsHandler)
            return server, port
        except OSError as exc:
            last_error = exc
            continue
    msg = (
        f"Could not bind any port in {preferred_port}..{preferred_port + tries - 1}. "
        f"Last error: {last_error}"
    )
    raise OSError(msg) from last_error


def main() -> None:
    parser = argparse.ArgumentParser(description="ArkPlots local web server")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    try:
        run_server(port=args.port, open_browser=not args.no_browser)
    except OSError as exc:
        print(f"ERROR: failed to start ArkPlots server.\n错误：无法启动服务。\n{exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
