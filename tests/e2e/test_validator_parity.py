#!/usr/bin/env python3
"""Validator parity test (A3: 20260606-A01).

The harness has two Task Card validators that can silently drift:
  - system/validate_task_card.py  — the RUNTIME schema_check gate (shelled by
    test_dummy_task_smoke.py and test_failure_drill.py).
  - scripts/check_spec_consistency.rb — the CI superset (also lints
    logs/approvals/errors, task_id regex, date, expected_output.location).

Ruby is intentionally a STRICT SUPERSET of Python on Task Card rules. This test
pins that contract:
  1. On shared rules (required fields, skill/risk enums, non-empty DoD) the two
     AGREE.
  2. The ONLY permitted asymmetry is "Ruby rejects while Python accepts"
     (Ruby stricter). Python must NEVER reject something Ruby accepts — if it
     does, the runtime gate is stricter than CI and in-flight cards could pass
     CI yet fail at runtime. That asymmetry direction is the regression guard.

Running the Ruby linter against a single fixture: it globs ``tasks/**/*.yaml``,
so we stand up a throwaway repo skeleton (required dirs + one tasks/ fixture)
and run it there. The linter loads system/TOOL_REGISTRY.yaml by its own path,
so it still resolves regardless of cwd.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
PY_VALIDATOR = ROOT / "system" / "validate_task_card.py"
RB_LINTER = ROOT / "scripts" / "check_spec_consistency.rb"

REQUIRED_DIRS = [
    "logs/runs",
    "logs/approvals",
    "logs/errors",
    "outputs/drafts",
    "outputs/reports",
    "memory/active_projects",
]

VALID_CARD = {
    "task_id": "20260606-P01",
    "date": "2026-06-06",
    "status": "pending",
    "goal": "parity fixture",
    "context": "synthetic",
    "definition_of_done": ["one independently verifiable item"],
    "expected_output": {"format": "md", "location": "outputs/drafts/", "filename": "p.md"},
    "risk_level": "low",
    "approval_needed": False,
    "allowed_tools": ["read_project_files"],
    "skill_type": "ops",
}


def py_accepts(card: dict) -> bool:
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        yaml.safe_dump(card, f, allow_unicode=True, sort_keys=False)
        path = f.name
    result = subprocess.run(
        [sys.executable, str(PY_VALIDATOR), path], capture_output=True, text=True
    )
    Path(path).unlink(missing_ok=True)
    return result.returncode == 0


def rb_accepts(card: dict) -> bool:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for d in REQUIRED_DIRS:
            (root / d).mkdir(parents=True, exist_ok=True)
        (root / "tasks").mkdir(parents=True, exist_ok=True)
        (root / "tasks" / "fixture.yaml").write_text(
            yaml.safe_dump(card, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )
        result = subprocess.run(
            ["ruby", str(RB_LINTER)], cwd=tmp, capture_output=True, text=True
        )
        return result.returncode == 0


def _drop(card: dict, key: str) -> dict:
    c = {**card}
    c.pop(key, None)
    return c


class TestValidatorParity(unittest.TestCase):
    def test_valid_card_accepted_by_both(self):
        self.assertTrue(py_accepts(VALID_CARD))
        self.assertTrue(rb_accepts(VALID_CARD))

    def test_shared_rules_agree_on_rejection(self):
        # Each of these violates a rule BOTH validators enforce -> both reject.
        cases = {
            "empty_dod": {**VALID_CARD, "definition_of_done": []},
            "bad_skill": {**VALID_CARD, "skill_type": "invalid_skill"},
            "bad_risk": {**VALID_CARD, "risk_level": "severe"},
            "missing_goal": _drop(VALID_CARD, "goal"),
        }
        for name, card in cases.items():
            with self.subTest(case=name):
                self.assertFalse(py_accepts(card), f"Python should reject {name}")
                self.assertFalse(rb_accepts(card), f"Ruby should reject {name}")

    def test_pinned_asymmetry_ruby_stricter(self):
        # Ruby requires `status` and `expected_output.location`; Python does not.
        # Documented, intentional asymmetry: Ruby rejects, Python accepts.
        no_status = _drop(VALID_CARD, "status")
        self.assertTrue(py_accepts(no_status), "Python does not require status")
        self.assertFalse(rb_accepts(no_status), "Ruby requires status")

        no_location = {**VALID_CARD, "expected_output": {"format": "md", "filename": "p.md"}}
        self.assertTrue(py_accepts(no_location), "Python does not require location")
        self.assertFalse(rb_accepts(no_location), "Ruby requires expected_output.location")

    def test_invariant_python_never_stricter_than_ruby(self):
        # The core regression guard. Across the whole matrix there must be NO
        # case where Python rejects but Ruby accepts (that would make the runtime
        # gate stricter than CI). New one-sided tightening of Python breaks here.
        matrix = [
            VALID_CARD,
            {**VALID_CARD, "definition_of_done": []},
            {**VALID_CARD, "skill_type": "invalid_skill"},
            {**VALID_CARD, "risk_level": "severe"},
            _drop(VALID_CARD, "goal"),
            _drop(VALID_CARD, "status"),
            {**VALID_CARD, "expected_output": {"format": "md", "filename": "p.md"}},
            {**VALID_CARD, "expected_output": {"format": "md", "location": "outputs/drafts/", "filename": ""}},
        ]
        for i, card in enumerate(matrix):
            with self.subTest(case=i):
                py_ok, rb_ok = py_accepts(card), rb_accepts(card)
                self.assertFalse(
                    (not py_ok) and rb_ok,
                    f"case {i}: Python rejected but Ruby accepted — Python is stricter "
                    f"than the CI superset, which violates the parity contract.",
                )


if __name__ == "__main__":
    unittest.main()
