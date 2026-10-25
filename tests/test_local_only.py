"""The local server refuses foreign origins/hosts and oversized bodies.

The server binds to 127.0.0.1, but browsers treat localhost as trustworthy, so
a random web page can otherwise read/overwrite Read_record.json cross-site
(DNS rebinding forges Host the same way).
"""
from __future__ import annotations

import http.client
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from server import (  # noqa: E402
    _bind_server,
    _host_is_loopback,
    _origin_is_local,
    serve_in_background,
    stop_server,
)


class HostHelpersTests(unittest.TestCase):
    def test_loopback_hosts(self) -> None:
        for header in ("localhost", "localhost:8765", "127.0.0.1", "127.0.0.1:8765",
                       "[::1]:8765", "LOCALHOST:80"):
            self.assertTrue(_host_is_loopback(header), header)

    def test_foreign_hosts(self) -> None:
        for header in ("evil.example", "evil.example:8765", "192.168.1.5:8765", "", None):
            self.assertFalse(_host_is_loopback(header), repr(header))

    def test_origin_locality(self) -> None:
        self.assertTrue(_origin_is_local("http://127.0.0.1:8765"))
        self.assertTrue(_origin_is_local("http://localhost:8765"))
        self.assertFalse(_origin_is_local("https://evil.example"))
        self.assertFalse(_origin_is_local("null"))


class LocalOnlyRequestsTests(unittest.TestCase):
    """End-to-end over a real bound server, forging headers with http.client."""

    def setUp(self) -> None:
        self.server, self.port = _bind_server(0, tries=1)
        serve_in_background(self.server)
        self.addCleanup(stop_server, self.server)

    def _request(self, method: str, path: str, headers=None, body=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            conn.request(method, path, body=body, headers=headers or {})
            resp = conn.getresponse()
            return resp.status, resp.read()
        finally:
            conn.close()

    def test_local_get_without_origin_is_served(self) -> None:
        status, body = self._request("GET", "/api/health")
        self.assertEqual(status, 200)
        self.assertIn(b'"ok"', body)

    def test_same_origin_get_is_served(self) -> None:
        status, _ = self._request(
            "GET", "/api/health", headers={"Origin": f"http://127.0.0.1:{self.port}"}
        )
        self.assertEqual(status, 200)

    def test_foreign_origin_get_is_refused(self) -> None:
        status, body = self._request(
            "GET", "/api/health", headers={"Origin": "https://evil.example"}
        )
        self.assertEqual(status, 403)
        self.assertIn(b"local_only", body)

    def test_foreign_host_get_is_refused(self) -> None:
        status, _ = self._request(
            "GET", "/api/health", headers={"Host": "evil.example:8765"}
        )
        self.assertEqual(status, 403)

    def test_foreign_origin_put_cannot_touch_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = os.path.join(tmp, "Read_record.json")
            with open(record, "w", encoding="utf-8") as handle:
                json.dump({"1": "已读"}, handle, ensure_ascii=False)
            with patch("server.READ_RECORD_PATH", record):
                status, body = self._request(
                    "PUT",
                    "/api/records",
                    headers={
                        "Origin": "https://evil.example",
                        "Content-Type": "application/json",
                    },
                    body=json.dumps({"1": "已读", "2": "已读"}).encode("utf-8"),
                )
                self.assertEqual(status, 403)
                with open(record, encoding="utf-8") as handle:
                    self.assertEqual(json.load(handle), {"1": "已读"})

    def test_local_put_still_writes_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = os.path.join(tmp, "Read_record.json")
            with patch("server.READ_RECORD_PATH", record):
                status, body = self._request(
                    "PUT",
                    "/api/records",
                    headers={"Content-Type": "application/json"},
                    body=json.dumps({"5": "已读"}).encode("utf-8"),
                )
                self.assertEqual(status, 200)
                self.assertIn(b'"5"', body)
                with open(record, encoding="utf-8") as handle:
                    self.assertEqual(json.load(handle), {"5": "已读"})

    def test_oversized_put_is_rejected_as_413(self) -> None:
        status, body = self._request(
            "PUT",
            "/api/records",
            headers={
                "Content-Type": "application/json",
                "Content-Length": str(6 * 1024 * 1024),
                "Connection": "close",
            },
            body=b"",
        )
        self.assertEqual(status, 413)
        self.assertIn(b"too large", body)


if __name__ == "__main__":
    unittest.main()
