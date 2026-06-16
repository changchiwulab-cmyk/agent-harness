#!/usr/bin/env python3
"""Unit tests for system/validate_task_card.py (focus: optional model field)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "system"))
import validate_task_card as v

BASE = {
    "task_id": "20260614-M01",
    "date": "2026-06-14",
    "status": "pending",
    "goal": "model field test",
    "definition_of_done": ["does a thing"],
    "expected_output": {"format": "md", "location": "outputs/drafts/", "filename": "x.md"},
    "risk_level": "low",
    "approval_needed": False,
    "skill_type": "ops",
}


def write(card: dict) -> str:
    f = tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False)
    yaml.safe_dump(card, f, allow_unicode=True, sort_keys=False)
    f.close()
    return f.name


class TestModelValidation(unittest.TestCase):
    def test_no_model_is_valid(self):
        self.assertEqual(v.validate(write(BASE)), [])

    def test_alias_model_valid(self):
        for m in ("haiku", "sonnet", "opus", "fable"):
            self.assertEqual(v.validate(write({**BASE, "model": m})), [], m)

    def test_full_id_model_valid(self):
        self.assertEqual(v.validate(write({**BASE, "model": "claude-opus-4-8"})), [])

    def test_invalid_model_rejected(self):
        errors = v.validate(write({**BASE, "model": "gpt-4"}))
        self.assertTrue(any("model 無效" in e for e in errors), errors)


R = "tasks/examples/2026-04-03_market-research-example.yaml"
W = "tasks/examples/2026-04-04_writing-proposal-example.yaml"


def orch(subtasks, **extra):
    return {"skill_type": "orchestration", "subtasks": subtasks, **extra}


class TestOrchestrationValidation(unittest.TestCase):
    def test_valid_dag_passes(self):
        card = orch([
            {"id": "research", "card": R, "depends_on": []},
            {"id": "writing", "card": W, "depends_on": ["research"]},
        ])
        self.assertEqual(v.validate_orchestration(card), [])

    def test_cycle_rejected(self):
        card = orch([
            {"id": "a", "card": R, "depends_on": ["b"]},
            {"id": "b", "card": W, "depends_on": ["a"]},
        ])
        errs = v.validate_orchestration(card)
        self.assertTrue(any("環" in e for e in errs), errs)

    def test_dangling_depends_on_rejected(self):
        card = orch([{"id": "writing", "card": W, "depends_on": ["ghost"]}])
        errs = v.validate_orchestration(card)
        self.assertTrue(any("依賴不存在" in e for e in errs), errs)

    def test_missing_subtask_card_rejected(self):
        card = orch([{"id": "x", "card": "tasks/does-not-exist.yaml", "depends_on": []}])
        errs = v.validate_orchestration(card)
        self.assertTrue(any("不存在" in e for e in errs), errs)

    def test_empty_subtasks_rejected(self):
        errs = v.validate_orchestration(orch([]))
        self.assertTrue(any("非空" in e for e in errs), errs)

    def test_non_orchestration_card_unaffected(self):
        # malformed subtasks on a non-orchestration card → skipped entirely
        self.assertEqual(v.validate_orchestration({"skill_type": "ops", "subtasks": "junk"}), [])

    def test_duplicate_id_rejected(self):
        card = orch([
            {"id": "dup", "card": R, "depends_on": []},
            {"id": "dup", "card": W, "depends_on": []},
        ])
        errs = v.validate_orchestration(card)
        self.assertTrue(any("重複" in e for e in errs), errs)

    def test_real_example_card_validates_clean(self):
        path = str(v.ROOT / "tasks" / "examples" / "2026-06-15_orchestration-example.yaml")
        self.assertEqual(v.validate(path), [])


if __name__ == "__main__":
    unittest.main()
