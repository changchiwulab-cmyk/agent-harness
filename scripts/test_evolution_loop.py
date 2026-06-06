#!/usr/bin/env python3
"""Unit tests for evolution_loop.py (self-evolution loop, 20260606)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import evolution_loop as el  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

HEALTHY = {
    "cost": {"measured": 3, "rule_estimated": 0, "by_skill": {"ops": [10000, 11000, 9000]}},
    "failure": {"error_types": {}, "verify_completion": {"OK": 5, "WARN": 0, "FAIL": 0}, "audit_warn": 0, "memory_fail": 0},
    "gate": {"fail": {}, "total": {"schema_check": 5, "rule_check": 5}},
    "decision": {"overlap_pct": 30, "due": []},
}


def facets(props):
    return {p.facet for p in props}


class TestBuildProposals(unittest.TestCase):
    def test_healthy_yields_no_proposals(self):
        self.assertEqual(el.build_proposals(HEALTHY), [])

    def test_cost_recalibration_trigger(self):
        sig = {**HEALTHY, "cost": {"measured": 2, "by_skill": {"ops": [13000, 14000]}}}  # avg 13500 / 8000 ≈ 1.69
        props = el.build_proposals(sig)
        self.assertTrue(any(p.facet == "cost" and p.severity == "action" for p in props), props)

    def test_low_cost_samples_is_info(self):
        sig = {**HEALTHY, "cost": {"measured": 0, "by_skill": {}}}
        props = el.build_proposals(sig)
        self.assertTrue(any(p.facet == "cost" and p.severity == "info" for p in props))

    def test_recurring_error_trigger(self):
        sig = {**HEALTHY, "failure": {"error_types": {"tool_failure": 3}, "verify_completion": {"FAIL": 0},
                                      "audit_warn": 0, "memory_fail": 0}}
        props = el.build_proposals(sig)
        self.assertTrue(any(p.facet == "failure" and "tool_failure" in p.finding for p in props))

    def test_verify_completion_fail_is_action(self):
        sig = {**HEALTHY, "failure": {"error_types": {}, "verify_completion": {"FAIL": 1, "WARN": 0, "OK": 0},
                                      "audit_warn": 0, "memory_fail": 0}}
        props = el.build_proposals(sig)
        self.assertTrue(any(p.facet == "failure" and p.severity == "action" and "謊報" in p.finding for p in props))

    def test_gate_bottleneck_trigger(self):
        sig = {**HEALTHY, "gate": {"fail": {"schema_check": 2}, "total": {"schema_check": 3}}}  # 2/3 ≥ 0.34
        props = el.build_proposals(sig)
        self.assertTrue(any(p.facet == "gate" and p.severity == "action" for p in props))

    def test_overlap_v3_trigger(self):
        sig = {**HEALTHY, "decision": {"overlap_pct": 55, "due": []}}
        props = el.build_proposals(sig)
        self.assertTrue(any(p.facet == "decision" and "v3" in p.suggestion for p in props))

    def test_overlap_warn_not_v3(self):
        sig = {**HEALTHY, "decision": {"overlap_pct": 42, "due": []}}
        props = el.build_proposals(sig)
        decs = [p for p in props if p.facet == "decision"]
        self.assertTrue(decs and all(p.severity == "warn" for p in decs))

    def test_decision_due_trigger(self):
        sig = {**HEALTHY, "decision": {"overlap_pct": 30, "due": ["D001"]}}
        props = el.build_proposals(sig)
        self.assertTrue(any(p.facet == "decision" and "D001" in p.finding for p in props))

    def test_all_proposals_need_human(self):
        # Propose-only invariant: nothing the loop emits is auto-appliable.
        sig = {**HEALTHY, "cost": {"measured": 0, "by_skill": {}}}
        self.assertTrue(all(p.needs_human for p in el.build_proposals(sig)))


class TestEngineRunsOnLiveRepo(unittest.TestCase):
    def test_collect_and_render_do_not_crash(self):
        signals = el.collect_signals(ROOT)
        self.assertEqual(set(signals.keys()), {"cost", "failure", "gate", "decision"})
        doc = el.render_proposal_doc(el.build_proposals(signals), "2026-06-06")
        self.assertIn("自我進化提案", doc)
        self.assertIn("人工把關", doc)  # propose-only banner always present

    def test_check_mode_exits_zero(self):
        # Advisory: never breaks CI.
        self.assertEqual(el.main(["--check", "--root", str(ROOT)]), 0)


if __name__ == "__main__":
    unittest.main()
