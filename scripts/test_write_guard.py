#!/usr/bin/env python3
"""Unit tests for scripts/write_guard.py (R13)."""

from __future__ import annotations

import io
import json
import os
import sys
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import write_guard as wg

ROOT = Path(__file__).resolve().parents[1]


def run_main(payload: dict, override: bool = False) -> tuple[int, dict, str]:
    sys.stdin = io.StringIO(json.dumps(payload))
    out, err = io.StringIO(), io.StringIO()
    prev = os.environ.get(wg.OVERRIDE_ENV)
    if override:
        os.environ[wg.OVERRIDE_ENV] = "1"
    elif prev is not None:
        del os.environ[wg.OVERRIDE_ENV]
    try:
        with redirect_stdout(out), redirect_stderr(err):
            code = wg.main()
    finally:
        sys.stdin = sys.__stdin__
        if prev is not None:
            os.environ[wg.OVERRIDE_ENV] = prev
        else:
            os.environ.pop(wg.OVERRIDE_ENV, None)
    text = out.getvalue().strip()
    return code, (json.loads(text) if text else {}), err.getvalue()


class TestEvaluate(unittest.TestCase):
    def test_system_blocked(self):
        d, reason = wg.evaluate(str(ROOT / "system" / "GATE_POLICY.yaml"))
        self.assertEqual(d, "block")
        self.assertIn("modify_system_rules", reason)

    def test_skills_blocked(self):
        d, _ = wg.evaluate("skills/research/SKILL.md")
        self.assertEqual(d, "block")

    def test_memory_blocked(self):
        d, reason = wg.evaluate("memory/user_prefs.md")
        self.assertEqual(d, "block")
        self.assertIn("write_long_term_memory", reason)

    def test_reports_blocked(self):
        d, reason = wg.evaluate("outputs/reports/foo.md")
        self.assertEqual(d, "block")
        self.assertIn("write_reports", reason)

    def test_claude_md_blocked(self):
        d, reason = wg.evaluate("CLAUDE.md")
        self.assertEqual(d, "block")
        self.assertIn("modify_claude_md", reason)

    def test_drafts_allowed(self):
        d, reason = wg.evaluate("outputs/drafts/foo.md")
        self.assertEqual(d, "allow")
        self.assertIsNone(reason)

    def test_logs_allowed(self):
        self.assertEqual(wg.evaluate("logs/errors/x.md")[0], "allow")

    def test_tasks_allowed(self):
        self.assertEqual(wg.evaluate("tasks/2026-06-20_x.yaml")[0], "allow")

    def test_scripts_allowed(self):
        self.assertEqual(wg.evaluate("scripts/foo.py")[0], "allow")

    def test_outside_repo_allowed(self):
        self.assertEqual(wg.evaluate("/tmp/whatever.txt")[0], "allow")


class TestMain(unittest.TestCase):
    def test_block_returns_exit_2(self):
        code, payload, err = run_main(
            {"tool_name": "Write", "tool_input": {"file_path": "system/X.yaml"}}
        )
        self.assertEqual(code, 2)
        self.assertEqual(payload["decision"], "block")
        self.assertIn("BLOCKED", err)

    def test_edit_tool_also_guarded(self):
        code, payload, _ = run_main(
            {"tool_name": "Edit", "tool_input": {"file_path": "CLAUDE.md"}}
        )
        self.assertEqual(code, 2)
        self.assertEqual(payload["decision"], "block")

    def test_allow_draft_exit_0(self):
        code, payload, _ = run_main(
            {"tool_name": "Write", "tool_input": {"file_path": "outputs/drafts/x.md"}}
        )
        self.assertEqual(code, 0)
        self.assertEqual(payload["decision"], "allow")

    def test_non_write_tool_passes_through(self):
        code, payload, _ = run_main(
            {"tool_name": "Read", "tool_input": {"file_path": "system/X.yaml"}}
        )
        self.assertEqual(code, 0)
        self.assertEqual(payload["decision"], "allow")

    def test_override_allows_ask_tier(self):
        code, payload, err = run_main(
            {"tool_name": "Write", "tool_input": {"file_path": "system/X.yaml"}}, override=True
        )
        self.assertEqual(code, 0)
        self.assertEqual(payload["decision"], "allow")
        self.assertIn("OVERRIDE", err)

    def test_empty_stdin_allows(self):
        sys.stdin = io.StringIO("")
        out = io.StringIO()
        try:
            with redirect_stdout(out):
                code = wg.main()
        finally:
            sys.stdin = sys.__stdin__
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out.getvalue())["decision"], "allow")


if __name__ == "__main__":
    unittest.main()
