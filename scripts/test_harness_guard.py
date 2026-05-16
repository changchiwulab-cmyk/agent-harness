#!/usr/bin/env python3
"""Unit tests for scripts/harness_guard.py.

_has_task_card_activity() shells out to git, so it is monkey-patched
(mirrors test_audit_drift_guard.py / test_generate_audit_log.py).
"""

from __future__ import annotations

import io
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_guard as hg


def run(payload, *, task_activity=True):
    stdin = io.StringIO(json.dumps(payload) if isinstance(payload, dict) else payload)
    stdout = io.StringIO()
    with mock.patch.object(hg.sys, "stdin", stdin), mock.patch.object(
        hg.sys, "stdout", stdout
    ), mock.patch.object(hg, "_has_task_card_activity", return_value=task_activity):
        code = hg.main()
    return code, json.loads(stdout.getvalue().splitlines()[0])


def w(path):
    return {"tool_name": "Write", "tool_input": {"file_path": path}}


class HarnessGuardTests(unittest.TestCase):
    def test_rule1_warns_without_task_card(self):
        code, out = run(w("system/PERMISSIONS.yaml"), task_activity=False)
        self.assertEqual(code, 0)
        self.assertEqual(out["decision"], "allow")
        self.assertIn("規則1", out["warning"])

    def test_rule1_silent_with_task_card(self):
        code, out = run(w("system/PERMISSIONS.yaml"), task_activity=True)
        self.assertEqual(out["decision"], "allow")
        self.assertNotIn("warning", out)

    def test_rule2_warns_on_non_drafts_output(self):
        code, out = run(w("outputs/reports/retro-2026-Q2-02.md"), task_activity=True)
        self.assertEqual(out["decision"], "allow")
        self.assertIn("規則2", out["warning"])

    def test_rule2_silent_on_drafts(self):
        # drafts path => no Rule 2; with task context => no Rule 1 either.
        code, out = run(w("outputs/drafts/20260515-004_x.md"), task_activity=True)
        self.assertEqual(out["decision"], "allow")
        self.assertNotIn("warning", out)

    def test_drafts_without_task_card_still_rule1(self):
        # Rule 1 is universal: even a draft needs a Task Card.
        code, out = run(w("outputs/drafts/x.md"), task_activity=False)
        self.assertEqual(out["decision"], "allow")
        self.assertIn("規則1", out["warning"])

    def test_tasks_path_not_rule1(self):
        # Writing the Task Card itself must never trigger rule 1.
        code, out = run(w("tasks/2026-05-15_enforce-hard-rules.yaml"), task_activity=False)
        self.assertEqual(out["decision"], "allow")
        self.assertNotIn("warning", out)

    def test_non_edit_tool_allowed(self):
        code, out = run(
            {"tool_name": "Bash", "tool_input": {"command": "rm -rf /"}},
            task_activity=False,
        )
        self.assertEqual(out["decision"], "allow")
        self.assertNotIn("warning", out)

    def test_bad_json_fails_open(self):
        code, out = run("{not json", task_activity=False)
        self.assertEqual(code, 0)
        self.assertEqual(out["decision"], "allow")

    def test_path_outside_repo_ignored(self):
        code, out = run(w("/etc/passwd"), task_activity=False)
        self.assertEqual(out["decision"], "allow")
        self.assertNotIn("warning", out)


if __name__ == "__main__":
    unittest.main()
