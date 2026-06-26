#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for scripts/run_evals.py — deterministic eval runner.

無外部依賴（PyYAML 已是 CI 既有依賴）。以 unittest 執行：
  python3 scripts/test_run_evals.py
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_evals as RE  # noqa: E402

SAMPLE = """# 標題

## 結論
這是結論。

## 已知事實
- 事實一

## 來源
- 來源一
"""


class TestCheckPrimitives(unittest.TestCase):
    def test_heading_index_found_and_order(self):
        self.assertTrue(RE.heading_index(SAMPLE, "結論") >= 0)
        self.assertEqual(RE.heading_index(SAMPLE, "不存在"), -1)
        self.assertLess(
            RE.heading_index(SAMPLE, "結論"),
            RE.heading_index(SAMPLE, "已知事實"),
        )

    def test_section_body_nonempty_vs_empty(self):
        self.assertIn("來源一", RE.section_body(SAMPLE, "來源"))
        self.assertEqual(RE.section_body(SAMPLE, "不存在").strip(), "")

    def test_required_heading(self):
        self.assertTrue(RE.run_check(SAMPLE, {"type": "required_heading", "token": "結論"}))
        self.assertFalse(RE.run_check(SAMPLE, {"type": "required_heading", "token": "高風險假設"}))

    def test_forbidden_and_required_regex(self):
        self.assertTrue(RE.run_check(SAMPLE, {"type": "forbidden_regex", "pattern": "根據研究"}))
        self.assertFalse(RE.run_check("根據研究顯示", {"type": "forbidden_regex", "pattern": "根據研究"}))
        self.assertTrue(RE.run_check(SAMPLE, {"type": "required_regex", "pattern": "事實"}))

    def test_heading_order_and_nonempty(self):
        self.assertTrue(RE.run_check(SAMPLE, {"type": "heading_order", "before": "結論", "after": "已知事實"}))
        self.assertFalse(RE.run_check(SAMPLE, {"type": "heading_order", "before": "已知事實", "after": "結論"}))
        self.assertTrue(RE.run_check(SAMPLE, {"type": "heading_nonempty", "token": "來源"}))

    def test_unknown_check_type_raises(self):
        with self.assertRaises(ValueError):
            RE.run_check(SAMPLE, {"type": "nope"})

    def test_malformed_check_missing_field_raises(self):
        # 缺 pattern / token / before-after → 必須大聲 raise（不靜默當失敗）
        with self.assertRaises(ValueError):
            RE.run_check(SAMPLE, {"id": "x", "type": "required_regex"})
        with self.assertRaises(ValueError):
            RE.run_check(SAMPLE, {"id": "x", "type": "required_heading"})
        with self.assertRaises(ValueError):
            RE.run_check(SAMPLE, {"id": "x", "type": "heading_order", "before": "結論"})


class TestEvaluateScoring(unittest.TestCase):
    def test_score_and_threshold(self):
        rubric = {
            "pass_threshold": 0.5,
            "checks": [
                {"id": "a", "type": "required_heading", "token": "結論"},   # pass
                {"id": "b", "type": "required_heading", "token": "缺席"},   # fail
            ],
        }
        res = RE.evaluate(rubric, SAMPLE)
        self.assertEqual(res["n_pass"], 1)
        self.assertEqual(res["total"], 2)
        self.assertEqual(res["score"], 0.5)
        self.assertTrue(res["passed"])  # 0.5 >= 0.5

    def test_empty_text_scores_zero(self):
        rubric = {"pass_threshold": 0.8, "checks": [{"id": "a", "type": "required_heading", "token": "結論"}]}
        res = RE.evaluate(rubric, "")
        self.assertEqual(res["score"], 0.0)
        self.assertFalse(res["passed"])

    def test_evaluate_propagates_malformed_check(self):
        # malformed rubric 不可被吞成「失敗的一條」，要往外拋
        rubric = {"pass_threshold": 0.8, "checks": [{"id": "a", "type": "forbidden_regex"}]}
        with self.assertRaises(ValueError):
            RE.evaluate(rubric, SAMPLE)


class TestExtractionAndGolden(unittest.TestCase):
    def test_discover_skills_has_five(self):
        skills = RE.discover_skills()
        for s in ("research", "analysis", "writing", "ops", "review"):
            self.assertIn(s, skills)

    def test_extract_examples_returns_both(self):
        ex = RE.extract_examples("research")
        self.assertTrue(ex["good"] and "結論" in ex["good"])
        self.assertTrue(ex["bad"] is not None)

    def test_parse_examples_missing_section_returns_none(self):
        md = "## 好的輸出範例\n\n```markdown\n## 結論\nok\n```\n"  # 無壞範例
        ex = RE.parse_examples(md)
        self.assertIsNotNone(ex["good"])
        self.assertIsNone(ex["bad"])

    def test_golden_invariant_raises_when_example_missing(self):
        import unittest.mock as mock
        with mock.patch.object(RE, "extract_examples", return_value={"good": "x", "bad": None}):
            with self.assertRaises(ValueError):
                RE.check_golden_invariant("research")

    def test_golden_invariant_all_skills(self):
        for skill in RE.discover_skills():
            ok, good, bad = RE.check_golden_invariant(skill)
            self.assertTrue(
                ok,
                "%s: good必過/bad必不過 不變式違反 (good=%s bad=%s)" % (skill, good["passed"], bad["passed"]),
            )
            self.assertGreater(good["score"], bad["score"], "%s: good 分數應高於 bad" % skill)


if __name__ == "__main__":
    unittest.main()
