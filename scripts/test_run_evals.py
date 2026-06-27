#!/usr/bin/env python3
"""Unit tests for scripts/run_evals.py."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_evals as re


RESEARCH_RUBRIC = {
    "skill": "research",
    "min_auto_pass_ratio": 0.5,
    "auto_checks": [
        {"id": "conclusion-first", "scope": "head", "any_markers": ["結論", "摘要"]},
        {"id": "structure", "scope": "full", "any_markers": ["來源", "待驗證"]},
    ],
    "judge_checks": [
        {"id": "sourced-facts", "desc": "..."},
        {"id": "honesty", "desc": "..."},
    ],
}


class TestHasMarker(unittest.TestCase):
    def test_any_match(self):
        self.assertTrue(re.has_marker("這是結論段", ["結論", "摘要"]))

    def test_no_match(self):
        self.assertFalse(re.has_marker("沒有關鍵字", ["結論", "摘要"]))


class TestEvaluateContent(unittest.TestCase):
    def test_all_auto_pass(self):
        content = "# 標題\n## 結論\n內容\n## 來源\n- a"
        ev = re.evaluate_content(content, RESEARCH_RUBRIC)
        self.assertTrue(ev["has_title"])
        self.assertEqual(ev["auto_pass_ratio"], 1.0)
        self.assertEqual([r["result"] for r in ev["auto_results"]], ["pass", "pass"])
        self.assertEqual(ev["judge_pending"], ["sourced-facts", "honesty"])

    def test_partial_auto(self):
        # 有結論（head pass），但無 structure 標記（來源/待驗證皆不出現）
        content = "# 標題\n## 結論\n內容主體沒有出處區塊"
        ev = re.evaluate_content(content, RESEARCH_RUBRIC)
        self.assertEqual(ev["auto_pass_ratio"], 0.5)

    def test_head_scope_excludes_deep_marker(self):
        # 結論 出現在第 200 行，超出 HEAD_LINES → conclusion-first 應 fail
        body = "\n".join(["填充"] * 200) + "\n## 結論"
        content = "# 標題\n" + body + "\n## 來源"
        ev = re.evaluate_content(content, RESEARCH_RUBRIC)
        results = {r["id"]: r["result"] for r in ev["auto_results"]}
        self.assertEqual(results["conclusion-first"], "fail")
        self.assertEqual(results["structure"], "pass")  # full scope 仍抓到

    def test_no_title(self):
        ev = re.evaluate_content("沒有井號開頭\n## 結論\n## 來源", RESEARCH_RUBRIC)
        self.assertFalse(ev["has_title"])


class TestEvaluateCase(unittest.TestCase):
    def _write(self, root: Path, rel: str, text: str) -> None:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def test_missing_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "evals" / "rubrics").mkdir(parents=True)
            res = re.evaluate_case(root, {"case_id": "c1", "skill": "research",
                                          "output_path": "nope.md"},
                                   root / "evals" / "rubrics")
            self.assertFalse(res["passed"])
            self.assertEqual(res["reason"], "output_missing")

    def test_too_short(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "out.md", "# 短")
            res = re.evaluate_case(root, {"case_id": "c1", "skill": "research",
                                          "output_path": "out.md"},
                                   root / "evals" / "rubrics")
            self.assertEqual(res["reason"], "output_too_short")

    def test_passing_case_with_real_rubric_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content = "# 標題\n## 結論\n" + ("內容 " * 100) + "\n## 來源\n- x"
            self._write(root, "outputs/good.md", content)
            res = re.evaluate_case(
                root,
                {"case_id": "c1", "skill": "research", "output_path": "outputs/good.md"},
                re.RUBRICS_DIR,  # 用 repo 內真實 rubric
            )
            self.assertTrue(res["passed"], res)


class TestRunRealRepo(unittest.TestCase):
    def test_run_against_repo_manifest_all_pass(self):
        scorecard = re.run()["scorecard"]
        self.assertGreaterEqual(scorecard["summary"]["cases_total"], 1)
        # 既有 regression golden 應全數通過（否則代表產出結構退化）
        self.assertEqual(
            scorecard["summary"]["cases_passed"], scorecard["summary"]["cases_total"],
            [c for c in scorecard["cases"] if not c["passed"]],
        )

    def test_dump_is_deterministic(self):
        sc = re.run()
        self.assertEqual(re.dump(sc), re.dump(sc))

    def test_main_returns_zero(self):
        self.assertEqual(re.main(["--no-write"]), 0)

    def test_all_five_rubrics_loadable(self):
        for skill in re.ALLOWED_SKILL:
            rub = re.load_rubric(re.RUBRICS_DIR, skill)
            self.assertEqual(rub["skill"], skill)
            self.assertTrue(rub["auto_checks"])


if __name__ == "__main__":
    unittest.main()
