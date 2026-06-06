#!/usr/bin/env python3
"""Unit tests for verify_completion.py (AGI-1: 20260606-B01)."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify_completion as vc  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

BASE = {
    "task_id": "20260606-V01",
    "date": "2026-06-06",
    "status": "done",
    "goal": "g",
    "definition_of_done": ["did the thing"],
    "expected_output": {"format": "md", "location": "outputs/drafts/", "filename": "v.md"},
    "risk_level": "low",
    "approval_needed": False,
    "skill_type": "ops",
    "completion_time": "2026-06-06",
}

NO_CP = lambda task_id, root: []           # noqa: E731 — stub: no checkpoints
HAS_CP = lambda task_id, root: [{"commit": "abc123", "subject": "x"}]  # noqa: E731


class TestEvaluateTask(unittest.TestCase):
    def test_artifact_present_is_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "outputs" / "drafts").mkdir(parents=True)
            (root / "outputs" / "drafts" / "v.md").write_text("x", encoding="utf-8")
            r = vc.evaluate_task(BASE, root, checkpoint_finder=NO_CP)
            self.assertEqual(r["level"], vc.OK)

    def test_missing_artifact_no_checkpoint_is_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = vc.evaluate_task(BASE, Path(tmp), checkpoint_finder=NO_CP)
            self.assertEqual(r["level"], vc.FAIL)
            self.assertIn("self-report falsification", r["reason"])

    def test_missing_artifact_with_checkpoint_is_warn(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = vc.evaluate_task(BASE, Path(tmp), checkpoint_finder=HAS_CP)
            self.assertEqual(r["level"], vc.WARN)

    def test_multitarget_location_is_warn(self):
        card = {**BASE, "expected_output": {"format": "md", "location": "system/, tasks/", "filename": "見 DoD"}}
        r = vc.evaluate_task(card, ROOT, checkpoint_finder=NO_CP)
        self.assertEqual(r["level"], vc.WARN)

    def test_high_risk_in_reports_is_fail(self):
        card = {**BASE, "risk_level": "high",
                "expected_output": {"format": "md", "location": "outputs/reports/", "filename": "r.md"}}
        r = vc.evaluate_task(card, ROOT, checkpoint_finder=HAS_CP)
        self.assertEqual(r["level"], vc.FAIL)
        self.assertIn("outputs/reports/", r["reason"])

    def test_non_completion_status_is_ok(self):
        card = {**BASE, "status": "pending"}
        r = vc.evaluate_task(card, ROOT, checkpoint_finder=NO_CP)
        self.assertEqual(r["level"], vc.OK)


class TestCheckMode(unittest.TestCase):
    def _run(self, root: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "verify_completion.py"), "--check", "--root", str(root)],
            capture_output=True, text=True,
        )

    def test_check_fails_on_falsified_card(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tasks").mkdir(parents=True)
            (root / "tasks" / "20260606-bad.yaml").write_text(
                yaml.safe_dump(BASE, allow_unicode=True, sort_keys=False), encoding="utf-8"
            )
            # No artifact, no git -> find_checkpoints returns [] -> FAIL.
            r = self._run(root)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)

    def test_check_passes_when_artifact_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tasks").mkdir(parents=True)
            (root / "outputs" / "drafts").mkdir(parents=True)
            (root / "outputs" / "drafts" / "v.md").write_text("x", encoding="utf-8")
            (root / "tasks" / "20260606-good.yaml").write_text(
                yaml.safe_dump(BASE, allow_unicode=True, sort_keys=False), encoding="utf-8"
            )
            r = self._run(root)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_real_corpus_has_no_fail(self):
        """The live repo must pass --check (regression guard for CI wiring)."""
        r = self._run(ROOT)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
