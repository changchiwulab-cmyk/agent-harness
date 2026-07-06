#!/usr/bin/env python3
"""Unit tests for scripts/permissions_guard.py."""

from __future__ import annotations

import io
import json
import sys
import tempfile
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


class TestPermissionsYamlIntegration(unittest.TestCase):
    """H1: guard is driven by PERMISSIONS.yaml, not hardcoded."""

    def test_load_deny_list_from_real_permissions(self):
        deny = guard.load_deny_list()
        self.assertIsNotNone(deny, "real PERMISSIONS.yaml should parse")
        self.assertIn("shell_delete", deny)
        self.assertIn("send_email", deny)
        self.assertIn("modify_production_data", deny)

    def test_active_rules_filters_by_deny_set(self):
        # If shell_delete is absent, the rm -rf pattern should be inactive.
        no_delete = {"send_email", "send_message_external"}
        active = guard.active_rules(no_delete)
        rule_ids = {r.rule_id for r in active}
        self.assertNotIn("shell_delete", rule_ids)
        self.assertIn("send_email", rule_ids)

    def test_failsafe_returns_all_rules_when_load_fails(self):
        # None signals a failed load → all rules stay active.
        active = guard.active_rules(None)
        self.assertEqual(len(active), len(guard.DENY_RULES))

    def test_load_deny_list_missing_file_returns_none(self):
        deny = guard.load_deny_list(Path("/nonexistent/PERMISSIONS.yaml"))
        self.assertIsNone(deny)

    def test_load_deny_list_malformed_yaml_returns_none(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("permissions: [not, a, dict]\n  bad indent\n")
            tmp_path = Path(f.name)
        try:
            deny = guard.load_deny_list(tmp_path)
            self.assertIsNone(deny)
        finally:
            tmp_path.unlink()


if __name__ == "__main__":
    unittest.main()
