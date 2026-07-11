#!/usr/bin/env python3
"""Unit tests for scripts/check_inflight.py."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_inflight as ci


def _card(task_id="20260101-001", status="pending", goal="", slug="2026-01-01_x", path="tasks/x.yaml"):
    return {"task_id": task_id, "status": status, "goal": goal, "slug": slug, "path": path}


class TestMatchTaskCards(unittest.TestCase):
    def test_goal_hit_chinese_substring(self):
        cards = [_card(goal="依評分系譜檢視改進進度並執行優化")]
        self.assertEqual(len(ci.match_task_cards(cards, ["評分"])), 1)

    def test_slug_hit_case_insensitive(self):
        cards = [_card(goal="（無關 goal）", slug="2026-07-11_Evaluation-Improvement")]
        self.assertEqual(len(ci.match_task_cards(cards, ["evaluation"])), 1)

    def test_no_hit(self):
        cards = [_card(goal="整理發票資料", slug="2026-05-01_invoice-cleanup")]
        self.assertEqual(ci.match_task_cards(cards, ["eval", "評測"]), [])

    def test_multi_keyword_or_semantics(self):
        cards = [_card(goal="eval harness 收斂"), _card(goal="評測框架整併")]
        self.assertEqual(len(ci.match_task_cards(cards, ["eval", "評測"])), 2)


class TestMatchBranches(unittest.TestCase):
    def test_space_normalized_to_dash(self):
        names = ["claude/eval-harness-consolidation-abc123"]
        self.assertEqual(len(ci.match_branches(names, ["eval harness"])), 1)

    def test_case_insensitive(self):
        names = ["claude/Project-Evaluation-Improvements-s0blnw"]
        self.assertEqual(len(ci.match_branches(names, ["evaluation"])), 1)

    def test_no_hit(self):
        names = ["main", "claude/frontend-phase0-xyz"]
        self.assertEqual(ci.match_branches(names, ["eval"]), [])


class TestMatchPrs(unittest.TestCase):
    def test_title_hit(self):
        prs = [{"number": 126, "title": "外部評估報告（≈6.8/10）+ P0 修復"}]
        hits = ci.match_prs(prs, ["評估"])
        self.assertEqual(hits, [{"number": 126, "title": "外部評估報告（≈6.8/10）+ P0 修復"}])

    def test_non_dict_items_skipped(self):
        self.assertEqual(ci.match_prs(["garbage", None], ["x"]), [])


class TestLoadTaskCards(unittest.TestCase):
    def test_skips_templates_and_bad_yaml(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "TASK_CARD_TEMPLATE.yaml").write_text("task_id: ''\n", encoding="utf-8")
            (d / "2026-07-01_good.yaml").write_text(
                "task_id: '20260701-001'\nstatus: pending\ngoal: 測試查重\n", encoding="utf-8")
            (d / "2026-07-02_bad.yaml").write_text("task_id: [unclosed\n", encoding="utf-8")
            cards = ci.load_task_cards(d)
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0]["task_id"], "20260701-001")
        self.assertEqual(cards[0]["slug"], "2026-07-01_good")


class TestRemoteDegradation(unittest.TestCase):
    def test_remote_failure_does_not_crash_main(self):
        import io
        from contextlib import redirect_stdout, redirect_stderr

        original = ci.fetch_remote_branches
        ci.fetch_remote_branches = lambda: (_ for _ in ()).throw(RuntimeError("no network"))
        try:
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                code = ci.main(["絕不會命中的關鍵字xyzzy"])
            self.assertEqual(code, 0)
            self.assertIn("remote unavailable", err.getvalue())
        finally:
            ci.fetch_remote_branches = original

    def test_no_remote_flag_skips_fetch(self):
        import io
        from contextlib import redirect_stdout

        original = ci.fetch_remote_branches
        ci.fetch_remote_branches = lambda: (_ for _ in ()).throw(AssertionError("should not be called"))
        try:
            out = io.StringIO()
            with redirect_stdout(out):
                code = ci.main(["絕不會命中的關鍵字xyzzy", "--no-remote"])
            self.assertEqual(code, 0)
        finally:
            ci.fetch_remote_branches = original


class TestMainExitCodes(unittest.TestCase):
    def test_hit_on_real_repo_returns_1(self):
        # 本卡自己（tasks/2026-07-11_evaluation-improvement-progress.yaml）應被「評分」命中。
        import io
        from contextlib import redirect_stdout

        out = io.StringIO()
        with redirect_stdout(out):
            code = ci.main(["評分", "--no-remote"])
        self.assertEqual(code, 1)
        self.assertIn("20260711-001", out.getvalue())

    def test_blank_keywords_error(self):
        import io
        from contextlib import redirect_stderr

        err = io.StringIO()
        with redirect_stderr(err):
            code = ci.main(["   ", "--no-remote"])
        self.assertEqual(code, 2)

    def test_bad_pr_json_error(self):
        import io
        from contextlib import redirect_stderr

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            f.write('{"message": "not a list"}')
            path = f.name
        try:
            err = io.StringIO()
            with redirect_stderr(err):
                code = ci.main(["x", "--no-remote", "--pr-json", path])
            self.assertEqual(code, 2)
        finally:
            Path(path).unlink()

    def test_pr_json_hit(self):
        import io
        import json as _json
        from contextlib import redirect_stdout

        prs = [{"number": 130, "title": "P0 hardening：外部報告驗證", "created_at": "2026-07-10T05:00:00Z"}]
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            _json.dump(prs, f, ensure_ascii=False)
            path = f.name
        try:
            out = io.StringIO()
            with redirect_stdout(out):
                code = ci.main(["hardening", "--no-remote", "--pr-json", path])
            self.assertEqual(code, 1)
            self.assertIn("#130", out.getvalue())
        finally:
            Path(path).unlink()


if __name__ == "__main__":
    unittest.main()
