#!/usr/bin/env python3
"""Unit tests for scripts/active_task.py."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import active_task


def make_root(cards: dict[str, dict] | None = None) -> Path:
    """Temp root with tasks/ + state/，cards 為 {檔名: 卡片內容}。"""
    root = Path(tempfile.mkdtemp())
    (root / "tasks").mkdir()
    (root / "state").mkdir()
    for name, card in (cards or {}).items():
        (root / "tasks" / name).write_text(
            yaml.safe_dump(card, allow_unicode=True), encoding="utf-8"
        )
    return root


def live_card(task_id: str = "20260710-T01", status: str = "in_progress") -> dict:
    return {
        "task_id": task_id,
        "status": status,
        "expected_output": {"format": "md", "location": "outputs/reports/", "filename": "t.md"},
    }


class TestSetActive(unittest.TestCase):
    def test_set_live_card_writes_active_state(self):
        root = make_root({"card.yaml": live_card()})
        self.assertIsNone(active_task.set_active("20260710-T01", root))
        state = yaml.safe_load((root / "state" / "active_task.yaml").read_text(encoding="utf-8"))
        self.assertEqual(state["task_id"], "20260710-T01")
        self.assertEqual(state["status"], "active")
        self.assertTrue(state["activated_at"])

    def test_set_done_card_rejected(self):
        root = make_root({"card.yaml": live_card(status="done")})
        error = active_task.set_active("20260710-T01", root)
        self.assertIsNotNone(error)
        self.assertIn("stale", error)

    def test_set_failed_card_rejected(self):
        root = make_root({"card.yaml": live_card(status="failed")})
        self.assertIsNotNone(active_task.set_active("20260710-T01", root))

    def test_set_missing_card_rejected(self):
        root = make_root()
        error = active_task.set_active("20260710-NOPE", root)
        self.assertIsNotNone(error)
        self.assertIn("找不到", error)

    def test_set_empty_task_id_rejected(self):
        root = make_root({"card.yaml": live_card()})
        self.assertIsNotNone(active_task.set_active("  ", root))

    def test_template_card_never_matches(self):
        root = make_root({"TASK_CARD_TEMPLATE.yaml": live_card("20260710-T01")})
        self.assertIsNotNone(active_task.set_active("20260710-T01", root))


class TestReadState(unittest.TestCase):
    def test_active_task_id_after_set(self):
        root = make_root({"card.yaml": live_card()})
        active_task.set_active("20260710-T01", root)
        self.assertEqual(active_task.active_task_id(root), "20260710-T01")

    def test_clear_returns_idle(self):
        root = make_root({"card.yaml": live_card()})
        active_task.set_active("20260710-T01", root)
        active_task.clear_active(root)
        self.assertEqual(active_task.active_task_id(root), "")
        state = yaml.safe_load((root / "state" / "active_task.yaml").read_text(encoding="utf-8"))
        self.assertEqual(state["status"], "idle")

    def test_missing_state_file_is_none(self):
        root = make_root()
        self.assertIsNone(active_task.read_state(root))
        self.assertEqual(active_task.active_task_id(root), "")

    def test_corrupt_state_file_is_none(self):
        root = make_root()
        (root / "state" / "active_task.yaml").write_text("{[broken", encoding="utf-8")
        self.assertIsNone(active_task.read_state(root))
        self.assertEqual(active_task.active_task_id(root), "")

    def test_idle_status_yields_empty_id_even_with_residual_task_id(self):
        # 防手改殘留：status=idle 時即使 task_id 有值也不得視為 active。
        root = make_root()
        (root / "state" / "active_task.yaml").write_text(
            yaml.safe_dump({"task_id": "20260710-T01", "status": "idle"}), encoding="utf-8"
        )
        self.assertEqual(active_task.active_task_id(root), "")


class TestFindCard(unittest.TestCase):
    def test_finds_card_in_subdirectory(self):
        root = make_root()
        sub = root / "tasks" / "examples"
        sub.mkdir()
        sub.joinpath("ex.yaml").write_text(
            yaml.safe_dump(live_card("20260710-E01")), encoding="utf-8"
        )
        path, card = active_task.find_card("20260710-E01", root)
        self.assertIsNotNone(path)
        self.assertEqual(card["task_id"], "20260710-E01")

    def test_unparseable_card_skipped(self):
        root = make_root({"good.yaml": live_card()})
        (root / "tasks" / "bad.yaml").write_text("{[broken", encoding="utf-8")
        path, card = active_task.find_card("20260710-T01", root)
        self.assertIsNotNone(card)


if __name__ == "__main__":
    unittest.main()
