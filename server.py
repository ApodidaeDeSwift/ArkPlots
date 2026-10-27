#!/usr/bin/env python3
"""ArkPlots local HTTP server (stdlib only).

Serves:
  GET  /api/plots     -> Plotline.json
  GET  /api/records   -> Read_record.json
  PUT  /api/records   -> write Read_record.json (JSON body)
  GET  /api/version   -> app identity / version (for UI + updates)
  GET  /api/update/check -> find newest APP_Ver* GitHub tag and compare versions
  POST /api/update/apply -> download release exe and schedule safe replace
  POST /api/update/exit  -> restart after the UI has shown release notes
  POST /api/shutdown  -> local-only, token required; exit and release the port
  GET  /api/health    -> liveness
  static files from web/dist (production UI)
"""
from __future__ import annotations

import atexit
import argparse
import json
import mimetypes
import os
import signal
import socket
import struct
import sys
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List
from urllib.parse import parse_qs, urlparse

# Windowed builds (PyInstaller console=False) have no stdio. Keep writes safe.
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8", errors="replace")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8", errors="replace")

try:
    from app_info import is_packaged, version_payload
except ImportError:  # pragma: no cover - extremely old checkouts
    def version_payload() -> Dict[str, Any]:
        return {"name": "ArkPlots", "version": "0.0.0", "channel": "dev"}

    def is_packaged() -> bool:
        return bool(getattr(sys, "frozen", False)) or hasattr(sys, "_MEIPASS")

try:
    from updater import (
        apply_update,
        check_for_update,
        register_before_process_exit,
        request_update_exit,
    )
except ImportError:  # pragma: no cover
    def register_before_process_exit(callback) -> None:
        return None

    def check_for_update() -> Dict[str, Any]:
        return {"ok": False, "error": "updater_missing"}

    def apply_update(*, restart: bool = True, defer_exit: bool = False) -> Dict[str, Any]:
        return {"ok": False, "error": "updater_missing"}

    def request_update_exit() -> Dict[str, Any]:
        return {"ok": False, "error": "updater_missing"}


def get_app_dir() -> str:
    """Directory for user data (Plotline.json / Read_record.json).

    When frozen, this is the folder containing the .exe so data stays editable
    next to the binary.
    """
    if is_packaged():
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def get_static_dir() -> str:
    """Directory for the built Web UI (web/dist).

    When frozen, prefer the bundle extracted under ``sys._MEIPASS``; fall back
    to ``<exe_dir>/web/dist`` for side-by-side installs.
    """
    if is_packaged():
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

# Browsers refuse to sniff these. On Windows, mimetypes.guess_type() copies
# HKEY_CLASSES_ROOT, which often maps .js / .mjs / .cjs to text/plain. A module
# script with that type never runs, so the page stays blank. Stylesheets, SVG,
# and Wasm fail for the same reason when the registry type is wrong.
_STATIC_CONTENT_TYPES = {
    ".js": "text/javascript; charset=utf-8",
    ".mjs": "text/javascript; charset=utf-8",
    ".cjs": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".html": "text/html; charset=utf-8",
    ".htm": "text/html; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".map": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".wasm": "application/wasm",
    ".txt": "text/plain; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".ico": "image/x-icon",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
}


def static_content_type(path: str) -> str:
    """Content-Type for a static file, ignoring the OS MIME database."""
    ext = os.path.splitext(path)[1].lower()
    fixed = _STATIC_CONTENT_TYPES.get(ext)
    if fixed:
        return fixed
    guessed = mimetypes.guess_type(path)[0]
    return guessed or "application/octet-stream"


# Reading records are small; anything bigger is abuse, not a sync payload.
_MAX_BODY_BYTES = 5 * 1024 * 1024


class BodyTooLarge(ValueError):
    """Raised when Content-Length exceeds _MAX_BODY_BYTES."""

_LOOPBACK_NAMES = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}


