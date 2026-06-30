#!/usr/bin/env python3
"""Unit tests for scripts/run_evals.py (heuristic eval harness)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_evals as ev

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ["research", "analysis", "writing", "ops", "review"]


class TestChecks(unittest.TestCase):
    def test_headings_present(self):
        text = "# Title\n## 已知事實\n- x\n## 來源\n- y\n"
        self.assertTrue(ev.run_check({"type": "headings_present", "sections": ["已知事實", "來源"]}, text))
        self.assertFalse(ev.run_check({"type": "headings_present", "sections": ["待驗證"]}, text))

    def test_heading_order(self):
        text = "## 結論\nx\n## 已知事實\ny\n"
        self.assertTrue(ev.run_check({"type": "heading_order", "before": "結論", "after": "已知事實"}, text))
        self.assertFalse(ev.run_check({"type": "heading_order", "before": "已知事實", "after": "結論"}, text))

    def test_heading_nonempty(self):
        self.assertTrue(ev.run_check({"type": "heading_nonempty", "section": "來源"}, "## 來源\n- a\n"))
        self.assertFalse(ev.run_check({"type": "heading_nonempty", "section": "來源"}, "## 來源\n## 下一節\n"))

    def test_absent_and_present(self):
        self.assertFalse(ev.run_check({"type": "absent", "patterns": ["根據研究"]}, "根據研究指出"))
        self.assertTrue(ev.run_check({"type": "present_any", "patterns": ["下一步", "next"]}, "## 下一步\n"))
        self.assertFalse(ev.run_check({"type": "present_all", "patterns": ["必須修改", "建議修改"]}, "只有必須修改"))


class TestScoring(unittest.TestCase):
    def test_required_failure_forces_fail(self):
        rubric = {
            "pass_threshold": 0.1,
            "criteria": [
                {"id": "req", "weight": 1, "required": True,
                 "check": {"type": "present_any", "patterns": ["NEVER_THERE"]}},
                {"id": "ok", "weight": 9,
                 "check": {"type": "present_any", "patterns": ["x"]}},
            ],
        }
        result = ev.score_output("x", rubric)
        self.assertTrue(result["required_fail"])
        self.assertFalse(result["passed"])  # required fail overrides high pct

    def test_threshold_gate(self):
        rubric = {
            "pass_threshold": 0.8,
            "criteria": [
                {"id": "a", "weight": 1, "check": {"type": "present_any", "patterns": ["x"]}},
                {"id": "b", "weight": 1, "check": {"type": "present_any", "patterns": ["NO"]}},
            ],
        }
        # 1/2 = 0.5 < 0.8 → fail
        self.assertFalse(ev.score_output("x", rubric)["passed"])


class TestRubricsExist(unittest.TestCase):
    def test_every_skill_has_rubric(self):
        for skill in SKILLS:
            rubric = ev.load_rubric(skill, ROOT)
            self.assertEqual(rubric.get("skill"), skill)
            self.assertTrue(rubric.get("criteria"))


class TestGoldenCases(unittest.TestCase):
    def test_all_golden_match_expectation(self):
        cases = ev.run_golden(ROOT)
        self.assertTrue(cases, "no golden cases found")
        mismatches = [c["case_id"] for c in cases if not c["match"]]
        self.assertEqual(mismatches, [], f"golden mismatches: {mismatches}")

    def test_each_skill_has_a_pass_and_fail_case(self):
        cases = ev.run_golden(ROOT)
        by_skill: dict[str, set[bool]] = {}
        for c in cases:
            by_skill.setdefault(c["skill"], set()).add(c["expect_pass"])
        for skill in SKILLS:
            self.assertIn(skill, by_skill, f"{skill} has no golden cases")
            self.assertEqual(by_skill[skill], {True, False},
                             f"{skill} needs both a pass and a fail golden case")


if __name__ == "__main__":
    unittest.main()
