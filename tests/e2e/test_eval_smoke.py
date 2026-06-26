#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E2E smoke：eval harness 的 good>bad 不變式必須對每個 skill 成立。

對應 system/EVAL_POLICY.md 的 regression 不變式。執行：
  python3 tests/e2e/test_eval_smoke.py
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import run_evals as RE  # noqa: E402


class TestEvalSmoke(unittest.TestCase):
    def test_regression_passes_for_all_skills(self):
        skills = RE.discover_skills()
        self.assertGreaterEqual(len(skills), 5, "應至少有 5 個 skill rubric")
        failures = RE.regression(skills, quiet=True)
        self.assertEqual(failures, [], "eval regression 失敗的 skill：%s" % failures)

    def test_each_skill_good_beats_bad(self):
        for skill in RE.discover_skills():
            ok, good, bad = RE.check_golden_invariant(skill)
            self.assertTrue(good["passed"], "%s good 範例應通過" % skill)
            self.assertFalse(bad["passed"], "%s bad 範例不應通過" % skill)


if __name__ == "__main__":
    unittest.main()
