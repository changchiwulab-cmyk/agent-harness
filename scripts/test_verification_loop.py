#!/usr/bin/env python3
"""Unit tests for scripts/verification_loop.py — the verification-loop driver.

Pins the per-gate logic, disposition mapping, iteration-budget arithmetic, and
the decide() terminal-state machine so the loop's "可檢驗工程" contract cannot
silently regress.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import verification_loop as vl  # noqa: E402

FIX = ROOT / "tests" / "e2e" / "fixtures"


def card(**over):
    base = {
        "task_id": "20260620-999",
        "definition_of_done": ["a", "b"],
        "skill_type": "ops",
        "risk_level": "low",
        "expected_output": {"format": "md", "location": "outputs/drafts/", "filename": "x.md"},
        "allowed_tools": ["file_read"],
    }
    base.update(over)
    return base


def outcome_with(first_fail, results):
    o = vl.GateOutcome()
    o.results.update(results)
    o.first_fail = first_fail
    return o


class TestGates(unittest.TestCase):
    def test_rule_pass_clean(self):
        ok, msgs = vl.check_rule(card(), None)
        self.assertTrue(ok, msgs)

    def test_rule_fail_deny_tool(self):
        ok, msgs = vl.check_rule(card(allowed_tools=["file_read", "send_email"]), None)
        self.assertFalse(ok)
        self.assertTrue(any("send_email" in m for m in msgs))

    def test_rule_fail_tool_outside_whitelist(self):
        run_log = {"execution_log": {"tools_used": [{"tool": "web_search", "call_count": 1}]}}
        ok, msgs = vl.check_rule(card(allowed_tools=["file_read"]), run_log)
        self.assertFalse(ok)
        self.assertTrue(any("白名單外" in m for m in msgs))

    def test_rule_fail_too_many_web_searches(self):
        run_log = {"execution_log": {"tools_used": [{"tool": "web_search", "call_count": 4}]}}
        ok, msgs = vl.check_rule(card(allowed_tools=["web_search"]), run_log)
        self.assertFalse(ok)
        self.assertTrue(any("超過 3 輪" in m for m in msgs))

    def test_rule_ask_tool_used_without_approval_fails(self):
        run_log = {"execution_log": {
            "tools_used": [{"tool": "write_reports", "call_count": 1}],
            "approvals": [],
        }}
        ok, msgs = vl.check_rule(card(allowed_tools=["write_reports"]), run_log)
        self.assertFalse(ok)
        self.assertTrue(any("ask 等級" in m for m in msgs))

    def test_rule_ask_tool_used_with_approval_passes(self):
        run_log = {"execution_log": {
            "tools_used": [{"tool": "write_reports", "call_count": 1}],
            "approvals": [{"action": "write_reports 正式報告", "status": "approved", "approved_by": "human"}],
        }}
        ok, msgs = vl.check_rule(card(allowed_tools=["write_reports"]), run_log)
        self.assertTrue(ok, msgs)

    def test_rule_ask_tool_declared_only_no_runlog_passes(self):
        # 僅在 allowed_tools 宣告 ask 工具、無 run-log → 無法評估執行，不誤判
        ok, msgs = vl.check_rule(card(allowed_tools=["write_reports"]), None)
        self.assertTrue(ok, msgs)

    def test_completion_not_run_when_no_marks(self):
        ok, msgs = vl.check_completion(card(), None)
        self.assertFalse(ok)
        self.assertIsNone(msgs)  # sentinel → caller marks not_run

    def test_completion_length_mismatch(self):
        ok, msgs = vl.check_completion(card(), ["pass"])  # dod has 2
        self.assertFalse(ok)
        self.assertTrue(any("長度" in m for m in msgs))

    def test_completion_all_pass(self):
        ok, msgs = vl.check_completion(card(), ["pass", "pass"])
        self.assertTrue(ok, msgs)

    def test_completion_one_fail_lists_gap(self):
        ok, msgs = vl.check_completion(card(), ["pass", "fail"])
        self.assertFalse(ok)
        self.assertEqual(len(msgs), 1)
        self.assertIn("[1]", msgs[0])

    def test_risk_high_reports_fails(self):
        c = card(risk_level="high", expected_output={"format": "md", "location": "outputs/reports/", "filename": "x.md"})
        ok, msgs = vl.check_risk(c)
        self.assertFalse(ok)

    def test_risk_high_drafts_passes(self):
        c = card(risk_level="high")
        ok, _ = vl.check_risk(c)
        self.assertTrue(ok)

    def test_risk_low_reports_passes(self):
        c = card(expected_output={"format": "md", "location": "outputs/reports/", "filename": "x.md"})
        ok, _ = vl.check_risk(c)
        self.assertTrue(ok)

    def test_risk_high_drafts_lookalike_prefix_fails(self):
        # outputs/drafts-public/ 與 outputs/drafts/ 僅前綴相似，必須被擋
        c = card(risk_level="high",
                 expected_output={"format": "md", "location": "outputs/drafts-public/", "filename": "x.md"})
        ok, _ = vl.check_risk(c)
        self.assertFalse(ok)

    def test_risk_high_drafts_subdir_passes(self):
        c = card(risk_level="high",
                 expected_output={"format": "md", "location": "outputs/drafts/sub/", "filename": "x.md"})
        ok, _ = vl.check_risk(c)
        self.assertTrue(ok)


class TestBudget(unittest.TestCase):
    def test_attempts_schema_capped_at_2(self):
        self.assertEqual(vl.attempts_allowed("schema_check", 3), 2)

    def test_attempts_completion_uses_global(self):
        self.assertEqual(vl.attempts_allowed("completion_check", 3), 3)

    def test_attempts_rule_and_risk_single(self):
        self.assertEqual(vl.attempts_allowed("rule_check", 3), 1)
        self.assertEqual(vl.attempts_allowed("risk_check", 3), 1)


class TestDecide(unittest.TestCase):
    def test_pass(self):
        o = outcome_with(None, {g: "pass" for g in vl.GATES})
        self.assertEqual(vl.decide(o, 1, 3)[0], "pass")

    def test_completion_not_run_is_continue(self):
        o = outcome_with(None, {"schema_check": "pass", "rule_check": "pass",
                                "completion_check": "not_run", "risk_check": "pass"})
        out, disp, _ = vl.decide(o, 1, 3)
        self.assertEqual(out, "continue")
        self.assertEqual(disp, "human_gated")

    def test_completion_not_run_exhausts_at_cap(self):
        # 終止保證：not_run 在達到迭代上限時必須 exhausted，不可無限 continue
        o = outcome_with(None, {"schema_check": "pass", "rule_check": "pass",
                                "completion_check": "not_run", "risk_check": "pass"})
        self.assertEqual(vl.decide(o, 3, 3)[0], "exhausted")

    def test_schema_fail_continue_then_exhausted(self):
        o = outcome_with("schema_check", {"schema_check": "fail"})
        self.assertEqual(vl.decide(o, 1, 3)[0], "continue")
        self.assertEqual(vl.decide(o, 2, 3)[0], "exhausted")  # schema cap = 2 attempts

    def test_rule_fail_hard_stop(self):
        o = outcome_with("rule_check", {"schema_check": "pass", "rule_check": "fail"})
        out, disp, _ = vl.decide(o, 1, 3)
        self.assertEqual(out, "hard_stop")
        self.assertEqual(disp, "hard_stop")

    def test_risk_fail_escalated(self):
        o = outcome_with("risk_check", {"schema_check": "pass", "rule_check": "pass",
                                        "completion_check": "pass", "risk_check": "fail"})
        self.assertEqual(vl.decide(o, 1, 3)[0], "escalated")

    def test_completion_fail_exhausts_at_cap(self):
        o = outcome_with("completion_check", {"schema_check": "pass", "rule_check": "pass",
                                              "completion_check": "fail"})
        self.assertEqual(vl.decide(o, 1, 3)[0], "continue")
        self.assertEqual(vl.decide(o, 3, 3)[0], "exhausted")


class TestRunEndToEnd(unittest.TestCase):
    def test_run_pass_on_fixed_fixture(self):
        res = vl.run(FIX / "loop_schema_fixed.yaml", None, ["pass", "pass"], 1, None)
        self.assertEqual(res["outcome"], "pass")

    def test_run_collection_error_on_missing_card(self):
        with self.assertRaises(vl.CollectionError):
            vl.run(FIX / "does_not_exist.yaml", None, None, 1, None)


if __name__ == "__main__":
    unittest.main()
