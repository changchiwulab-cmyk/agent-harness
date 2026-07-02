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
        # PERMISSIONS.yaml shell_delete deliberately scopes runtime blocking to
        # the high-blast-radius -r/-f variants; single-file `rm` is left to
        # model-level judgement. This test pins that scoping.
        decision, reason = guard.evaluate("rm tempfile.txt")
        self.assertEqual(decision, "allow")
        self.assertIsNone(reason)

    def test_nohup_blocked(self):
        decision, reason = guard.evaluate("nohup python3 worker.py")
        self.assertEqual(decision, "block")
        self.assertIn("spawn_background_process", reason)

    def test_trailing_ampersand_blocked(self):
        decision, reason = guard.evaluate("python3 server.py &")
        self.assertEqual(decision, "block")
        self.assertIn("spawn_background_process", reason)

    def test_double_ampersand_allowed(self):
        decision, reason = guard.evaluate("make build && make test")
        self.assertEqual(decision, "allow")
        self.assertIsNone(reason)

    def test_ampersand_separator_blocked(self):
        # `cmd & cmd2` backgrounds cmd just like a trailing & (codex P2)
        decision, reason = guard.evaluate("python3 server.py & echo ok")
        self.assertEqual(decision, "block")
        self.assertIn("spawn_background_process", reason)

    def test_stderr_redirect_allowed(self):
        # 2>&1 / >&2 are redirections, not background separators
        decision, reason = guard.evaluate("make build 2>&1")
        self.assertEqual(decision, "allow")
        self.assertIsNone(reason)

    def test_ampersand_in_url_allowed(self):
        # Quote-free heuristic: & without surrounding whitespace (query strings)
        # must not trip the background rule. Known trade-off: a quoted string
        # containing " & " (e.g. echo "a & b") will false-positive — the guard
        # does not parse shell quoting.
        decision, reason = guard.evaluate('curl "http://example.com/?a=1&b=2"')
        self.assertEqual(decision, "allow")
        self.assertIsNone(reason)

    def test_tee_into_memory_blocked(self):
        decision, reason = guard.evaluate("echo note | tee memory/notes.md")
        self.assertEqual(decision, "block")
        self.assertIn("auto_write_memory", reason)

    def test_redirect_into_memory_blocked(self):
        decision, reason = guard.evaluate("echo fact >> memory/long_term.md")
        self.assertEqual(decision, "block")
        self.assertIn("auto_write_memory", reason)

    def test_read_from_memory_allowed(self):
        decision, reason = guard.evaluate("grep -rn topic memory/")
        self.assertEqual(decision, "allow")
        self.assertIsNone(reason)

    def test_quoted_memory_writes_blocked(self):
        # Quoted paths must not bypass the rule (codex P2)
        for cmd in (
            'echo fact >> "memory/long_term.md"',
            "echo x | tee 'memory/notes.md'",
            'cp a "memory/a"',
        ):
            decision, reason = guard.evaluate(cmd)
            self.assertEqual(decision, "block", cmd)
            self.assertIn("auto_write_memory", reason)

    def test_curl_publish_api_blocked(self):
        decision, reason = guard.evaluate(
            "curl -X POST https://api.twitter.com/2/tweets -d '{}'"
        )
        self.assertEqual(decision, "block")
        self.assertIn("publish_content", reason)


class TestPermissionsSync(unittest.TestCase):
    """DENY_RULES must stay in lockstep with system/PERMISSIONS.yaml.

    The guard cannot parse YAML at hook time (no dependencies), so this test
    is the enforcement point for the docstring's sync claim: deny list ↔
    deny_enforcement ↔ DENY_RULES must agree three ways.
    """

    @classmethod
    def setUpClass(cls):
        import yaml  # available in CI (pip install pyyaml); not needed by the hook itself

        doc = yaml.safe_load(guard.PERMISSIONS_PATH.read_text(encoding="utf-8"))
        cls.deny = set(doc["permissions"]["deny"])
        cls.enforcement = dict(doc["deny_enforcement"])
        cls.rule_ids = {rule.rule_id for rule in guard.DENY_RULES}

    def test_enforcement_covers_exactly_the_deny_list(self):
        self.assertEqual(self.deny, set(self.enforcement.keys()))

    def test_every_runtime_entry_has_a_guard_rule(self):
        runtime_ids = {k for k, v in self.enforcement.items() if v == "runtime"}
        self.assertEqual(runtime_ids, self.rule_ids)

    def test_every_guard_rule_is_a_declared_deny(self):
        self.assertTrue(self.rule_ids <= self.deny,
                        f"guard rules not in PERMISSIONS deny list: {self.rule_ids - self.deny}")

    def test_enforcement_values_are_valid(self):
        self.assertTrue(set(self.enforcement.values()) <= {"runtime", "model"})


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
