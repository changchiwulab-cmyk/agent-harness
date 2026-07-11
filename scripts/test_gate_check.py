#!/usr/bin/env python3
"""Unit tests for scripts/gate_check.py."""

from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gate_check as gc


GOOD_CARD = {
    "task_id": "20260609-T01",
    "date": "2026-06-09",
    "status": "pending",
    "goal": "fixture card for gate_check tests",
    "definition_of_done": ["thing one", "thing two"],
    "expected_output": {"format": "md", "location": "outputs/drafts/", "filename": "out.md"},
    "risk_level": "low",
    "approval_needed": False,
    "allowed_tools": ["file_read", "file_write"],
    "skill_type": "ops",
    "max_tool_calls": 5,
}


def make_root(card: dict, *, output: bool = False, run_log: dict | None = None) -> Path:
    """Build a temp repo root with tasks/<card>, optional output + run log."""
    root = Path(tempfile.mkdtemp())
    (root / "tasks").mkdir()
    (root / "outputs" / "drafts").mkdir(parents=True)
    (root / "outputs" / "reports").mkdir(parents=True)
    card_path = root / "tasks" / f"{card['task_id']}.yaml"
    card_path.write_text(yaml.safe_dump(card, allow_unicode=True, sort_keys=False), encoding="utf-8")
    if output:
        out = card.get("expected_output", {})
        (root / out["location"].rstrip("/") / out["filename"]).write_text("# out\n", encoding="utf-8")
    if run_log is not None:
        (root / "logs" / "runs").mkdir(parents=True)
        (root / "logs" / "runs" / "RUN-test.yaml").write_text(
            yaml.safe_dump({"execution_log": run_log}, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
    return root, card_path


class TestRunLogRequired(unittest.TestCase):
    """缺 run log 的條件 fail-closed（20260710-003）：cutoff + 高風險 + 產出/結案。"""

    def high_risk_card(self, **overrides) -> dict:
        card = dict(GOOD_CARD)
        card.update(
            {
                "date": "2026-07-10",
                "status": "done",
                "risk_level": "high",
                "approval_needed": True,
            }
        )
        card.update(overrides)
        return card

    def test_high_risk_done_after_cutoff_missing_log_fails(self):
        card = self.high_risk_card()
        self.assertTrue(gc.run_log_required(card))
        result = gc.gate_rule(card, None)
        self.assertEqual(result["status"], gc.FAIL)
        self.assertIn("fail-closed", result["detail"])

    def test_before_cutoff_missing_log_skipped(self):
        # 不追溯歷史卡（APPROVAL_COVERAGE_CUTOFF 同款模式）。
        card = self.high_risk_card(date="2026-07-09")
        self.assertFalse(gc.run_log_required(card))
        self.assertEqual(gc.gate_rule(card, None)["status"], gc.SKIPPED)

    def test_low_risk_done_missing_log_skipped(self):
        card = self.high_risk_card(risk_level="low")
        self.assertEqual(gc.gate_rule(card, None)["status"], gc.SKIPPED)

    def test_high_risk_in_progress_missing_log_skipped(self):
        # 尚未進入產出/結案狀態 — 還沒到必須有帳的時點。
        card = self.high_risk_card(status="in_progress")
        self.assertEqual(gc.gate_rule(card, None)["status"], gc.SKIPPED)

    def test_critical_failed_after_cutoff_missing_log_fails(self):
        card = self.high_risk_card(risk_level="critical", status="failed")
        self.assertEqual(gc.gate_rule(card, None)["status"], gc.FAIL)

    def test_unparseable_date_skipped(self):
        # date 壞掉時不強制（schema gate 會另行抓 date 缺失）。
        card = self.high_risk_card(date="not-a-date")
        self.assertFalse(gc.run_log_required(card))

    def test_present_log_still_checked_normally(self):
        card = self.high_risk_card()
        result = gc.gate_rule(card, {"tools_used": [{"tool": "file_read"}]})
        self.assertEqual(result["status"], gc.PASS)


class TestGates(unittest.TestCase):
    def test_pending_good_card_passes(self):
        root, card_path = make_root(GOOD_CARD)
        report = gc.check_card(card_path, root)
        self.assertFalse(report.failed)
        self.assertEqual(report.results["schema_check"]["status"], gc.PASS)
        self.assertEqual(report.results["rule_check"]["status"], gc.SKIPPED)   # no log
        self.assertEqual(report.results["completion_check"]["status"], gc.SKIPPED)  # not produced
        self.assertEqual(report.results["risk_check"]["status"], gc.NA)

    def test_schema_fail_on_missing_dod(self):
        bad = {**GOOD_CARD, "definition_of_done": []}
        root, card_path = make_root(bad)
        report = gc.check_card(card_path, root)
        self.assertTrue(report.failed)
        self.assertEqual(report.results["schema_check"]["status"], gc.FAIL)
        self.assertIn("definition_of_done", report.results["schema_check"]["detail"])

    def test_high_risk_in_reports_fails_risk_gate(self):
        card = {
            **GOOD_CARD,
            "risk_level": "high",
            "expected_output": {"format": "md", "location": "outputs/reports/", "filename": "out.md"},
        }
        root, card_path = make_root(card)
        report = gc.check_card(card_path, root)
        self.assertTrue(report.failed)
        self.assertEqual(report.results["risk_check"]["status"], gc.FAIL)
        self.assertIn("drafts/", report.results["risk_check"]["detail"])

    def test_high_risk_in_drafts_passes_risk_gate(self):
        card = {**GOOD_CARD, "risk_level": "high"}
        root, card_path = make_root(card)
        report = gc.check_card(card_path, root)
        self.assertEqual(report.results["risk_check"]["status"], gc.PASS)

    def test_done_without_output_fails_completion(self):
        card = {**GOOD_CARD, "status": "done", "completion_time": "2026-06-09"}
        root, card_path = make_root(card, output=False)
        report = gc.check_card(card_path, root)
        self.assertTrue(report.failed)
        self.assertEqual(report.results["completion_check"]["status"], gc.FAIL)

    def test_done_with_output_passes_completion(self):
        card = {**GOOD_CARD, "status": "done", "completion_time": "2026-06-09"}
        root, card_path = make_root(card, output=True)
        report = gc.check_card(card_path, root)
        self.assertEqual(report.results["completion_check"]["status"], gc.PASS)

    def test_rule_gate_flags_tool_outside_whitelist(self):
        run_log = {
            "task_id": GOOD_CARD["task_id"],
            "status": "completed",
            "tools_used": [{"tool": "file_read", "call_count": 1}, {"tool": "web_search", "call_count": 2}],
        }
        root, card_path = make_root(GOOD_CARD, run_log=run_log)
        report = gc.check_card(card_path, root)
        self.assertTrue(report.failed)
        self.assertEqual(report.results["rule_check"]["status"], gc.FAIL)
        self.assertIn("web_search", report.results["rule_check"]["detail"])

    def test_rule_gate_passes_when_tools_subset(self):
        run_log = {
            "task_id": GOOD_CARD["task_id"],
            "status": "completed",
            "tools_used": [{"tool": "file_read", "call_count": 3}],
        }
        root, card_path = make_root(GOOD_CARD, run_log=run_log)
        report = gc.check_card(card_path, root)
        self.assertEqual(report.results["rule_check"]["status"], gc.PASS)

    def test_gate_results_block_matches_schema_keys(self):
        root, card_path = make_root(GOOD_CARD)
        report = gc.check_card(card_path, root)
        self.assertEqual(
            set(report.gate_results.keys()),
            {"schema_check", "rule_check", "completion_check", "risk_check"},
        )


class TestRiskGateSemantics(unittest.TestCase):
    """L4 語意（20260711-A01）：前綴精確、高風險空路徑 fail-closed、run log 落點照查，
    且 gate_check.gate_risk 與 verification_loop.check_risk 對同一矩陣判定一致。"""

    # (risk_level, 宣告 location, run log output_path, 預期 ok)
    MATRIX = [
        ("high", "", None, False),                                   # 空宣告 fail-closed
        ("critical", "", None, False),
        ("high", "outputs/drafts/", None, True),
        ("high", "outputs/drafts/sub/", None, True),
        ("high", "outputs/drafts-public/", None, False),             # 前綴相似路徑
        ("high", "foo/outputs/drafts/", None, False),                # 子字串誤判案例
        ("high", "outputs/reports/", None, False),
        ("high", "outputs/drafts/", "outputs/reports/x.md", False),  # 實際落點違規
        ("high", "outputs/drafts/", "outputs/drafts/x.md", True),
        ("low", "outputs/reports/", None, True),                     # 低風險不受限
        ("high", "outputs/drafts/../reports/", None, False),         # traversal 出界（Codex P1 on #133）
        ("high", "outputs/drafts/sub/../x/", None, True),            # 內部 .. 不出界
        ("high", "outputs/drafts/", "outputs/drafts/../reports/x.md", False),  # run log traversal
    ]

    @staticmethod
    def _card(risk: str, location: str) -> dict:
        return {
            "risk_level": risk,
            "expected_output": {"format": "md", "location": location, "filename": "x.md"},
        }

    def test_matrix_and_parity_with_verification_loop(self):
        import verification_loop as vl

        for risk, loc, out_path, expect_ok in self.MATRIX:
            card = self._card(risk, loc)
            run_log = {"output_path": out_path} if out_path else None
            with self.subTest(risk=risk, loc=loc, out_path=out_path):
                gate_ok = gc.gate_risk(card, run_log)["status"] != gc.FAIL
                loop_ok, _ = vl.check_risk(card, run_log)
                self.assertEqual(gate_ok, expect_ok)
                self.assertEqual(loop_ok, expect_ok)

    def test_empty_location_high_risk_fails_closed(self):
        result = gc.gate_risk(self._card("high", ""), None)
        self.assertEqual(result["status"], gc.FAIL)
        self.assertIn("no expected_output.location", result["detail"])


class TestCLI(unittest.TestCase):
    def _run(self, argv: list[str]) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = gc.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_card_path_exit_0_for_passing(self):
        root, card_path = make_root(GOOD_CARD)
        code, out, _ = self._run(["--card", str(card_path), "--root", str(root)])
        self.assertEqual(code, 0)
        self.assertIn("PASS", out)

    def test_exit_1_for_failing(self):
        bad = {**GOOD_CARD, "definition_of_done": []}
        root, card_path = make_root(bad)
        code, out, _ = self._run(["--card", str(card_path), "--root", str(root)])
        self.assertEqual(code, 1)

    def test_exit_2_for_unknown_task_id(self):
        root, _ = make_root(GOOD_CARD)
        code, _, err = self._run(["20991231-999", "--root", str(root)])
        self.assertEqual(code, 2)
        self.assertIn("no Task Card", err)

    def test_lookup_by_task_id(self):
        root, _ = make_root(GOOD_CARD)
        code, out, _ = self._run([GOOD_CARD["task_id"], "--root", str(root), "--json"])
        self.assertEqual(code, 0)
        self.assertIn("gate_results", out)


if __name__ == "__main__":
    unittest.main()
