#!/usr/bin/env python3
"""Hook tests — pre_tool_use deny matching + post_task_use gate runner."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pre_tool_use as pre
import post_task_use as post


class TestPreToolUseDenyRules(unittest.TestCase):
    def test_rm_rf_blocked(self):
        decision, reason = pre.evaluate("rm -rf /tmp/something")
        self.assertEqual(decision, "block")
        self.assertIn("shell_delete", reason)

    def test_sendmail_blocked(self):
        decision, _ = pre.evaluate("sendmail recipient@example.com < body.txt")
        self.assertEqual(decision, "block")

    def test_slack_webhook_blocked(self):
        decision, _ = pre.evaluate("curl -X POST https://hooks.slack.com/services/X/Y/Z -d '{}'")
        self.assertEqual(decision, "block")

    def test_git_force_push_blocked(self):
        decision, _ = pre.evaluate("git push --force origin main")
        self.assertEqual(decision, "block")

    def test_benign_commands_allowed(self):
        for cmd in ("ls -la", "git status", "python -m unittest", "cat README.md"):
            decision, _ = pre.evaluate(cmd)
            self.assertEqual(decision, "allow", f"falsely blocked: {cmd}")


class TestPreToolUseHookEntry(unittest.TestCase):
    def _run_hook(self, payload: dict) -> tuple[int, dict]:
        out = io.StringIO()
        original_stdin = sys.stdin
        sys.stdin = io.StringIO(json.dumps(payload))
        try:
            with redirect_stdout(out), redirect_stderr(io.StringIO()):
                code = pre.main()
        finally:
            sys.stdin = original_stdin
        return code, json.loads(out.getvalue() or "{}")

    def test_block_on_match(self):
        code, payload = self._run_hook({"tool_name": "Bash", "tool_input": {"command": "rm -rf /tmp/x"}})
        self.assertEqual(code, 2)
        self.assertEqual(payload.get("decision"), "block")

    def test_allow_on_non_bash_tool(self):
        code, payload = self._run_hook({"tool_name": "Edit", "tool_input": {"command": "rm -rf /tmp/x"}})
        self.assertEqual(code, 0)
        self.assertEqual(payload.get("decision"), "allow")


class TestPostTaskUseGates(unittest.TestCase):
    def _build_card(self, **overrides) -> dict:
        base = {
            "task_id": "20260509-XTEST",
            "date": "2026-05-09",
            "status": "review",
            "goal": "test",
            "definition_of_done": ["alpha", "beta"],
            "expected_output": {"format": "md", "location": "outputs/drafts/", "filename": "x.md"},
            "risk_level": "low",
            "approval_needed": False,
            "allowed_tools": ["file_read", "write_drafts"],
            "max_tool_calls": 5,
            "skill_type": "ops",
        }
        base.update(overrides)
        return base

    def test_all_gates_pass_when_dod_present_in_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            card_path = tmp_path / "card.yaml"
            card_path.write_text(yaml.safe_dump(self._build_card(), allow_unicode=True), encoding="utf-8")
            drafts = tmp_path / "outputs" / "drafts"
            drafts.mkdir(parents=True)
            output = drafts / "x.md"
            output.write_text("# x\n\n- alpha\n- beta\n", encoding="utf-8")

            result = post.run(card_path, output, deny_tools=set())
        self.assertEqual(result["verdict"], "pass")
        self.assertEqual(set(result["results"].keys()), set(post.EXPECTED_GATES))

    def test_completion_warn_when_dod_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            card_path = tmp_path / "card.yaml"
            card_path.write_text(yaml.safe_dump(self._build_card(), allow_unicode=True), encoding="utf-8")
            drafts = tmp_path / "outputs" / "drafts"
            drafts.mkdir(parents=True)
            output = drafts / "x.md"
            output.write_text("# x\n\nonly alpha here\n", encoding="utf-8")  # missing 'beta'

            result = post.run(card_path, output, deny_tools=set())
        self.assertEqual(result["verdict"], "warn")
        self.assertEqual(result["results"]["completion_check"]["status"], "warn")

    def test_risk_gate_fails_when_high_risk_output_in_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            card_path = tmp_path / "card.yaml"
            card_path.write_text(
                yaml.safe_dump(self._build_card(risk_level="high"), allow_unicode=True), encoding="utf-8"
            )
            reports = tmp_path / "outputs" / "reports"
            reports.mkdir(parents=True)
            output = reports / "x.md"
            output.write_text("# x\n\n- alpha\n- beta\n", encoding="utf-8")

            result = post.run(card_path, output, deny_tools=set())
        self.assertEqual(result["verdict"], "fail")
        self.assertEqual(result["results"]["risk_check"]["status"], "fail")
        self.assertIn("risk_check", result["failed_gates"])

    def test_rule_gate_blocks_deny_listed_tool(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            card = self._build_card(allowed_tools=["file_read", "execute_payment"])
            card_path = tmp_path / "card.yaml"
            card_path.write_text(yaml.safe_dump(card, allow_unicode=True), encoding="utf-8")
            drafts = tmp_path / "outputs" / "drafts"
            drafts.mkdir(parents=True)
            output = drafts / "x.md"
            output.write_text("# x\n\n- alpha\n- beta\n", encoding="utf-8")

            result = post.run(card_path, output, deny_tools={"execute_payment"})
        self.assertEqual(result["verdict"], "fail")
        self.assertEqual(result["results"]["rule_check"]["status"], "fail")


if __name__ == "__main__":
    unittest.main()
