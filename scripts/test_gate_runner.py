#!/usr/bin/env python3
"""Unit tests for scripts/gate_runner.py (R11)."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gate_runner as gr

ROOT = Path(__file__).resolve().parents[1]
CLEAN_RUN_LOG = ROOT / "logs" / "runs" / "20260409-001_system-validation.yaml"
CLEAN_TASK_CARD = ROOT / "tasks" / "2026-04-09_system-validation.yaml"
BROKEN_FIXTURE = ROOT / "tests" / "e2e" / "fixtures" / "broken_schema_task.yaml"


def run_main(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = gr.main(argv)
    return code, out.getvalue(), err.getvalue()


class TestSchemaGate(unittest.TestCase):
    def test_valid_card_passes(self):
        res = gr.gate_schema(CLEAN_TASK_CARD)
        self.assertEqual(res.status, "pass")

    def test_broken_fixture_fails(self):
        res = gr.gate_schema(BROKEN_FIXTURE)
        self.assertEqual(res.status, "fail")
        self.assertIn("definition_of_done", res.reason)

    def test_missing_card_fails(self):
        res = gr.gate_schema(None)
        self.assertEqual(res.status, "fail")

    def test_empty_allowed_tools_fails(self):
        # GATE_POLICY schema_check requires allowed_tools non-empty even though the
        # shared validate_task_card.py does not — gate_runner must enforce it.
        card = {
            "task_id": "20260620-999", "date": "2026-06-20", "goal": "x",
            "definition_of_done": ["x"], "skill_type": "ops", "risk_level": "low",
            "status": "review",
            "expected_output": {"format": "md", "location": "outputs/drafts/", "filename": "x.md"},
            "allowed_tools": [],
        }
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "card.yaml"
            p.write_text(yaml.safe_dump(card, allow_unicode=True), encoding="utf-8")
            res = gr.gate_schema(p)
        self.assertEqual(res.status, "fail")
        self.assertIn("allowed_tools", res.reason)


class TestRuleGate(unittest.TestCase):
    def test_within_whitelist_passes(self):
        run = {"tools_used": [{"tool": "file_read", "call_count": 3}], "checkpoints": []}
        card = {"allowed_tools": ["file_read", "web_search"]}
        self.assertEqual(gr.gate_rule(run, card, deny_actions=set()).status, "pass")

    def test_tool_outside_whitelist_fails(self):
        run = {"tools_used": [{"tool": "web_search", "call_count": 1}], "checkpoints": []}
        card = {"allowed_tools": ["file_read"]}
        res = gr.gate_rule(run, card, deny_actions=set())
        self.assertEqual(res.status, "fail")
        self.assertIn("whitelist", res.reason)

    def test_deny_action_fails(self):
        run = {"tools_used": [{"tool": "shell_delete", "call_count": 1}], "checkpoints": []}
        card = {"allowed_tools": ["shell_delete"]}  # even if whitelisted, deny wins
        res = gr.gate_rule(run, card, deny_actions={"shell_delete"})
        self.assertEqual(res.status, "fail")
        self.assertIn("deny", res.reason)

    def test_over_threshold_without_checkpoint_fails(self):
        run = {"tools_used": [{"tool": "file_read", "call_count": 9}], "checkpoints": []}
        card = {"allowed_tools": ["file_read"]}
        res = gr.gate_rule(run, card, deny_actions=set())
        self.assertEqual(res.status, "fail")
        self.assertIn("checkpoint", res.reason)

    def test_over_threshold_with_checkpoint_passes(self):
        run = {
            "tools_used": [{"tool": "file_read", "call_count": 9}],
            "checkpoints": [{"commit": "abc", "stage": "x"}],
        }
        card = {"allowed_tools": ["file_read"]}
        self.assertEqual(gr.gate_rule(run, card, deny_actions=set()).status, "pass")


class TestCompletionGate(unittest.TestCase):
    def test_existing_output_passes(self):
        run = {"output_path": "logs/runs/20260409-001_system-validation.yaml"}
        self.assertEqual(gr.gate_completion(run).status, "pass")

    def test_empty_output_fails(self):
        self.assertEqual(gr.gate_completion({"output_path": ""}).status, "fail")

    def test_missing_output_fails(self):
        run = {"output_path": "outputs/drafts/does-not-exist-xyz.md"}
        self.assertEqual(gr.gate_completion(run).status, "fail")


class TestRiskGate(unittest.TestCase):
    def test_high_risk_not_in_drafts_fails(self):
        run = {"output_path": "outputs/reports/foo.md"}
        card = {"risk_level": "high"}
        res = gr.gate_risk(run, card)
        self.assertEqual(res.status, "fail")

    def test_high_risk_in_drafts_passes(self):
        run = {"output_path": "outputs/drafts/foo.md"}
        card = {"risk_level": "high"}
        self.assertEqual(gr.gate_risk(run, card).status, "pass")

    def test_low_risk_anywhere_passes(self):
        run = {"output_path": "outputs/reports/foo.md"}
        card = {"risk_level": "low"}
        self.assertEqual(gr.gate_risk(run, card).status, "pass")


class TestRunAllAndCli(unittest.TestCase):
    def test_clean_run_log_all_pass(self):
        results = gr.run_all(CLEAN_RUN_LOG)
        self.assertTrue(gr.overall_pass(results))
        self.assertTrue(all(r.status == "pass" for r in results))

    def test_cli_clean_run_log_exit_0(self):
        code, out, _ = run_main(["--run-log", str(CLEAN_RUN_LOG), "--json"])
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertTrue(payload[0]["overall_pass"])

    def test_cli_broken_fixture_exit_1(self):
        code, out, _ = run_main(["--task-card", str(BROKEN_FIXTURE)])
        self.assertEqual(code, 1)
        self.assertIn("fail", out)


if __name__ == "__main__":
    unittest.main()
