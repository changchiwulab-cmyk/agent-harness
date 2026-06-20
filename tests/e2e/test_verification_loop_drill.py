#!/usr/bin/env python3
"""E2E drill for the verification loop (system/VERIFICATION_LOOP.yaml).

Drives the full "verify → fix → re-verify" loop across iterations on dedicated
fixtures and pins all four terminal outcomes plus the loop ledger shape:

    pass       — schema fails on iter 1, agent's fix passes on iter 2
    hard_stop  — rule_check (deny tool in whitelist) stops with no retry
    escalated  — risk_check (high risk → reports/) locks output, no retry
    exhausted  — a fixable failure still failing at the iteration budget

The ledger entries must match the verification_loop block defined in
system/EXECUTION_LOG_SCHEMA.yaml. Fixtures live under tests/e2e/fixtures/
(NOT tasks/) so check_spec_consistency.rb's tasks/**/*.yaml glob ignores them.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import verification_loop as vl  # noqa: E402

FIX = ROOT / "tests" / "e2e" / "fixtures"
LEDGER_KEYS = {"iteration", "gate_results", "first_fail", "disposition", "action"}


class TestVerificationLoopDrill(unittest.TestCase):
    def test_schema_fixable_loop_reaches_pass(self):
        """Two-iteration loop: schema fail (iter 1) → fix → pass (iter 2)."""
        ledger = []

        r1 = vl.run(FIX / "loop_schema_broken.yaml", None, None, 1, None)
        self.assertEqual(r1["outcome"], "continue")
        self.assertEqual(r1["first_fail"], "schema_check")
        self.assertEqual(r1["disposition"], "retry_fixable")
        ledger.append(r1["ledger_entry"])

        # agent applies the fix between iterations → corrected card + completion marks
        r2 = vl.run(FIX / "loop_schema_fixed.yaml", None, ["pass", "pass"], 2, None)
        self.assertEqual(r2["outcome"], "pass")
        self.assertIsNone(r2["first_fail"])
        ledger.append(r2["ledger_entry"])

        # ledger shape matches EXECUTION_LOG_SCHEMA verification_loop block
        self.assertEqual(len(ledger), 2)
        for entry in ledger:
            self.assertEqual(set(entry), LEDGER_KEYS)
            self.assertEqual(set(entry["gate_results"]), set(vl.GATES))
        self.assertEqual(ledger[0]["gate_results"]["schema_check"], "fail")
        self.assertEqual(ledger[1]["gate_results"]["schema_check"], "pass")

    def test_rule_violation_hard_stops(self):
        r = vl.run(FIX / "loop_rule_violation.yaml", None, None, 1, None)
        self.assertEqual(r["outcome"], "hard_stop")
        self.assertEqual(r["first_fail"], "rule_check")
        self.assertEqual(r["gate_results"]["schema_check"], "pass")
        self.assertTrue(any("send_email" in m for m in r["messages"]))

    def test_high_risk_escalates(self):
        r = vl.run(FIX / "loop_risk_escalate.yaml", None, None, 1, None)
        self.assertEqual(r["outcome"], "escalated")
        self.assertEqual(r["first_fail"], "risk_check")
        self.assertEqual(r["disposition"], "escalate")

    def test_budget_exhausts_at_hard_cap(self):
        """Still failing at the iteration ceiling → exhausted (never exceeds cap=3)."""
        r = vl.run(FIX / "loop_schema_broken.yaml", None, None, 3, 3)
        self.assertEqual(r["outcome"], "exhausted")
        self.assertLessEqual(r["max_iterations"], vl.GLOBAL_HARD_CAP)

    def test_cli_exit_codes(self):
        self.assertEqual(
            vl.main([str(FIX / "loop_schema_fixed.yaml"), "--completion", "pass,pass"]), 0
        )
        self.assertEqual(vl.main([str(FIX / "loop_rule_violation.yaml")]), 1)
        self.assertEqual(vl.main([str(FIX / "missing.yaml")]), 2)


if __name__ == "__main__":
    unittest.main()
