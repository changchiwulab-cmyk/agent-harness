#!/usr/bin/env python3
"""Unit tests for scripts/permissions_guard.py."""

from __future__ import annotations

import io
import json
import sys
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import permissions_guard as guard


def run_main(payload: dict) -> tuple[int, dict, str]:
    """Run guard.main() with stdin set to ``payload``. Return (exit_code, stdout_json, stderr)."""
    sys.stdin = io.StringIO(json.dumps(payload))
    out = io.StringIO()
    err = io.StringIO()
    try:
        with redirect_stdout(out), redirect_stderr(err):
            code = guard.main()
    finally:
        sys.stdin = sys.__stdin__
    stdout_text = out.getvalue().strip()
    parsed = json.loads(stdout_text) if stdout_text else {}
    return code, parsed, err.getvalue()


class TestEvaluate(unittest.TestCase):
    def test_rm_recursive_force_blocked(self):
        decision, reason = guard.evaluate("rm -rf /tmp/junk")
        self.assertEqual(decision, "block")
        self.assertIn("shell_delete", reason)

    def test_plain_ls_allowed(self):
        decision, reason = guard.evaluate("ls -la")
        self.assertEqual(decision, "allow")
        self.assertIsNone(reason)

    def test_curl_to_slack_webhook_blocked(self):
        decision, reason = guard.evaluate(
            "curl -X POST https://hooks.slack.com/services/AAA -d '{}'"
        )
        self.assertEqual(decision, "block")
        self.assertIn("send_message_external", reason)

    def test_unknown_tool_allowed(self):
        decision, reason = guard.evaluate("git status")
        self.assertEqual(decision, "allow")
        self.assertIsNone(reason)

    def test_git_force_push_blocked(self):
        decision, reason = guard.evaluate("git push --force origin main")
        self.assertEqual(decision, "block")
        self.assertIn("git_force_push", reason)

    def test_sendmail_blocked(self):
        decision, reason = guard.evaluate("sendmail user@example.com < body.txt")
        self.assertEqual(decision, "block")
        self.assertIn("send_email", reason)

    def test_rm_without_destructive_flags_allowed(self):
        # `rm filename` (no -r/-f) is technically still destructive but rare in
        # the harness; the current rule set deliberately limits scope to the
        # high-blast-radius -r/-f variants. This test pins that scoping.
        decision, reason = guard.evaluate("rm tempfile.txt")
        self.assertEqual(decision, "allow")
        self.assertIsNone(reason)


class TestClassifyWritePath(unittest.TestCase):
    def test_system_dir_asks(self):
        decision, reason = guard.classify_write_path("system/GATE_POLICY.yaml")
        self.assertEqual(decision, "ask")
        self.assertIn("modify_system_rules", reason)

    def test_skills_dir_asks(self):
        decision, reason = guard.classify_write_path("skills/research/SKILL.md")
        self.assertEqual(decision, "ask")
        self.assertIn("modify_skills", reason)

    def test_memory_dir_asks(self):
        decision, reason = guard.classify_write_path("memory/user_prefs.md")
        self.assertEqual(decision, "ask")
        self.assertIn("write_long_term_memory", reason)

    def test_reports_dir_asks(self):
        decision, reason = guard.classify_write_path("outputs/reports/x.md")
        self.assertEqual(decision, "ask")
        self.assertIn("write_reports", reason)

    def test_root_claude_md_asks_but_not_nested(self):
        d1, r1 = guard.classify_write_path("CLAUDE.md")
        self.assertEqual(d1, "ask")
        self.assertIn("modify_claude_md", r1)
        # A nested file that merely ends with the name must NOT match.
        d2, _ = guard.classify_write_path("memory/notes/CLAUDE.md")
        self.assertEqual(d2, "ask")  # caught by memory/ rule, not claude_md rule

    def test_drafts_and_tasks_allowed(self):
        for p in ("outputs/drafts/x.md", "tasks/2026-06-14_x.yaml", "logs/runs/r.yaml", "scripts/x.py"):
            decision, reason = guard.classify_write_path(p)
            self.assertEqual(decision, "allow", p)
            self.assertIsNone(reason)

    def test_absolute_path_under_root_resolves(self):
        target = str(guard.ROOT / "system" / "PERMISSIONS.yaml")
        decision, reason = guard.classify_write_path(target)
        self.assertEqual(decision, "ask")
        self.assertIn("modify_system_rules", reason)

    def test_path_outside_repo_allowed(self):
        decision, reason = guard.classify_write_path("/tmp/somewhere/else.md")
        self.assertEqual(decision, "allow")
        self.assertIsNone(reason)

    def test_empty_path_allowed(self):
        decision, reason = guard.classify_write_path("")
        self.assertEqual(decision, "allow")
        self.assertIsNone(reason)


class TestMainEntrypoint(unittest.TestCase):
    def test_block_returns_exit_2(self):
        code, payload, err = run_main(
            {"tool_name": "Bash", "tool_input": {"command": "rm -rf /tmp"}}
        )
        self.assertEqual(code, 2)
        self.assertEqual(payload["decision"], "block")
        self.assertIn("BLOCKED", err)

    def test_allow_returns_exit_0(self):
        code, payload, _ = run_main(
            {"tool_name": "Bash", "tool_input": {"command": "echo hi"}}
        )
        self.assertEqual(code, 0)
        self.assertEqual(payload["decision"], "allow")

    def test_non_bash_tool_passes_through(self):
        code, payload, _ = run_main(
            {"tool_name": "Read", "tool_input": {"file_path": "/etc/passwd"}}
        )
        self.assertEqual(code, 0)
        self.assertEqual(payload["decision"], "allow")

    def test_write_to_system_returns_ask(self):
        code, payload, _ = run_main(
            {"tool_name": "Write", "tool_input": {"file_path": "system/PERMISSIONS.yaml"}}
        )
        self.assertEqual(code, 0)
        self.assertEqual(payload["decision"], "ask")
        self.assertEqual(payload["hookSpecificOutput"]["permissionDecision"], "ask")

    def test_edit_to_drafts_allowed(self):
        code, payload, _ = run_main(
            {"tool_name": "Edit", "tool_input": {"file_path": "outputs/drafts/x.md"}}
        )
        self.assertEqual(code, 0)
        self.assertEqual(payload["decision"], "allow")

    def test_write_to_reports_returns_ask(self):
        code, payload, _ = run_main(
            {"tool_name": "Write", "tool_input": {"file_path": "outputs/reports/r.md"}}
        )
        self.assertEqual(code, 0)
        self.assertEqual(payload["decision"], "ask")

    def test_empty_stdin_defaults_allow(self):
        sys.stdin = io.StringIO("")
        out = io.StringIO()
        try:
            with redirect_stdout(out):
                code = guard.main()
        finally:
            sys.stdin = sys.__stdin__
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out.getvalue())["decision"], "allow")


if __name__ == "__main__":
    unittest.main()
