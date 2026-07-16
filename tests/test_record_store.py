#!/usr/bin/env python3
"""Executable checks for the private sansanskill record store."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "sansan-save" / "scripts" / "record_store.py"


SAMPLE = """---
project: 测试项目
timestamp: 2026-07-16T15:30:00+08:00
title: 获客瓶颈
source_skill: sansan-business-diagnosis
status: in-progress
schema_version: 1
---

## 用户主诉

测试。
"""


class RecordStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name) / "state"
        self.content = Path(self.temp.name) / "content.md"
        self.content.write_text(SAMPLE, encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_tool(self, *args: str, expected: int = 0) -> dict[str, object]:
        result = subprocess.run(
            ["python3", str(SCRIPT), *args, "--base", str(self.base)],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, expected, result.stderr or result.stdout)
        return json.loads(result.stdout)

    def write(self, kind: str = "record", project: str = "测试项目") -> dict[str, object]:
        return self.run_tool(
            "write",
            "--kind",
            kind,
            "--project",
            project,
            "--title",
            "获客瓶颈",
            "--content-file",
            str(self.content),
        )

    def test_write_is_append_only_and_private(self) -> None:
        first = self.write()
        second = self.write()
        self.assertNotEqual(first["path"], second["path"])
        self.assertEqual(second["count"], 2)
        for item in (first, second):
            path = Path(str(item["path"]))
            self.assertTrue(path.exists())
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.base.stat().st_mode & 0o777, 0o700)
        self.assertEqual((self.base / "records").stat().st_mode & 0o777, 0o700)

    def test_project_name_cannot_escape_root(self) -> None:
        receipt = self.write(project="../../客户/项目")
        path = Path(str(receipt["path"])).resolve()
        records_root = (self.base / "records").resolve()
        self.assertEqual(os.path.commonpath([path, records_root]), str(records_root))
        self.assertNotIn("..", path.parts)

    def test_list_and_resolve_use_same_newest_first_order(self) -> None:
        self.write()
        self.write()
        listing = self.run_tool("list", "--kind", "record", "--project", "测试项目")
        resolved = self.run_tool("resolve", "--project", "测试项目", "--selector", "1")
        self.assertEqual(listing["count"], 2)
        self.assertEqual(listing["items"][0]["path"], resolved["path"])

    def test_missing_record_returns_machine_readable_error(self) -> None:
        result = self.run_tool("resolve", "--project", "不存在", expected=2)
        self.assertEqual(result["error"], "not_found")

    def test_report_uses_separate_root(self) -> None:
        receipt = self.write(kind="report")
        self.assertIn("reports", Path(str(receipt["path"])).parts)
        self.assertFalse((self.base / "records").exists())

    def test_project_symlink_is_rejected(self) -> None:
        records = self.base / "records"
        records.mkdir(parents=True)
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        (records / "危险项目").symlink_to(outside, target_is_directory=True)
        result = subprocess.run(
            [
                "python3",
                str(SCRIPT),
                "write",
                "--kind",
                "record",
                "--project",
                "危险项目",
                "--title",
                "测试",
                "--content-file",
                str(self.content),
                "--base",
                str(self.base),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(any(outside.iterdir()))


if __name__ == "__main__":
    unittest.main()
