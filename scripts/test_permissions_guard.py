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
