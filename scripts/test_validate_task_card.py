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


if __name__ == "__main__":
    unittest.main()
