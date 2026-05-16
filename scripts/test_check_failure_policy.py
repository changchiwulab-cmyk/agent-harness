#!/usr/bin/env python3
"""Unit tests for scripts/check_failure_policy.py (CLAUDE.md hard-rule 3)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_failure_policy as cfp


def mkroot(tmp: str) -> Path:
    root = Path(tmp)
    (root / "logs" / "runs").mkdir(parents=True)
    (root / "logs" / "errors").mkdir(parents=True)
    return root


def run_log(root: Path, name: str, task_id: str, cf, action="none", omit=False):
    if omit:
        body = f"execution_log:\n  task_id: \"{task_id}\"\n  status: \"failed\"\n"
    else:
        body = (
            "execution_log:\n"
            f"  task_id: \"{task_id}\"\n"
            "  status: \"failed\"\n"
            "  retry_policy:\n"
            f"    consecutive_failures: {cf}\n"
            f"    failure_policy_action: \"{action}\"\n"
        )
    (root / "logs" / "runs" / name).write_text(body, encoding="utf-8")


def err_log(root: Path, name: str, task_id: str):
    (root / "logs" / "errors" / name).write_text(
        f"# Error\n\n```yaml\ntask_id: \"{task_id}\"\nerror_type: \"rule_violation\"\n```\n",
        encoding="utf-8",
    )


class CheckFailurePolicyTests(unittest.TestCase):
    def test_no_runs_is_vacuously_ok(self):
        with tempfile.TemporaryDirectory() as t:
            root = mkroot(t)
            self.assertEqual(cfp.check(root), [])
            self.assertEqual(cfp.main(["--root", str(root)]), 0)

    def test_below_threshold_ok(self):
        with tempfile.TemporaryDirectory() as t:
            root = mkroot(t)
            run_log(root, "a.yaml", "T-1", 2, "warned")
            self.assertEqual(cfp.check(root), [])
            self.assertEqual(cfp.main(["--root", str(root)]), 0)

    def test_three_failures_stopped_with_error_log_ok(self):
        with tempfile.TemporaryDirectory() as t:
            root = mkroot(t)
            run_log(root, "a.yaml", "T-2", 3, "stopped")
            err_log(root, "e.md", "T-2")
            self.assertEqual(cfp.check(root), [])
            self.assertEqual(cfp.main(["--root", str(root)]), 0)

    def test_three_failures_not_stopped_is_violation(self):
        with tempfile.TemporaryDirectory() as t:
            root = mkroot(t)
            run_log(root, "a.yaml", "T-3", 3, "warned")
            err_log(root, "e.md", "T-3")
            v = cfp.check(root)
            self.assertTrue(any("'stopped'" in x for x in v))
            self.assertEqual(cfp.main(["--root", str(root)]), 1)

    def test_three_failures_without_error_log_is_violation(self):
        with tempfile.TemporaryDirectory() as t:
            root = mkroot(t)
            run_log(root, "a.yaml", "T-4", 4, "stopped")
            v = cfp.check(root)
            self.assertTrue(any("無 task_id" in x for x in v))
            self.assertEqual(cfp.main(["--root", str(root)]), 1)

    def test_legacy_run_without_retry_policy_ok(self):
        with tempfile.TemporaryDirectory() as t:
            root = mkroot(t)
            run_log(root, "old.yaml", "T-OLD", None, omit=True)
            self.assertEqual(cfp.check(root), [])


if __name__ == "__main__":
    unittest.main()
