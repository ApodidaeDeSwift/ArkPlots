"""Sanity checks for Inno Setup script syntax-sensitive sections."""
from __future__ import annotations

import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ISS_PATH = os.path.join(ROOT, "packaging", "ArkPlots.iss")


class InnoSyntaxTests(unittest.TestCase):
    def test_no_nested_constants_inside_brace_comment(self) -> None:
        with open(ISS_PATH, encoding="utf-8") as handle:
            iss = handle.read()
        self.assertIsNone(re.search(r"\{[^}\r\n]*\{[A-Za-z]+\\", iss))


if __name__ == "__main__":
    unittest.main()
