"""Plot-id remap for Read_record.json, used by the installer."""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "packaging", "migrate_read_record.ps1")
PLOTLINE = os.path.join(ROOT, "Plotline.json")
COMIC = "循途漫录：王权金币"


def _run(old: str, new: str, record: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            SCRIPT,
            "-OldPlotline",
            old,
            "-NewPlotline",
            new,
            "-Record",
            record,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _write(path: str, data: object) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def _read(path: str) -> object:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


class ReadRecordMigrationTests(unittest.TestCase):
    def test_statuses_follow_plot_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old = os.path.join(tmp, "old.json")
            new = os.path.join(tmp, "new.json")
            record = os.path.join(tmp, "Read_record.json")
            _write(
                old,
                {
                    "data": [
                        {"id": 1, "name": "十字路口"},
                        {"id": 2, "name": "人们，我们"},
                        {"id": 3, "name": "已删除"},
                    ]
                },
            )
            _write(
                new,
                {
                    "data": [
                        {"id": 1, "name": "十字路口"},
                        {"id": 2, "name": COMIC},
                        {"id": 3, "name": "人们，我们"},
                    ]
                },
            )
            _write(
                record,
                {
                    "1": '引号"与\\反斜杠',
                    "2": "读过人们",
                    "3": "已删除的状态",
                    "9": "无法对应",
                },
            )
            with open(record, "rb") as handle:
                before = handle.read()
            result = _run(old, new, record)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(os.path.exists(record + ".migrate.tmp"))
            mapped = _read(record)
            self.assertEqual(
                mapped,
                {
                    "1": '引号"与\\反斜杠',
                    "3": "读过人们",
                },
            )
            with open(record, "rb") as handle:
                self.assertNotEqual(before, handle.read())
            self.assertNotIn("2", mapped)

    def test_duplicate_name_keeps_the_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old = os.path.join(tmp, "old.json")
            new = os.path.join(tmp, "new.json")
            record = os.path.join(tmp, "Read_record.json")
            _write(old, {"data": [{"id": 1, "name": "甲"}]})
            _write(
                new,
                {"data": [{"id": 1, "name": "甲"}, {"id": 2, "name": "甲"}]},
            )
            _write(record, {"1": "已读"})
            with open(record, "rb") as handle:
                before = handle.read()
            result = _run(old, new, record)
            self.assertEqual(result.returncode, 1)
            with open(record, "rb") as handle:
                self.assertEqual(handle.read(), before)
            self.assertFalse(os.path.exists(record + ".migrate.tmp"))

    def test_missing_old_plotline_is_a_noop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = os.path.join(tmp, "Read_record.json")
            _write(record, {"1": "已读"})
            with open(record, "rb") as handle:
                before = handle.read()
            result = _run(os.path.join(tmp, "missing.json"), os.path.join(tmp, "also.json"), record)
            self.assertEqual(result.returncode, 0, result.stderr)
            with open(record, "rb") as handle:
                self.assertEqual(handle.read(), before)

    def test_catalog_insert_keeps_every_existing_status(self) -> None:
        new_doc = _read(PLOTLINE)
        self.assertIsInstance(new_doc, dict)
        rows = new_doc["data"]
        by_name = {row["name"]: row for row in rows}
        self.assertEqual(len(by_name), len(rows))
        comic = by_name[COMIC]
        self.assertEqual(comic["id"], 124)
        self.assertEqual(comic["date"], "2026-03-20")
        self.assertEqual([row["id"] for row in rows], list(range(1, 136)))
        pointed = []
        for row in rows:
            for key in ("necessary_plot", "optional_plot"):
                for ref in row.get(key) or []:
                    if isinstance(ref, dict) and ref.get("id") == 124:
                        pointed.append(row["name"])
        self.assertEqual(pointed, [])

        old_rows = []
        for row in rows:
            if row["name"] == COMIC:
                continue
            copied = json.loads(json.dumps(row))
            copied["id"] = copied["id"] if copied["id"] < 124 else copied["id"] - 1
            for key in ("necessary_plot", "optional_plot"):
                for ref in copied.get(key) or []:
                    if isinstance(ref, dict) and isinstance(ref.get("id"), int) and ref["id"] > 124:
                        ref["id"] -= 1
            old_rows.append(copied)

        with tempfile.TemporaryDirectory() as tmp:
            old = os.path.join(tmp, "old.json")
            new = os.path.join(tmp, "new.json")
            record = os.path.join(tmp, "Read_record.json")
            _write(old, {"data": old_rows})
            _write(new, new_doc)
            _write(record, {str(row["id"]): f"状态:{row['name']}" for row in old_rows})
            result = _run(old, new, record)
            self.assertEqual(result.returncode, 0, result.stderr)
            mapped = _read(record)
            self.assertNotIn(str(comic["id"]), mapped)
            for row in old_rows:
                new_id = str(by_name[row["name"]]["id"])
                self.assertEqual(mapped[new_id], f"状态:{row['name']}", row["name"])
            self.assertEqual(mapped["123"], "状态:十字路口")
            self.assertEqual(mapped["125"], "状态:人们，我们")
            self.assertEqual(mapped["135"], "状态:昨日海")


class PlotInsertTests(unittest.TestCase):
    def test_ids_and_references_follow_the_insert(self) -> None:
        with open(PLOTLINE, "rb") as handle:
            raw = handle.read()
        self.assertIn(b"\r\n", raw)
        self.assertNotIn(b"\n", raw.replace(b"\r\n", b""))
        doc = json.loads(raw.decode("utf-8"))
        rows = doc["data"]
        by_name = {row["name"]: row for row in rows}
        self.assertEqual(by_name["十字路口"]["id"], 123)
        self.assertEqual(by_name[COMIC]["class"], "manga")
        self.assertNotIn("first_appearance", by_name[COMIC])
        self.assertEqual(by_name[COMIC]["necessary_plot"], [])
        self.assertEqual(by_name["生息演算：沙洲遗闻"]["id"], 85)
        self.assertEqual(by_name["塞茜莉亚的安魂寻旅"]["id"], 92)
        self.assertEqual(by_name["理想城：长夏狂欢季"]["id"], 54)
        general = by_name["循途漫录：大将军，出击！"]
        self.assertEqual(general["id"], 129)
        self.assertEqual(general["necessary_plot"][0]["id"], 54)
        critical = by_name["EP17. 相变临界"]
        student = next(
            ref["id"]
            for ref in critical["necessary_plot"]
            if "乌萨斯学生" in ref["reason"]
        )
        self.assertEqual(student, by_name["人们，我们"]["id"])
        drowned = by_name["沉沦者的黑流树海"]
        warm = next(ref["id"] for ref in drowned["necessary_plot"] if "肉鸽预热" in ref["reason"])
        self.assertEqual(warm, general["id"])

        covers = _read(os.path.join(ROOT, "web", "public", "covers", "covers.json"))
        sources = _read(os.path.join(ROOT, "web", "public", "covers", "sources.json"))
        self.assertNotIn("124", covers)
        self.assertEqual(covers["125"], "covers/125.png")
        self.assertEqual(covers["135"], "covers/135.jpg")
        self.assertEqual(sources["125"], "活动名称_人们，我们.png")
        self.assertEqual(sources["135"], "bilibili/昨日海活动宣传PV封面.jpg")
        cover_dir = os.path.join(ROOT, "web", "public", "covers")
        self.assertTrue(os.path.isfile(os.path.join(cover_dir, "125.png")))
        self.assertTrue(os.path.isfile(os.path.join(cover_dir, "135.jpg")))
        self.assertFalse(os.path.exists(os.path.join(cover_dir, "124.png")))

        with open(
            os.path.join(ROOT, "web", "src", "i18n", "content", "plotNames.en-US.ts"),
            encoding="utf-8",
        ) as handle:
            names = handle.read()
        self.assertIn("'125': \"People, a People\", // 人们，我们", names)
        self.assertIn("'135': \"Yet Another Wave\", // 昨日海", names)
        with open(os.path.join(ROOT, "web", "src", "viewLink.ts"), encoding="utf-8") as handle:
            link = handle.read()
        self.assertIn(f"'{COMIC}': '4578'", link)
        with open(os.path.join(ROOT, "packaging", "ArkPlots.iss"), encoding="utf-8") as handle:
            iss = handle.read()
        self.assertIn("BeforeInstall: MigrateReadRecord", iss)
        self.assertIn("ExtractTemporaryFile('Plotline.new.json')", iss)

        record = _read(os.path.join(ROOT, "Read_record.json"))
        self.assertNotIn("124", record)
        self.assertIn("125", record)
        self.assertIn("135", record)
        self.assertEqual(set(record.values()), {"未读"})


if __name__ == "__main__":
    unittest.main()
