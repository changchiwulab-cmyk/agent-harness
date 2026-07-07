#!/usr/bin/env python3
"""Unit tests for the eval runner (G-B)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_evals  # noqa: E402


class TestParsing(unittest.TestCase):
    def test_parse_sections_and_first_h2(self):
        text = "# Title\n\n## 結論\nbody\n\n## 來源\n- a\n"
        secs = run_evals.parse_sections(text)
        self.assertEqual([s.heading for s in secs], ["Title", "結論", "來源"])
        self.assertEqual(run_evals.first_h2(secs).heading, "結論")

    def test_first_h2_none_when_only_h1(self):
        secs = run_evals.parse_sections("# only h1\nprose\n")
        self.assertIsNone(run_evals.first_h2(secs))


class TestScoring(unittest.TestCase):
    CASE = {
        "case_id": "t",
        "rubric": [
            {"id": "concl", "kind": "section_first", "args": {"heading": "結論"}},
            {"id": "src", "kind": "section_nonempty", "args": {"heading": "來源"}},
            {"id": "num", "kind": "regex", "args": {"pattern": r"\d+%"}},
            {"id": "needle", "kind": "contains_any", "args": {"needles": ["待驗證"]}},
        ],
    }

    def test_full_pass(self):
        text = "## 結論\nok\n\n## 來源\n- s\n\n38% 待驗證\n"
        res = run_evals.score_text(self.CASE, text)
        self.assertEqual(res.score, 1.0)
        self.assertTrue(res.passed)

    def test_partial_fail(self):
        text = "## 結論\nok\n\n## 來源\n- s\n"  # missing number + 待驗證
        res = run_evals.score_text(self.CASE, text)
        self.assertLess(res.score, 1.0)
        self.assertFalse(res.passed)

    def test_unknown_kind_raises(self):
        with self.assertRaises(ValueError):
            run_evals.score_text({"case_id": "x", "rubric": [{"id": "i", "kind": "bogus"}]}, "x")


class TestCalibration(unittest.TestCase):
    def test_repo_cases_discriminate(self):
        """Every shipped case must pass gold and fail bad (the calibration contract)."""
        cases = run_evals.load_cases()
        self.assertGreaterEqual(len(cases), 2, "expected at least research + analysis cases")
        rows, ok = run_evals.calibrate(cases, "rule")
        self.assertTrue(ok, f"calibration failed: {rows}")


if __name__ == "__main__":
    unittest.main()
