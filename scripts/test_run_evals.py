#!/usr/bin/env python3
"""Unit tests for scripts/run_evals.py."""

from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_evals as re_


RESEARCH_RUBRIC = {
    "skill": "research",
    "pass_threshold": 80,
    "dimensions": [
        {"id": "sources", "blocker": True},
        {"id": "classification", "blocker": False},
        {"id": "conclusion_first", "blocker": False},
        {"id": "honesty", "blocker": False},
    ],
}


def write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


class TestScoring(unittest.TestCase):
    def test_score_pct(self):
        self.assertEqual(re_.compute_score_pct([2, 2, 2, 2]), 100.0)
        self.assertEqual(re_.compute_score_pct([1, 1, 1, 1]), 50.0)
        self.assertEqual(re_.compute_score_pct([2, 2, 2, 1]), 87.5)
        self.assertEqual(re_.compute_score_pct([]), 0.0)

    def test_verdict_pass(self):
        pct, v = re_.compute_verdict(
            {"sources": 2, "classification": 2, "conclusion_first": 2, "honesty": 2}, RESEARCH_RUBRIC
        )
        self.assertEqual((pct, v), (100.0, "pass"))

    def test_verdict_partial(self):
        # 6/8 = 75% < 80 threshold, no blocker zero -> partial
        pct, v = re_.compute_verdict(
            {"sources": 2, "classification": 1, "conclusion_first": 1, "honesty": 2}, RESEARCH_RUBRIC
        )
        self.assertEqual((pct, v), (75.0, "partial"))

    def test_verdict_fail_low_pct(self):
        pct, v = re_.compute_verdict(
            {"sources": 1, "classification": 1, "conclusion_first": 0, "honesty": 1}, RESEARCH_RUBRIC
        )
        self.assertEqual(v, "fail")  # 3/8 = 37.5%

    def test_verdict_fail_blocker_zero_overrides_high_pct(self):
        # sources (blocker) == 0 forces fail even though pct = 75%
        pct, v = re_.compute_verdict(
            {"sources": 0, "classification": 2, "conclusion_first": 2, "honesty": 2}, RESEARCH_RUBRIC
        )
        self.assertEqual(pct, 75.0)
        self.assertEqual(v, "fail")


class TestValidateResult(unittest.TestCase):
    rubrics = {"research": RESEARCH_RUBRIC}

    def _record(self, **over):
        rec = {
            "eval_id": "EVAL-20260628-001",
            "task_id": "20260628-001",
            "skill_type": "research",
            "target": "outputs/drafts/x.md",
            "judge": "rubric_self",
            "scored_at": "2026-06-28",
            "dimensions": [
                {"id": "sources", "score": 2},
                {"id": "classification", "score": 2},
                {"id": "conclusion_first", "score": 2},
                {"id": "honesty", "score": 2},
            ],
            "score_pct": 100.0,
            "verdict": "pass",
        }
        rec.update(over)
        return rec

    def test_valid_record(self):
        self.assertEqual(re_.validate_result("x.yaml", self._record(), self.rubrics), [])

    def test_missing_required_field(self):
        errs = re_.validate_result("x.yaml", self._record(eval_id=""), self.rubrics)
        self.assertTrue(any("eval_id" in e for e in errs))

    def test_bad_score_value(self):
        rec = self._record()
        rec["dimensions"][0]["score"] = 3
        errs = re_.validate_result("x.yaml", rec, self.rubrics)
        self.assertTrue(any("score" in e for e in errs))

    def test_missing_dimension(self):
        rec = self._record()
        rec["dimensions"] = rec["dimensions"][:3]  # drop honesty
        errs = re_.validate_result("x.yaml", rec, self.rubrics)
        self.assertTrue(any("missing rubric dimensions" in e for e in errs))

    def test_unknown_dimension(self):
        rec = self._record()
        rec["dimensions"].append({"id": "made_up", "score": 2})
        errs = re_.validate_result("x.yaml", rec, self.rubrics)
        self.assertTrue(any("unknown dimensions" in e for e in errs))

    def test_verdict_mismatch_is_caught(self):
        # scores say partial but record claims pass -> drift caught
        rec = self._record(verdict="pass", score_pct=75.0)
        rec["dimensions"] = [
            {"id": "sources", "score": 2},
            {"id": "classification", "score": 1},
            {"id": "conclusion_first", "score": 1},
            {"id": "honesty", "score": 2},
        ]
        errs = re_.validate_result("x.yaml", rec, self.rubrics)
        self.assertTrue(any("verdict" in e for e in errs))

    def test_score_pct_drift_is_caught(self):
        errs = re_.validate_result("x.yaml", self._record(score_pct=90.0), self.rubrics)
        self.assertTrue(any("score_pct" in e for e in errs))

    def test_non_numeric_score_pct_rejected_without_crash(self):
        # Hand-authored "80%" / "pending" must surface as a schema error, not a traceback.
        for bad in ("80%", "pending"):
            errs = re_.validate_result("x.yaml", self._record(score_pct=bad), self.rubrics)
            self.assertTrue(any("must be a number" in e for e in errs), bad)


