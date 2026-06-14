#!/usr/bin/env python3
"""Unit tests for scripts/run_gates.py."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_gates

ROOT = Path(__file__).resolve().parents[1]
BROKEN_FIXTURE = ROOT / "tests" / "e2e" / "fixtures" / "broken_schema_task.yaml"

GOOD_CARD = {
    "task_id": "20260614-T01",
    "date": "2026-06-14",
    "status": "in_progress",
    "goal": "unit test card",
    "definition_of_done": ["thing one", "thing two"],
    "expected_output": {"format": "md", "location": "outputs/drafts/", "filename": "x.md"},
    "risk_level": "low",
    "approval_needed": False,
    "allowed_tools": ["read_project_files", "write_drafts"],
    "max_tool_calls": 5,
    "skill_type": "ops",
}


def write_card(card: dict) -> Path:
    f = tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False)
    yaml.safe_dump(card, f, allow_unicode=True, sort_keys=False)
    f.close()
    return Path(f.name)


class TestGates(unittest.TestCase):
    def test_good_card_passes_all_runnable_gates(self):
        path = write_card(GOOD_CARD)
        try:
            results = run_gates.run_gates(path, None)
        finally:
            path.unlink(missing_ok=True)
        self.assertEqual(results["schema_check"][0], "pass")
        self.assertEqual(results["rule_check"][0], "pass")
        self.assertEqual(results["completion_check"][0], "skip")  # no --output
        self.assertEqual(results["risk_check"][0], "pass")

    def test_broken_fixture_fails_schema(self):
        results = run_gates.run_gates(BROKEN_FIXTURE, None)
        self.assertEqual(results["schema_check"][0], "fail")

    def test_rule_gate_rejects_empty_tools(self):
        card = {**GOOD_CARD, "allowed_tools": []}
        status, _ = run_gates.gate_rule(card)
        self.assertEqual(status, "fail")

    def test_rule_gate_rejects_deny_tool(self):
        card = {**GOOD_CARD, "allowed_tools": ["read_project_files", "shell_delete"]}
        status, detail = run_gates.gate_rule(card)
        self.assertEqual(status, "fail")
        self.assertIn("deny", detail)

    def test_risk_gate_fails_high_risk_in_reports(self):
        card = {**GOOD_CARD, "risk_level": "high",
                "expected_output": {"format": "md", "location": "outputs/reports/", "filename": "x.md"}}
        status, detail = run_gates.gate_risk(card, None)
        self.assertEqual(status, "fail")
        self.assertIn("drafts", detail)

    def test_risk_gate_passes_high_risk_in_drafts(self):
        card = {**GOOD_CARD, "risk_level": "high"}
        status, _ = run_gates.gate_risk(card, None)
        self.assertEqual(status, "pass")

    def test_completion_gate_with_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "outputs" / "drafts" / "x.md"
            out.parent.mkdir(parents=True)
            out.write_text("thing one\nthing two\n", encoding="utf-8")
            status, _ = run_gates.gate_completion(GOOD_CARD, out)
            self.assertEqual(status, "pass")
            out.write_text("only one\n", encoding="utf-8")
            status2, detail2 = run_gates.gate_completion(GOOD_CARD, out)
            self.assertEqual(status2, "fail")
            self.assertIn("thing two", detail2)

    def test_main_exit_codes(self):
        good = write_card(GOOD_CARD)
        try:
            self.assertEqual(run_gates.main([str(good)]), 0)   # all pass
            self.assertEqual(run_gates.main([str(BROKEN_FIXTURE)]), 1)  # gate failure
            self.assertEqual(run_gates.main(["/nonexistent/card.yaml"]), 2)  # missing file
        finally:
            good.unlink(missing_ok=True)

    def test_load_error_exits_2_not_1(self):
        # Malformed YAML and a non-mapping root are load errors (exit 2), distinct
        # from a gate failure (exit 1) — so CI/Stop hooks can tell them apart.
        bad_yaml = tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False)
        bad_yaml.write("key: [unclosed\n")
        bad_yaml.close()
        non_mapping = tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False)
        non_mapping.write("- just\n- a\n- list\n")
        non_mapping.close()
        try:
            self.assertEqual(run_gates.main([bad_yaml.name]), 2)
            self.assertEqual(run_gates.main([non_mapping.name]), 2)
            with self.assertRaises(run_gates.GateLoadError):
                run_gates.run_gates(Path(non_mapping.name), None)
        finally:
            Path(bad_yaml.name).unlink(missing_ok=True)
            Path(non_mapping.name).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
