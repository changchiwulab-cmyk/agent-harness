#!/usr/bin/env python3
"""Unit tests for scripts/build_memory_index.py."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_memory_index as bmi


def make_tree(root: Path) -> None:
    d = root / "memory" / "active_projects" / "proj-a" / "decisions"
    d.mkdir(parents=True)
    (d / "20260101-D001_first.yaml").write_text(
        yaml.safe_dump({"decision_id": "20260101-D001", "date": "2026-01-01",
                        "decision": "do X", "status": "active", "related_task": "20260101-001"},
                       allow_unicode=True), encoding="utf-8")
    a = root / "memory" / "archived_projects" / "proj-old" / "decisions"
    a.mkdir(parents=True)
    (a / "20251201-D009_old.yaml").write_text(
        yaml.safe_dump({"decision_id": "20251201-D009", "date": "2025-12-01",
                        "decision": "legacy", "status": "superseded"},
                       allow_unicode=True), encoding="utf-8")


class TestBuild(unittest.TestCase):
    def test_indexes_active_and_archived(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_tree(root)
            payload = bmi.build(root)
            self.assertEqual(payload["count"], 2)
            ids = [r["decision_id"] for r in payload["decisions"]]
            self.assertEqual(ids, ["20251201-D009", "20260101-D001"])  # sorted
            scopes = {r["decision_id"]: r["scope"] for r in payload["decisions"]}
            self.assertEqual(scopes["20260101-D001"], "active")
            self.assertEqual(scopes["20251201-D009"], "archived")
            self.assertEqual(payload["decisions"][1]["project"], "proj-a")

    def test_dump_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_tree(root)
            self.assertEqual(bmi.dump(bmi.build(root)), bmi.dump(bmi.build(root)))

    def test_repo_index_is_up_to_date(self):
        """The committed memory/decision_index.json must match a fresh build."""
        self.assertEqual(bmi.main(["--check"]), 0)


if __name__ == "__main__":
    unittest.main()
