#!/usr/bin/env python3
"""Unit tests for scripts/check_task_output_exists.py.

Runs in a temporary repo-like directory and exercises four cases:
  1. status=done, output present  -> not missing
  2. status=review, output absent -> missing
  3. archived/* cards skipped     -> never inspected
  4. status=pending, output absent -> not missing (out of scope)
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_task_output_exists as checker  # noqa: E402


def write_card(
    path: Path, *, task_id: str, status: str, location: str, filename: str
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "task_id: \"{tid}\"\n"
        "date: \"2026-05-03\"\n"
        "status: \"{status}\"\n"
        "goal: \"test\"\n"
        "definition_of_done:\n"
        "  - \"x\"\n"
        "expected_output:\n"
        "  format: \"md\"\n"
        "  location: \"{loc}\"\n"
        "  filename: \"{fn}\"\n"
        "risk_level: \"low\"\n"
        "skill_type: \"ops\"\n".format(
            tid=task_id, status=status, loc=location, fn=filename
        ),
        encoding="utf-8",
    )


class CheckTaskOutputExistsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "tasks").mkdir()
        (self.root / "tasks" / "archived").mkdir()
        (self.root / "outputs" / "drafts").mkdir(parents=True)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_done_with_present_output_passes(self) -> None:
        write_card(
            self.root / "tasks" / "20260101_a.yaml",
            task_id="20260101-T01",
            status="done",
            location="outputs/drafts/",
            filename="a.md",
        )
        (self.root / "outputs" / "drafts" / "a.md").write_text("ok")
        self.assertEqual(checker.find_missing(self.root), [])

    def test_review_with_missing_output_flagged(self) -> None:
        write_card(
            self.root / "tasks" / "20260102_b.yaml",
            task_id="20260102-T02",
            status="review",
            location="outputs/drafts/",
            filename="b.md",
        )
        missing = checker.find_missing(self.root)
        self.assertEqual(len(missing), 1)
        self.assertIn("20260102_b.yaml", missing[0][0])
        self.assertIn("b.md", missing[0][1])

    def test_archived_card_with_missing_output_skipped(self) -> None:
        write_card(
            self.root / "tasks" / "archived" / "20260103_c.yaml",
            task_id="20260103-T03",
            status="review",
            location="outputs/drafts/",
            filename="c.md",
        )
        self.assertEqual(checker.find_missing(self.root), [])

    def test_pending_card_with_missing_output_skipped(self) -> None:
        write_card(
            self.root / "tasks" / "20260104_d.yaml",
            task_id="20260104-T04",
            status="pending",
            location="outputs/drafts/",
            filename="d.md",
        )
        self.assertEqual(checker.find_missing(self.root), [])

    def test_multi_format_card_skipped(self) -> None:
        path = self.root / "tasks" / "20260105_e.yaml"
        path.write_text(
            "task_id: \"20260105-T05\"\n"
            "date: \"2026-05-03\"\n"
            "status: \"done\"\n"
            "goal: \"multi-output card\"\n"
            "definition_of_done:\n"
            "  - \"x\"\n"
            "expected_output:\n"
            "  format: \"multi\"\n"
            "  location: \"outputs/drafts/, system/\"\n"
            "  filename: \"見 DoD\"\n"
            "risk_level: \"low\"\n"
            "skill_type: \"ops\"\n",
            encoding="utf-8",
        )
        self.assertEqual(checker.find_missing(self.root), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
