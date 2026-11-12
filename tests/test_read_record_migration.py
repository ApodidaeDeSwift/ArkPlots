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


def _git_blob(path: str) -> bytes:
    return subprocess.run(
        ["git", "-C", ROOT, "show", "HEAD:" + path],
        capture_output=True,
        check=True,
    ).stdout


def _git_has(path: str) -> bool:
    return (
        subprocess.run(
            ["git", "-C", ROOT, "cat-file", "-e", "HEAD:" + path],
            capture_output=True,
        ).returncode
        == 0
    )


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
        self.assertEqual(comic["id"], 125)
        self.assertEqual(comic["date"], "2026-03-20")
        self.assertEqual(by_name["暮岁闲谈：正是团圆时分"]["id"], 123)
        self.assertEqual(by_name["序言组曲：孤行之人"]["id"], 127)
        self.assertEqual([row["id"] for row in rows], list(range(1, 138)))
        inserted = {COMIC, "暮岁闲谈：正是团圆时分", "序言组曲：孤行之人"}
        pointed = []
        for row in rows:
            for key in ("necessary_plot", "optional_plot"):
                for ref in row.get(key) or []:
                    if isinstance(ref, dict) and ref.get("id") in {123, 125, 127}:
                        pointed.append(row["name"])
        self.assertEqual(pointed, [])

        kept = [row for row in rows if row["name"] not in inserted]
        new_to_old = {row["id"]: index for index, row in enumerate(kept, 1)}
        old_rows = []
        for index, row in enumerate(kept, 1):
            copied = json.loads(json.dumps(row))
            copied["id"] = index
            for key in ("necessary_plot", "optional_plot"):
                for ref in copied.get(key) or []:
                    if isinstance(ref, dict) and isinstance(ref.get("id"), int):
                        ref["id"] = new_to_old[ref["id"]]
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
            self.assertNotIn("123", mapped)
            self.assertNotIn("127", mapped)
            self.assertEqual(mapped["124"], "状态:十字路口")
            self.assertEqual(mapped["126"], "状态:人们，我们")
            self.assertEqual(mapped["137"], "状态:昨日海")


class PlotInsertTests(unittest.TestCase):
    def test_ids_and_references_follow_the_insert(self) -> None:
        with open(PLOTLINE, "rb") as handle:
            raw = handle.read()
        self.assertIn(b"\r\n", raw)
        self.assertNotIn(b"\n", raw.replace(b"\r\n", b""))
        doc = json.loads(raw.decode("utf-8"))
        rows = doc["data"]
        by_name = {row["name"]: row for row in rows}
        self.assertEqual(by_name["十字路口"]["id"], 124)
        self.assertEqual(by_name["暮岁闲谈：正是团圆时分"]["date"], "2026-02-16")
        self.assertEqual(by_name["序言组曲：孤行之人"]["date"], "2026-04-25")
        self.assertEqual(by_name[COMIC]["class"], "manga")
        self.assertNotIn("first_appearance", by_name[COMIC])
        self.assertEqual(by_name[COMIC]["necessary_plot"][0]["id"], 29)
        self.assertEqual(by_name["生息演算：沙洲遗闻"]["id"], 85)
        self.assertEqual(by_name["塞茜莉亚的安魂寻旅"]["id"], 92)
        self.assertEqual(by_name["理想城：长夏狂欢季"]["id"], 54)
        general = by_name["循途漫录：大将军，出击！"]
        self.assertEqual(general["id"], 131)
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

        # The working tree may carry build-time cover overrides (compressed
        # jpgs for mobile builds, no sources.json) or a personal read state,
        # so the shipped data files are verified as committed, not as checked
        # out.
        covers = json.loads(_git_blob("web/public/covers/covers.json"))
        sources = json.loads(_git_blob("web/public/covers/sources.json"))
        self.assertEqual(covers["123"], "covers/123.jpg")
        self.assertEqual(covers["124"], "covers/124.png")
        self.assertEqual(covers["125"], "covers/125.png")
        self.assertEqual(covers["126"], "covers/126.png")
        self.assertEqual(covers["127"], "covers/127.jpg")
        self.assertEqual(covers["137"], "covers/137.jpg")
        self.assertTrue(sources["123"].startswith("https://web.hycdn.cn/comic/pic/"))
        self.assertTrue(sources["125"].startswith("https://web.hycdn.cn/comic/pic/"))
        self.assertTrue(sources["127"].startswith("https://web.hycdn.cn/comic/pic/"))
        self.assertEqual(sources["126"], "活动名称_人们，我们.png")
        self.assertEqual(sources["137"], "bilibili/昨日海活动宣传PV封面.jpg")
        for cover_id in ("123", "125", "126", "127", "137"):
            self.assertTrue(
                _git_has("web/public/covers/" + covers[cover_id].split("/")[-1]),
                covers[cover_id],
            )

        with open(
            os.path.join(ROOT, "web", "src", "i18n", "content", "plotNames.en-US.ts"),
            encoding="utf-8",
        ) as handle:
            names = handle.read()
        self.assertIn("'123': \"暮岁闲谈：正是团圆时分\", // 暮岁闲谈：正是团圆时分", names)
        self.assertIn("'126': \"People, a People\", // 人们，我们", names)
        self.assertIn("'127': \"序言组曲：孤行之人\", // 序言组曲：孤行之人", names)
        self.assertIn("'137': \"Yet Another Wave\", // 昨日海", names)
        with open(os.path.join(ROOT, "web", "src", "viewLink.ts"), encoding="utf-8") as handle:
            link = handle.read()
        self.assertIn(f"'{COMIC}': '4578'", link)
        self.assertIn("'暮岁闲谈：正是团圆时分': '8907'", link)
        self.assertIn("'序言组曲：孤行之人': '0694'", link)
        with open(os.path.join(ROOT, "packaging", "ArkPlots.iss"), encoding="utf-8") as handle:
            iss = handle.read()
        self.assertIn("BeforeInstall: MigrateReadRecord", iss)
        self.assertIn("ExtractTemporaryFile('Plotline.new.json')", iss)

        record = json.loads(_git_blob("Read_record.json"))
        self.assertNotIn("123", record)
        self.assertNotIn("125", record)
        self.assertNotIn("127", record)
        self.assertIn("124", record)
        self.assertIn("126", record)
        self.assertIn("137", record)
        self.assertEqual(set(record.values()), {"未读"})


if __name__ == "__main__":
    unittest.main()
