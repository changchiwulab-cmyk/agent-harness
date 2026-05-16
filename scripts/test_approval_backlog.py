#!/usr/bin/env python3
"""Unit tests for scripts/approval_backlog.py."""

from __future__ import annotations

import datetime as dt
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import approval_backlog as ab

TODAY = dt.date(2026, 5, 20)


def mkroot(tmp: str) -> Path:
    root = Path(tmp)
    for d in ("tasks", "logs/approvals", "outputs/drafts"):
        (root / d).mkdir(parents=True)
    return root


def card(root: Path, name: str, tid: str, *, status, approval_needed, date="2026-05-15", goal="g", risk="medium"):
    (root / "tasks" / name).write_text(
        f'task_id: "{tid}"\ndate: "{date}"\nstatus: "{status}"\n'
        f'goal: "{goal}"\nskill_type: "ops"\nrisk_level: "{risk}"\n'
        f"approval_needed: {str(approval_needed).lower()}\n"
        "definition_of_done:\n  - x\n"
        'expected_output:\n  format: "md"\n  filename: "x.md"\n',
        encoding="utf-8",
    )


class ApprovalBacklogTests(unittest.TestCase):
    def test_pending_detected_with_waiting_days(self):
        with tempfile.TemporaryDirectory() as t:
            r = mkroot(t)
            card(r, "20a.yaml", "20260515-009", status="review",
                 approval_needed=True, date="2026-05-15")
            s = ab.scan(r, TODAY)
            self.assertEqual(len(s["pending"]), 1)
            self.assertEqual(s["pending"][0]["task_id"], "20260515-009")
            self.assertEqual(s["pending"][0]["waiting_days"], 5)

    def test_excluded_when_already_approved(self):
        with tempfile.TemporaryDirectory() as t:
            r = mkroot(t)
            card(r, "20a.yaml", "20260515-009", status="review", approval_needed=True)
            (r / "logs/approvals/x.md").write_text(
                '```yaml\napproval_id: "APR-20260515-001"\ntask_id: "20260515-009"\n```\n',
                encoding="utf-8",
            )
            self.assertEqual(ab.scan(r, TODAY)["pending"], [])

    def test_not_pending_when_no_approval_needed_or_not_review(self):
        with tempfile.TemporaryDirectory() as t:
            r = mkroot(t)
            card(r, "a.yaml", "20260515-001", status="review", approval_needed=False)
            card(r, "b.yaml", "20260515-002", status="done", approval_needed=True)
            self.assertEqual(ab.scan(r, TODAY)["pending"], [])

    def test_scan_no_tasks_dir_ok(self):
        with tempfile.TemporaryDirectory() as t:
            r = mkroot(t)
            s = ab.scan(r, TODAY)
            self.assertEqual(s["pending"], [])
            self.assertIn("backlog clear", ab.render_scan(s))

    def test_approve_writes_sequential_records(self):
        with tempfile.TemporaryDirectory() as t:
            r = mkroot(t)
            rc = ab.approve(r, ["20260515-009", "20260515-010"], "user", "n", TODAY)
            self.assertEqual(rc, 0)
            files = sorted((r / "logs/approvals").glob("*.md"))
            self.assertEqual(len(files), 2)
            ids = sorted(
                ab._FENCE_RE.search(f.read_text()).group(1) for f in files
            )
            self.assertIn("APR-20260520-001", "".join(ids))
            self.assertIn("APR-20260520-002", "".join(ids))

    def test_duplicate_approve_refused(self):
        with tempfile.TemporaryDirectory() as t:
            r = mkroot(t)
            ab.approve(r, ["20260515-009"], "user", "n", TODAY)
            rc = ab.approve(r, ["20260515-009"], "user", "n", TODAY)
            self.assertEqual(rc, 1)
            self.assertEqual(len(list((r / "logs/approvals").glob("*.md"))), 1)

    def test_approve_requires_operator(self):
        with tempfile.TemporaryDirectory() as t:
            r = mkroot(t)
            rc = ab.main(["--root", str(r), "--approve", "20260515-009", "--today", "2026-05-20"])
            self.assertEqual(rc, 2)

    def test_next_seq_continues_after_existing_same_day(self):
        with tempfile.TemporaryDirectory() as t:
            r = mkroot(t)
            ab.approve(r, ["20260515-009"], "user", "n", TODAY)
            self.assertEqual(ab._next_seq(r, TODAY), 2)


if __name__ == "__main__":
    unittest.main()