def _host_is_loopback(host_header: str | None) -> bool:
    """True when the Host header names this machine (DNS-rebinding guard)."""
    host = (host_header or "").strip().lower()
    if not host:
        return False
    if host.startswith("["):  # IPv6 literal like [::1]:8765
        host = host[1:].split("]", 1)[0]
    else:
        host = host.split(":", 1)[0]
    return host in _LOOPBACK_NAMES


def _origin_is_local(origin: str) -> bool:
    """True when an Origin header points back at localhost (any port)."""
    host = (urlparse(origin).hostname or "").lower()
    return host in _LOOPBACK_NAMES


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
    """Ensure every Plotline id has a Read_record entry (default 「未读」).

    Called on server start and on GET /api/records so newly added plots after
    an update are written into Read_record.json without clearing existing status.
    """
    data = load_json(READ_RECORD_PATH)
    if not isinstance(data, dict):
        data = {}
    # Normalize keys to str so "12" and 12 never diverge across reloads.
    normalized: Dict[str, str] = {str(k): str(v) for k, v in data.items()}
    changed = len(normalized) != len(data) or any(
        not isinstance(k, str) for k in data.keys()
    )
    for p in plots:
        if not isinstance(p, dict):
            continue
        pid = p.get("id")
        if pid is None or pid == "":
            continue
        key = str(pid)
        if key not in normalized:
            normalized[key] = "未读"
            changed = True
    if changed or not os.path.exists(READ_RECORD_PATH):
        save_json(READ_RECORD_PATH, normalized)
    return normalized


class ArkPlotsHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def guess_type(self, path: str) -> str:
        # do_HEAD still serves files through SimpleHTTPRequestHandler.send_head.
        return static_content_type(path)

    def log_message(self, fmt: str, *args) -> None:
        stream = sys.stderr
        if stream is None:
            return
        try:
            stream.write("%s - %s\n" % (self.address_string(), fmt % args))
        except Exception:
            pass

    def _write(self, body: bytes) -> None:
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
            return

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
        self._write(body)

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return b""
        if length > _MAX_BODY_BYTES:
            raise BodyTooLarge(f"request body too large: {length} bytes")
        return self.rfile.read(length)

    def _reject_foreign(self) -> bool:
        """Refuse requests that did not originate on this machine.

        The server binds to 127.0.0.1 only, but browsers treat http://localhost
        as a trustworthy origin, so a random web page can still try to read or
        overwrite Read_record.json cross-site (and DNS rebinding forges Host).
        Requests without an Origin header (pywebview, urllib, same-origin GET)
        are allowed as long as Host names localhost.
        """
        origin = self.headers.get("Origin")
        if origin and origin != "null" and not _origin_is_local(origin):
            return True
        if not _host_is_loopback(self.headers.get("Host")):
            return True
        return False

    def do_OPTIONS(self) -> None:
        if self._reject_foreign():
            self._send_json(403, {"error": "local_only"})
            return
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, PUT, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        if self._reject_foreign():
            self._send_json(403, {"error": "local_only"})
            return
        try:
            self._do_GET()
        except Exception as exc:
            try:
                self._send_json(500, {"error": str(exc)})
            except Exception:
                pass

    def _do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/plots":
            data = load_json(PLOTLINE_PATH)
            if data is None:
                self._send_json(404, {"error": f"Plotline.json not found at {PLOTLINE_PATH}"})
                return
            plots = data.get("data") if isinstance(data, dict) else None
            if isinstance(plots, list):
                ensure_read_record(plots)
            self._send_json(200, data)
            return

        if path == "/api/records":
            plotdata = load_json(PLOTLINE_PATH) or {}
            plots = plotdata.get("data") or []
            records = ensure_read_record(plots if isinstance(plots, list) else [])
            self._send_json(200, records)
            return

        if path == "/api/health":
            self._send_json(200, {"ok": True, "name": "ArkPlots", "pid": os.getpid()})
            return

        if path == "/api/version":
            self._send_json(200, version_payload())
            return

        if path == "/api/update/check":
            channel = parse_qs(parsed.query).get("channel", ["release"])[0]
            include_prerelease = str(channel).strip().lower() == "preview"
            self._send_json(200, check_for_update(include_prerelease=include_prerelease))
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

        ctype = self.guess_type(candidate)
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
        self._write(body)

    def do_POST(self) -> None:
        if self._reject_foreign():
            self._send_json(403, {"error": "local_only"})
            return
        parsed = urlparse(self.path)
        if parsed.path == "/api/shutdown":
            # A web page on localhost can POST here; the token is only in the
            # instance file, which that page cannot read.
            token = self.headers.get("X-ArkPlots-Token") or ""
            from listener import current_token

            if not token or token != current_token():
                self._send_json(403, {"ok": False, "error": "forbidden"})
                return
            self._send_json(200, {"ok": True})
            request_listener_shutdown()
            return
        if parsed.path == "/api/update/exit":
            try:
                result = request_update_exit()
                self._send_json(200 if result.get("ok") else 409, result)
            except Exception as e:
                self._send_json(500, {"ok": False, "error": str(e)})
            return
        if parsed.path != "/api/update/apply":
            self.send_error(404)
            return
        restart = True
        defer_exit = False
        include_prerelease = False
        try:
            raw = self._read_body()
            if raw.strip():
                data = json.loads(raw.decode("utf-8"))
                if isinstance(data, dict):
                    if "restart" in data:
                        restart = bool(data.get("restart"))
                    if "defer_exit" in data:
                        defer_exit = bool(data.get("defer_exit"))
                    include_prerelease = str(data.get("channel") or "").strip().lower() == "preview"
        except Exception:
            restart = True
            defer_exit = False
            include_prerelease = False
        try:
            result = apply_update(
                restart=restart,
                defer_exit=defer_exit,
                include_prerelease=include_prerelease,
            )
            code = 200 if result.get("ok") and result.get("applied") else 200
            # Still 200 for soft failures (up to date / no asset) so UI can show message.
            if result.get("error") in ("network_error", "http_error", "download_failed"):
                code = 502
            self._send_json(code, result)
        except Exception as e:
            self._send_json(500, {"ok": False, "error": str(e)})

    def do_PUT(self) -> None:
        if self._reject_foreign():
            self._send_json(403, {"error": "local_only"})
            return
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
        except BodyTooLarge as e:
            self._send_json(413, {"error": str(e)})
        except json.JSONDecodeError:
            self._send_json(400, {"error": "invalid JSON"})
        except Exception as e:
            self._send_json(500, {"error": str(e)})


def listening_url(server: ThreadingHTTPServer) -> str:
    """URL for the port the server actually bound, not the requested one."""
    host, port = server.server_address[:2]
    if not isinstance(host, str) or host in ("0.0.0.0", "::", ""):
        host = "127.0.0.1"
    return f"http://{host}:{port}/"


_active_server: ThreadingHTTPServer | None = None
_exit_hooks_installed = False
_EXIT_ON_SHUTDOWN_ENV = "ARKPLOTS_EXIT_ON_SHUTDOWN"


def _close_listening_socket() -> None:
    """Unblock ``serve_forever`` without waiting for it.

    ``HTTPServer.shutdown()`` waits until the serve loop finishes. Calling it
    from that same thread (Ctrl+C during ``run_server``) deadlocks, so signal
    handlers only close the socket.
    """
    server = _active_server
    if server is not None:
        try:
            server.socket.close()
        except Exception:
            pass
    from listener import clear_instance

    clear_instance()


def _release_listener() -> None:
    """Close the listening socket and drop our instance record."""
    server = _active_server
    if server is not None:
        stop_server(server)
    from listener import clear_instance

    clear_instance()


