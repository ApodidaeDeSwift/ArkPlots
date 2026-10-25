"""Pure filter/date/record helpers in main.py (legacy tkinter + CLI paths)."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from datetime import datetime
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import main  # noqa: E402


class NormalizeListFieldTests(unittest.TestCase):
    def test_none_is_empty_list(self) -> None:
        self.assertEqual(main.normalize_list_field(None), [])

    def test_scalar_becomes_single_item_list(self) -> None:
        self.assertEqual(main.normalize_list_field("乌萨斯"), ["乌萨斯"])

    def test_list_drops_none_and_stringifies(self) -> None:
        self.assertEqual(main.normalize_list_field(["a", None, 3]), ["a", "3"])


class ParseDateTests(unittest.TestCase):
    def test_accepts_common_formats(self) -> None:
        for text, expected in (
            ("2026-10-22", datetime(2026, 10, 22)),
            ("2026/10/22", datetime(2026, 10, 22)),
            ("2026.10.22", datetime(2026, 10, 22)),
            ("2026-10", datetime(2026, 10, 1)),
        ):
            self.assertEqual(main.parse_date(text), expected, text)

    def test_blank_and_invalid_return_none(self) -> None:
        self.assertIsNone(main.parse_date("   "))
        self.assertIsNone(main.parse_date("not-a-date"))


class MatchesFiltersTests(unittest.TestCase):
    def setUp(self) -> None:
        self.item = {
            "id": 12,
            "name": "生息演算",
            "class": "RA",
            "date": "2026-01-15",
            "country": ["雨林", "荒野"],
            "plot_stage": 3,
            "new_operator": ["Test Operator"],
            "related_power": ["罗德岛"],
            "related_plot": ["孤星"],
        }

    def test_empty_filters_match_everything(self) -> None:
        self.assertTrue(main.matches_filters(self.item, {}))

    def test_null_date_does_not_crash(self) -> None:
        """Regression: date=null used to raise AttributeError (NoneType.strip)."""
        broken = dict(self.item, date=None)
        self.assertTrue(main.matches_filters(broken, {}))
        self.assertTrue(main.matches_filters(broken, {"start": datetime(2020, 1, 1)}))
        self.assertTrue(main.matches_filters(broken, {"end": datetime(2020, 1, 1)}))

    def test_date_range_boundaries(self) -> None:
        start = datetime(2026, 1, 15)
        end = datetime(2026, 1, 15)
        self.assertTrue(main.matches_filters(self.item, {"start": start, "end": end}))
        self.assertFalse(
            main.matches_filters(self.item, {"start": datetime(2026, 1, 16)})
        )
        self.assertFalse(main.matches_filters(self.item, {"end": datetime(2026, 1, 14)}))

    def test_class_membership(self) -> None:
        self.assertTrue(main.matches_filters(self.item, {"class": ["RA", "main"]}))
        self.assertFalse(main.matches_filters(self.item, {"class": ["main"]}))

    def test_country_any_vs_all(self) -> None:
        filters = {"country": ["雨林", "维多利亚"], "country_mode": "any"}
        self.assertTrue(main.matches_filters(self.item, filters))
        filters["country_mode"] = "all"
        self.assertFalse(main.matches_filters(self.item, filters))
        filters["country"] = ["雨林", "荒野"]
        self.assertTrue(main.matches_filters(self.item, filters))

    def test_new_operator_substring_is_case_insensitive(self) -> None:
        self.assertTrue(main.matches_filters(self.item, {"new_operator": "test"}))
        self.assertFalse(main.matches_filters(self.item, {"new_operator": "silverash"}))

    def test_plot_stage(self) -> None:
        self.assertTrue(main.matches_filters(self.item, {"plot_stage": [3, 4]}))
        self.assertFalse(main.matches_filters(self.item, {"plot_stage": [1]}))
        # Non-numeric stage on the item is excluded from any stage filter.
        self.assertFalse(
            main.matches_filters(dict(self.item, plot_stage="x"), {"plot_stage": [3]})
        )

    def test_related_power_and_plot_modes(self) -> None:
        self.assertTrue(
            main.matches_filters(self.item, {"related_power": ["罗德岛"]})
        )
        self.assertFalse(
            main.matches_filters(
                self.item,
                {"related_power": ["罗德岛", "莱塔尼亚"], "power_mode": "all"},
            )
        )
        self.assertTrue(
            main.matches_filters(self.item, {"related_plot": ["孤星"]})
        )
        self.assertFalse(
            main.matches_filters(
                self.item,
                {"related_plot": ["孤星", "长夜临光"], "rplot_mode": "all"},
            )
        )


class EnsureReadRecordTests(unittest.TestCase):
    def test_normalizes_keys_and_defaults_new_plots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = os.path.join(tmp, "Read_record.json")
            with open(record, "w", encoding="utf-8") as handle:
                handle.write('{"1": "已读", "2": null}')  # null value from old builds
            with patch("main.READ_RECORD_PATH", record):
                data = main.ensure_read_record([{"id": 2}, {"id": "3"}])
        self.assertEqual(data, {"1": "已读", "2": "None", "3": "未读"})

    def test_missing_file_starts_fresh(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = os.path.join(tmp, "Read_record.json")
            with patch("main.READ_RECORD_PATH", record):
                data = main.ensure_read_record([{"id": 7}])
                self.assertEqual(data, {"7": "未读"})
                self.assertTrue(os.path.isfile(record))


if __name__ == "__main__":
    unittest.main()
