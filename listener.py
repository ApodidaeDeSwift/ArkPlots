# -*- coding: utf-8 -*-
"""Own the local port, and close a previous ArkPlots listener that is still up.

A leftover ``python server.py`` or an installed exe that was never closed used
to keep 127.0.0.1:8765. On Windows that socket was shared, so the window
talked to the old process. Starting again now asks that process to exit, and
if it does not, stops it, before this process binds the port.
"""
from __future__ import annotations

import json
import os
import socket
import sys
import time
import urllib.error
import urllib.request
from typing import Any

_INSTANCE_ENV = "ARKPLOTS_INSTANCE_FILE"
_TOKEN = ""


def instance_file() -> str:
    """Per-user record of the listener we started (pid, port, shutdown token)."""
    override = os.environ.get(_INSTANCE_ENV)
    if override:
        parent = os.path.dirname(override)
        if parent:
            os.makedirs(parent, exist_ok=True)
        return override
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
    if not base:
        base = os.path.join(os.path.expanduser("~"), ".local", "share")
    folder = os.path.join(base, "ArkPlots")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "instance.json")


def current_token() -> str:
    return _TOKEN


def publish_instance(port: int) -> str:
    """Remember this process as the listener. Returns the shutdown token."""
    global _TOKEN
    import secrets

    _TOKEN = secrets.token_hex(16)
    payload = {
        "name": "ArkPlots",
        "pid": os.getpid(),
        "port": int(port),
        "token": _TOKEN,
    }
    path = instance_file()
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle)
    os.replace(tmp, path)
    return _TOKEN


def _remove_instance_file() -> None:
    try:
        os.remove(instance_file())
    except OSError:
        pass


def clear_instance() -> None:
    """Remove the record only when it still names this process."""
    data = read_instance()
    if not data or int(data.get("pid") or -1) != os.getpid():
        return
    _remove_instance_file()


def read_instance() -> dict[str, Any] | None:
    try:
        with open(instance_file(), "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _opener() -> urllib.request.OpenerDirector:
    # A machine-wide proxy must not swallow 127.0.0.1.
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))


def _tcp_open(host: str, port: int, timeout: float = 0.25) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def app_name_on(host: str, port: int) -> str:
    """``/api/version`` name, or empty when the listener is not ArkPlots."""
    req = urllib.request.Request(f"http://{host}:{port}/api/version", method="GET")
    try:
        with _opener().open(req, timeout=0.5) as resp:
            data = json.loads(resp.read(8192).decode("utf-8", "replace"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError, ValueError, TimeoutError):
        return ""
    if isinstance(data, dict):
        return str(data.get("name") or "")
    return ""


def post_shutdown(host: str, port: int, token: str) -> bool:
    req = urllib.request.Request(
        f"http://{host}:{port}/api/shutdown",
        data=b"{}",
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-ArkPlots-Token": token,
        },
    )
    try:
        with _opener().open(req, timeout=1.0) as resp:
            return int(getattr(resp, "status", 200)) == 200
    except urllib.error.HTTPError as exc:
        exc.close()
        return False
    except (OSError, urllib.error.URLError, TimeoutError):
        return False