def _close_windows() -> None:
    try:
        import webview

        for win in list(getattr(webview, "windows", []) or []):
            try:
                win.destroy()
            except Exception:
                pass
    except Exception:
        pass


def _exit_on_shutdown() -> bool:
    return os.environ.get(_EXIT_ON_SHUTDOWN_ENV, "1") != "0"


def request_listener_shutdown() -> None:
    """Leave the port after the shutdown response has been written.

    A later start can then bind the same port. When this is the real app,
    the process exits so a window cannot stay up without its server.
    """

    def _run() -> None:
        import time

        time.sleep(0.2)
        _release_listener()
        _close_windows()
        if _exit_on_shutdown():
            os._exit(0)

    threading.Thread(target=_run, name="arkplots-shutdown", daemon=True).start()


def _install_exit_hooks() -> None:
    """Release the port on Ctrl+C, console close, and normal interpreter exit."""
    global _exit_hooks_installed
    if _exit_hooks_installed:
        return
    _exit_hooks_installed = True
    atexit.register(_release_listener)

    def _on_signal(signum: int, frame: Any) -> None:
        _close_listening_socket()
        if signum == signal.SIGINT:
            raise KeyboardInterrupt
        raise SystemExit(0)

    for sig in (signal.SIGINT, signal.SIGTERM, getattr(signal, "SIGBREAK", None)):
        if sig is None:
            continue
        try:
            signal.signal(sig, _on_signal)
        except (OSError, ValueError):
            pass

    if sys.platform == "win32":
        _install_console_close_handler()


def _install_console_close_handler() -> None:
    import ctypes
    from ctypes import wintypes

    handler_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.DWORD)

    def _handler(ctrl_type: int) -> bool:
        # CTRL_C, CTRL_BREAK, CLOSE, LOGOFF, SHUTDOWN.
        if ctrl_type in (0, 1, 2, 5, 6):
            _close_listening_socket()
        return False

    global _console_ctrl_handler
    _console_ctrl_handler = handler_type(_handler)
    ctypes.windll.kernel32.SetConsoleCtrlHandler(_console_ctrl_handler, True)


def prepare_server(port: int = DEFAULT_PORT) -> tuple[ThreadingHTTPServer, str]:
    """Bind the HTTP server (falling forward if the port is busy) and return (server, url).

    Does not serve yet. The URL always uses the port stored on the socket.
    A previous ArkPlots process still listening on ``port`` is closed first.
    """
    global _active_server
    from listener import publish_instance, reclaim_arkplots_port

    plotdata = load_json(PLOTLINE_PATH) or {}
    plots = plotdata.get("data") or []
    if isinstance(plots, list):
        ensure_read_record(plots)

    reclaim_arkplots_port("127.0.0.1", port)
    server, bound_port = _bind_server(port)
    publish_instance(bound_port)
    _active_server = server
    register_before_process_exit(_release_listener)
    url = listening_url(server)
    if port != 0 and bound_port != port:
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
    return server, url


def serve_in_background(server: ThreadingHTTPServer) -> threading.Thread:
    """Run serve_forever on a daemon thread so the GUI can own the main thread."""
    atexit.register(stop_server, server)
    thread = threading.Thread(
        target=server.serve_forever,
        name="arkplots-http",
        daemon=True,
    )
    server._arkplots_thread = thread  # type: ignore[attr-defined]
    thread.start()
    return thread


def stop_server(server: ThreadingHTTPServer) -> None:
    """Stop the HTTP server. Safe to call more than once.

    ``HTTPServer.shutdown()`` deadlocks unless ``serve_forever()`` is running
    in another thread, so it is only used after ``serve_in_background``.
    """
    lock = getattr(server, "_arkplots_stop_lock", None)
    if lock is None:
        lock = threading.Lock()
        server._arkplots_stop_lock = lock  # type: ignore[attr-defined]
    with lock:
        if getattr(server, "_arkplots_stopped", False):
            return
        server._arkplots_stopped = True  # type: ignore[attr-defined]
    thread = getattr(server, "_arkplots_thread", None)
    if thread is not None:
        try:
            server.shutdown()
        except Exception:
            pass
        try:
            thread.join(timeout=3)
        except Exception:
            pass
    try:
        server.server_close()
    except Exception:
        pass
    from listener import clear_instance

    clear_instance()