class TestGoldenRegression(unittest.TestCase):
    def test_pass_meets_expected(self):
        results = [("r.yaml", {"target": "a.md", "verdict": "pass"})]
        golden = [{"case_id": "G1", "target": "a.md", "expected_verdict": "pass"}]
        self.assertEqual(re_.check_golden_regression(results, golden), [])

    def test_partial_below_expected_pass_is_regression(self):
        results = [("r.yaml", {"target": "a.md", "verdict": "partial"})]
        golden = [{"case_id": "G1", "target": "a.md", "expected_verdict": "pass"}]
        errs = re_.check_golden_regression(results, golden)
        self.assertTrue(any("regression" in e for e in errs))

    def test_no_matching_result_is_inert(self):
        results = [("r.yaml", {"target": "other.md", "verdict": "fail"})]
        golden = [{"case_id": "G1", "target": "a.md", "expected_verdict": "pass"}]
        self.assertEqual(re_.check_golden_regression(results, golden), [])


class TestCheckIntegration(unittest.TestCase):
    def _repo(self, root: Path, result_body: str) -> None:
        for skill, dims in (
            ("research", ["sources", "classification", "conclusion_first", "honesty"]),
            ("analysis", ["conclusion"]),
            ("writing", ["structure"]),
            ("ops", ["plan_first"]),
            ("review", ["specificity"]),
        ):
            lines = [f"skill: {skill}", "pass_threshold: 80", "dimensions:"]
            for i, d in enumerate(dims):
                lines.append(f"  - id: {d}")
                lines.append(f"    blocker: {'true' if i == 0 else 'false'}")
            write(root / "evals" / "rubrics" / f"{skill}.yaml", "\n".join(lines) + "\n")
        write(root / "evals" / "golden" / "cases.yaml", "golden_cases: []\n")
        write(root / "evals" / "results" / "EVAL-1.yaml", result_body)

    def test_check_passes_on_valid_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._repo(root, (
                "eval_record:\n"
                '  eval_id: "EVAL-1"\n  task_id: "20260628-001"\n  skill_type: "research"\n'
                '  target: "x.md"\n  judge: "rubric_self"\n  scored_at: "2026-06-28"\n'
                "  dimensions:\n"
                "    - {id: sources, score: 2}\n    - {id: classification, score: 2}\n"
                "    - {id: conclusion_first, score: 2}\n    - {id: honesty, score: 2}\n"
                "  score_pct: 100.0\n  verdict: pass\n"
            ))
            out = io.StringIO()
            with redirect_stdout(out):
                code = re_.cmd_check(root)
            self.assertEqual(code, 0, out.getvalue())

    def test_check_fails_on_verdict_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._repo(root, (
                "eval_record:\n"
                '  eval_id: "EVAL-1"\n  task_id: "20260628-001"\n  skill_type: "research"\n'
                '  target: "x.md"\n  judge: "rubric_self"\n  scored_at: "2026-06-28"\n'
                "  dimensions:\n"
                "    - {id: sources, score: 0}\n    - {id: classification, score: 2}\n"
                "    - {id: conclusion_first, score: 2}\n    - {id: honesty, score: 2}\n"
                "  score_pct: 75.0\n  verdict: pass\n"  # blocker=0 should be fail
            ))
            out = io.StringIO()
            with redirect_stdout(out):
                code = re_.cmd_check(root)
            self.assertEqual(code, 1)
            self.assertIn("verdict", out.getvalue())


class TestRealRepo(unittest.TestCase):
    def test_check_real_repo_is_green(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = re_.cmd_check(re_.ROOT)
        self.assertEqual(code, 0, out.getvalue())

    def test_scaffold_real_repo(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = re_.cmd_scaffold(
                "outputs/drafts/20260502-T01_taiwan-ai-industry-quick-scan.md", "research", re_.ROOT
            )
        self.assertEqual(code, 0)
        text = out.getvalue()
        self.assertIn("skill_type: \"research\"", text)
        self.assertIn("id: sources", text)


if __name__ == "__main__":
    unittest.main()
