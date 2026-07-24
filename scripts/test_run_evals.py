#!/usr/bin/env python3
"""Unit tests for the eval runner (G-B)."""
from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest import mock

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
        self.assertGreaterEqual(
            len(cases), 6, "expected 6/6 skill coverage (research/analysis/writing/ops/review/retro)"
        )
        rows, ok = run_evals.calibrate(cases, "rule")
        self.assertTrue(ok, f"calibration failed: {rows}")

    def test_all_six_skills_covered(self):
        """One case per skill — the 6/6 coverage contract."""
        skills = {c.get("skill") for c in run_evals.load_cases()}
        self.assertEqual(
            skills, {"research", "analysis", "writing", "ops", "review", "retro"}
        )


class TestLLMJudge(unittest.TestCase):
    """Provider branch + offline fallback. No test touches the network:
    the seam functions (_llm_available / _call_anthropic) are monkeypatched."""

    CASE = {
        "case_id": "llm-t",
        "definition_of_done": ["結論先行", "標記待驗證"],
        "rubric": [
            {"id": "a", "kind": "section_first", "args": {"heading": "結論"}},
            {"id": "b", "kind": "contains_any", "args": {"needles": ["待驗證"]}},
        ],
        "gold_example": "## 結論\nok 待驗證\n",
        "bad_example": "prose only\n",
    }

    def test_llm_availability_follows_env_key(self):
        with mock.patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test"}):
            self.assertTrue(run_evals._llm_available())
        with mock.patch.dict("os.environ", {}, clear=True):
            self.assertFalse(run_evals._llm_available())

    def test_llm_path_scores_from_provider(self):
        reply = '{"items": {"a": true, "b": true}}'
        with mock.patch.object(run_evals, "_call_anthropic", return_value=reply) as m:
            res = run_evals._judge_score(self.CASE, "candidate text", "llm")
        self.assertTrue(res.passed)
        self.assertEqual(res.items, {"a": True, "b": True})
        m.assert_called_once()

    def test_llm_partial_fail(self):
        reply = 'here you go: {"items": {"a": true, "b": false}} thanks'  # tolerate surrounding prose
        with mock.patch.object(run_evals, "_call_anthropic", return_value=reply):
            res = run_evals.llm_score_text(self.CASE, "x")
        self.assertFalse(res.passed)
        self.assertEqual(res.items, {"a": True, "b": False})

    def test_provider_exception_falls_back_to_rule(self):
        with mock.patch.object(run_evals, "_call_anthropic", side_effect=RuntimeError("boom")):
            with contextlib.redirect_stderr(io.StringIO()) as err:
                res = run_evals._judge_score(self.CASE, self.CASE["gold_example"], "llm")
        rule = run_evals.score_text(self.CASE, self.CASE["gold_example"])
        self.assertEqual(res.items, rule.items)  # identical to rule result
        self.assertTrue(res.passed)
        self.assertIn("falling back to rule", err.getvalue())

    def test_bad_json_falls_back_to_rule(self):
        with mock.patch.object(run_evals, "_call_anthropic", return_value="not json at all"):
            with contextlib.redirect_stderr(io.StringIO()) as err:
                res = run_evals._judge_score(self.CASE, self.CASE["bad_example"], "llm")
        rule = run_evals.score_text(self.CASE, self.CASE["bad_example"])
        self.assertEqual(res.items, rule.items)
        self.assertFalse(res.passed)
        self.assertIn("falling back to rule", err.getvalue())

    def test_calibrate_routes_through_llm_judge(self):
        def fake_call(prompt: str) -> str:
            # The candidate output is embedded in the prompt; mirror the rule
            # verdict so the plumbing (calibrate → _judge_score → llm) is exercised.
            ok = "## 結論" in prompt and "待驗證" in prompt
            v = "true" if ok else "false"
            return '{"items": {"a": %s, "b": %s}}' % (v, v)

        with mock.patch.object(run_evals, "_call_anthropic", side_effect=fake_call):
            rows, ok = run_evals.calibrate([self.CASE], "llm")
        self.assertTrue(ok)
        self.assertEqual(rows[0]["judge"], "llm")

    def test_main_llm_without_key_prints_notice_and_uses_rule(self):
        with mock.patch.object(run_evals, "_llm_available", return_value=False):
            with contextlib.redirect_stderr(io.StringIO()) as err, \
                 contextlib.redirect_stdout(io.StringIO()) as out:
                rc = run_evals.main(["run_evals.py", "--judge", "llm"])
        self.assertEqual(rc, 0)
        self.assertIn("ANTHROPIC_API_KEY not set", err.getvalue())
        self.assertIn("judge=rule", out.getvalue())  # fell back to CI-safe judge

    def test_build_prompt_carries_rubric_ids_and_dod(self):
        prompt = run_evals._build_judge_prompt(self.CASE, "候選")
        self.assertIn("結論先行", prompt)   # DoD present
        self.assertIn('"a"', prompt)         # rubric ids present
        self.assertIn('"b"', prompt)
        self.assertIn("候選", prompt)        # candidate embedded


if __name__ == "__main__":
    unittest.main()