def run_server(port: int = DEFAULT_PORT, open_browser: bool = True) -> ThreadingHTTPServer:
    _install_exit_hooks()
    server, url = prepare_server(port)
    if open_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        stop_server(server)
    return server


def _probe_health(host: str, port: int, timeout: float = 0.35) -> bool:
    """True if something on host:port already answers ArkPlots /api/health."""
    import urllib.error
    import urllib.request

    url = f"http://{host}:{port}/api/health"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            if getattr(resp, "status", 200) != 200:
                return False
            body = resp.read(64)
            return b'"ok"' in body or b"true" in body
    except (OSError, urllib.error.URLError, ValueError):
        return False


def _tcp_accepts(host: str, port: int, timeout: float = 0.25) -> bool:
    """True if a TCP connect to host:port succeeds (listener present)."""
    import socket

    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


class ArkPlotsServer(ThreadingHTTPServer):
    """Local server that refuses to share its port with another process.

    ``http.server.HTTPServer`` sets ``allow_reuse_address = True``. On Windows
    that is ``SO_REUSEADDR``, and a second process can then also listen on
    127.0.0.1:8765. The kernel delivers each connection to only one of them,
    so a leftover ``python server.py`` can answer every request while the
    installed exe sits on the same port and never sees them. The window then
    shows the source process's version and refuses one-click update.
    """

    allow_reuse_address = False
    allow_reuse_port = False

    def server_bind(self) -> None:
        if sys.platform == "win32":
            exclusive = getattr(socket, "SO_EXCLUSIVEADDRUSE", None)
            if exclusive is not None:
                self.socket.setsockopt(socket.SOL_SOCKET, exclusive, 1)
        # Drop the port as soon as the process closes the socket, instead of
        # leaving it in TIME_WAIT for the next launch.
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
        super().server_bind()

    def serve_forever(self, poll_interval: float = 0.1) -> None:  # type: ignore[override]
        super().serve_forever(poll_interval=poll_interval)


def _bind_server(
    preferred_port: int,
    host: str = "127.0.0.1",
    tries: int = 30,
) -> tuple[ThreadingHTTPServer, int]:
    """Bind to preferred_port, or the next free ports if it is busy/blocked.

    The returned port is the one the socket actually got (important when the
    caller asked for port 0, or when the OS remaps the bind).

    Ports that accept TCP but do not answer /api/health are treated as dead
    listeners (common cause of ERR_EMPTY_RESPONSE) and skipped when possible.
    """
    last_error: OSError | None = None
    for offset in range(max(1, tries)):
        port = preferred_port + offset
        if port > 65535:
            break
        # Never attach to a port that already accepts connections. Binding
        # again used to succeed on Windows and split requests with the
        # process that was already there.
        if port != 0 and _tcp_accepts(host, port):
            if _probe_health(host, port):
                print(
                    f"Port {port} is already serving ArkPlots; choosing another port.\n"
                    f"端口 {port} 上已有 ArkPlots 在应答，已改用下一个端口，避免两个进程抢同一端口。"
                )
            else:
                print(
                    f"Port {port} accepts connections but is not a healthy ArkPlots server; skipping.\n"
                    f"端口 {port} 可连接但无有效响应（可能是残留进程），已跳过。"
                )
            last_error = OSError(f"port {port} is already in use")
            continue
        try:
            server = ArkPlotsServer((host, port), ArkPlotsHandler)
            server.daemon_threads = True
            actual = int(server.server_address[1])
            return server, actual
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