def wait_until_closed(host: str, port: int, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not _tcp_open(host, port):
            return True
        time.sleep(0.05)
    return not _tcp_open(host, port)


def listener_pids(host: str, port: int) -> list[int]:
    """PIDs listening on host:port. Empty when the OS cannot be asked."""
    if sys.platform != "win32":
        return []
    try:
        return _windows_listener_pids(host, port)
    except OSError:
        return []


def _windows_listener_pids(host: str, port: int) -> list[int]:
    import ctypes
    import struct
    from ctypes import wintypes

    AF_INET = 2
    TCP_TABLE_OWNER_PID_LISTENER = 3
    ERROR_INSUFFICIENT_BUFFER = 122
    iphlpapi = ctypes.WinDLL("iphlpapi", use_last_error=True)
    get_table = iphlpapi.GetExtendedTcpTable
    get_table.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(wintypes.DWORD),
        wintypes.BOOL,
        wintypes.ULONG,
        ctypes.c_int,
        wintypes.ULONG,
    ]
    get_table.restype = wintypes.DWORD
    size = wintypes.DWORD(0)
    ret = get_table(None, ctypes.byref(size), False, AF_INET, TCP_TABLE_OWNER_PID_LISTENER, 0)
    if ret != ERROR_INSUFFICIENT_BUFFER and ret != 0:
        return []
    buf = ctypes.create_string_buffer(max(int(size.value), 4))
    size = wintypes.DWORD(len(buf))
    ret = get_table(buf, ctypes.byref(size), False, AF_INET, TCP_TABLE_OWNER_PID_LISTENER, 0)
    if ret != 0:
        return []
    count = struct.unpack_from("<I", buf.raw, 0)[0]
    want_addr = socket.inet_aton(host)
    found: list[int] = []
    for index in range(count):
        state, local_addr, local_port, _remote_addr, _remote_port, pid = struct.unpack_from(
            "<IIIIII", buf.raw, 4 + index * 24
        )
        del state
        addr = struct.pack("<I", local_addr)
        local = socket.ntohs(local_port & 0xFFFF)
        if addr == want_addr and local == port and pid not in found:
            found.append(int(pid))
    return found


def process_image(pid: int) -> str:
    if sys.platform != "win32" or pid <= 0:
        return ""
    import ctypes
    from ctypes import wintypes

    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return ""
    try:
        size = wintypes.DWORD(32768)
        buf = ctypes.create_unicode_buffer(size.value)
        ok = kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size))
        if not ok:
            return ""
        return buf.value
    finally:
        kernel32.CloseHandle(handle)


def may_stop(pid: int) -> bool:
    """True for another ArkPlots.exe or a python process, never for ourselves."""
    if pid <= 0 or pid == os.getpid():
        return False
    name = os.path.basename(process_image(pid)).lower()
    return name in {"arkplots.exe", "python.exe", "pythonw.exe"}


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if sys.platform != "win32":
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        return True
    import ctypes
    from ctypes import wintypes

    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    STILL_ACTIVE = 259
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return False
    try:
        code = wintypes.DWORD()
        if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
            return False
        return int(code.value) == STILL_ACTIVE
    finally:
        kernel32.CloseHandle(handle)


def terminate_pid(pid: int) -> bool:
    if not may_stop(pid):
        return False
    if sys.platform != "win32":
        try:
            os.kill(pid, 15)
        except OSError:
            return False
        return True
    import ctypes

    PROCESS_TERMINATE = 0x0001
    SYNCHRONIZE = 0x00100000
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    handle = kernel32.OpenProcess(PROCESS_TERMINATE | SYNCHRONIZE, False, pid)
    if not handle:
        return False
    try:
        if not kernel32.TerminateProcess(handle, 1):
            return False
        kernel32.WaitForSingleObject(handle, 3000)
        return True
    finally:
        kernel32.CloseHandle(handle)


def reclaim_arkplots_port(host: str, port: int, timeout: float = 4.0) -> None:
    """Close a previous ArkPlots listener on this port, if one is still there.

    Anything that does not answer ``/api/version`` as ArkPlots is left alone.
    This process is never terminated.
    """
    if port <= 0 or port > 65535 or not _tcp_open(host, port):
        return
    if app_name_on(host, port) != "ArkPlots":
        return

    record = read_instance()
    token = ""
    if record and int(record.get("port") or 0) == port:
        old_pid = int(record.get("pid") or 0)
        if old_pid and pid_alive(old_pid):
            token = str(record.get("token") or "")
        elif old_pid:
            _remove_instance_file()

    if token and post_shutdown(host, port, token):
        if wait_until_closed(host, port, min(timeout, 2.0)):
            return

    stopped = False
    for pid in listener_pids(host, port):
        if not may_stop(pid):
            continue
        print(
            f"Closing previous ArkPlots listener pid {pid} on port {port}.\n"
            f"正在关闭仍占用端口 {port} 的 ArkPlots 进程（pid {pid}）。"
        )
        if terminate_pid(pid):
            stopped = True
    if stopped:
        wait_until_closed(host, port, timeout)
