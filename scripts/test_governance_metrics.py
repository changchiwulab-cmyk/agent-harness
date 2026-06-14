#!/usr/bin/env python3
"""Unit tests for scripts/governance_metrics.py."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import governance_metrics as gm


class TestMetricM1(unittest.TestCase):
    def test_ok_when_each_recent_month_at_least_3(self):
        cards = (
            [{"year_month": "2026-03", "status": "done", "task_id": f"20260301-{i:03}"} for i in range(4)]
            + [{"year_month": "2026-04", "status": "done", "task_id": f"20260401-{i:03}"} for i in range(5)]
            + [{"year_month": "2026-05", "status": "done", "task_id": f"20260501-{i:03}"} for i in range(3)]
        )
        result = gm.metric_m1(cards, date(2026, 5, 9))
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.details["below_threshold_months"], [])

    def test_warn_when_one_month_below(self):
        cards = (
            [{"year_month": "2026-03", "status": "done", "task_id": f"20260301-{i:03}"} for i in range(4)]
            + [{"year_month": "2026-04", "status": "done", "task_id": f"20260401-{i:03}"} for i in range(2)]  # < 3
            + [{"year_month": "2026-05", "status": "done", "task_id": f"20260501-{i:03}"} for i in range(5)]
        )
        result = gm.metric_m1(cards, date(2026, 5, 9))
        self.assertEqual(result.status, "warn")
        self.assertIn("2026-04", result.details["below_threshold_months"])

    def test_alert_when_two_consecutive_months_below(self):
        cards = (
            [{"year_month": "2026-03", "status": "done", "task_id": f"20260301-{i:03}"} for i in range(4)]
            + [{"year_month": "2026-04", "status": "done", "task_id": f"20260401-{i:03}"} for i in range(2)]
            + [{"year_month": "2026-05", "status": "done", "task_id": f"20260501-{i:03}"} for i in range(1)]
        )
        result = gm.metric_m1(cards, date(2026, 5, 9))
        self.assertEqual(result.status, "alert")

    def test_zero_count_current_month_warns(self):
        # Codex P2: today=2026-07; July has zero new cards but earlier months
        # exist. Zero must be evaluated against the < 3 threshold.
        cards = (
            [{"year_month": "2026-05", "status": "done", "task_id": f"20260501-{i:03}"} for i in range(4)]
            + [{"year_month": "2026-06", "status": "done", "task_id": f"20260601-{i:03}"} for i in range(5)]
        )
        result = gm.metric_m1(cards, date(2026, 7, 15))
        self.assertEqual(result.status, "warn")
        self.assertIn("2026-07", result.details["below_threshold_months"])
        self.assertEqual(dict(result.details["recent"])["2026-07"], 0)

    def test_zero_count_two_consecutive_months_alerts(self):
        # Codex P2: project went silent for the last 2 calendar months.
        cards = [{"year_month": "2026-05", "status": "done", "task_id": f"20260501-{i:03}"} for i in range(4)]
        result = gm.metric_m1(cards, date(2026, 7, 15))
        self.assertEqual(result.status, "alert")

    def test_pre_project_months_excluded_from_window(self):
        # Boot-phase carve-out: a brand-new project shouldn't alert just
        # because months before its first card are zero.
        cards = [{"year_month": "2026-05", "status": "done", "task_id": f"20260501-{i:03}"} for i in range(5)]
        result = gm.metric_m1(cards, date(2026, 5, 9))
        # Window [2026-03, 2026-04, 2026-05] but only 2026-05 is in scope.
        self.assertEqual(result.status, "ok")
        recent_months = {m for m, _ in result.details["recent"]}
        self.assertEqual(recent_months, {"2026-05"})


class TestLoadTaskCardsRaisesOnInvalidYaml(unittest.TestCase):
    """Codex P1: malformed YAML must surface as collection error, not be skipped."""

    def test_main_returns_exit_2_on_malformed_task_yaml(self):
        import io
        import tempfile
        from contextlib import redirect_stdout, redirect_stderr

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "tasks").mkdir()
            (tmp_path / "logs").mkdir()
            (tmp_path / "outputs" / "drafts").mkdir(parents=True)
            (tmp_path / "outputs" / "reports").mkdir(parents=True)
            (tmp_path / "system").mkdir()
            (tmp_path / "logs" / "AUDIT_LOG.md").write_text("", encoding="utf-8")
            (tmp_path / "system" / "NATIVE_OVERLAP.yaml").write_text(
                "aggregate_estimate_pct: 30\nreviewed_on: '2026-05-09'\n", encoding="utf-8"
            )
            # Malformed YAML: unbalanced braces.
            (tmp_path / "tasks" / "broken.yaml").write_text(
                "task_id: '20260101-X01'\nstatus: {oops\n", encoding="utf-8"
            )

            original = {
                "ROOT": gm.ROOT,
                "TASKS_DIR": gm.TASKS_DIR,
                "AUDIT_LOG": gm.AUDIT_LOG,
                "DRAFTS_DIR": gm.DRAFTS_DIR,
                "REPORTS_DIR": gm.REPORTS_DIR,
                "NATIVE_OVERLAP": gm.NATIVE_OVERLAP,
            }
            try:
                gm.ROOT = tmp_path
                gm.TASKS_DIR = tmp_path / "tasks"
                gm.AUDIT_LOG = tmp_path / "logs" / "AUDIT_LOG.md"
                gm.DRAFTS_DIR = tmp_path / "outputs" / "drafts"
                gm.REPORTS_DIR = tmp_path / "outputs" / "reports"
                gm.NATIVE_OVERLAP = tmp_path / "system" / "NATIVE_OVERLAP.yaml"
                err = io.StringIO()
                out = io.StringIO()
                with redirect_stdout(out), redirect_stderr(err):
                    code = gm.main(["--today", "2026-05-09"])
                self.assertEqual(code, 2)
                self.assertIn("broken.yaml", err.getvalue())
            finally:
                for k, v in original.items():
                    setattr(gm, k, v)


class TestMetricM2(unittest.TestCase):
    def test_ok_when_drafts_far_exceed_reports(self):
        result = gm.metric_m2(drafts_count=17, reports_count=2)
        self.assertEqual(result.status, "ok")

    def test_alert_when_drafts_less_than_reports(self):
        result = gm.metric_m2(drafts_count=2, reports_count=5)
        self.assertEqual(result.status, "alert")

    def test_warn_when_ratio_just_above_one(self):
        result = gm.metric_m2(drafts_count=11, reports_count=10)
        self.assertEqual(result.status, "warn")

    def test_ok_when_no_reports_yet(self):
        result = gm.metric_m2(drafts_count=5, reports_count=0)
        self.assertEqual(result.status, "ok")


class TestMetricM3(unittest.TestCase):
    def test_full_coverage_is_ok(self):
        cards = [
            {"task_id": "20260501-001", "status": "done"},
            {"task_id": "20260501-002", "status": "review"},
        ]
        audit = {"20260501-001", "20260501-002"}
        result = gm.metric_m3(cards, audit)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.details["coverage_pct"], 100.0)

    def test_alert_below_80(self):
        cards = [{"task_id": f"20260501-{i:03}", "status": "done"} for i in range(10)]
        audit = {f"20260501-{i:03}" for i in range(7)}  # 70%
        result = gm.metric_m3(cards, audit)
        self.assertEqual(result.status, "alert")
        self.assertEqual(result.details["coverage_pct"], 70.0)

    def test_pending_cards_excluded_from_denominator(self):
        cards = [
            {"task_id": "20260501-001", "status": "done"},
            {"task_id": "20260501-002", "status": "pending"},  # excluded
            {"task_id": "20260501-003", "status": "in_progress"},  # excluded
        ]
        audit = {"20260501-001"}
        result = gm.metric_m3(cards, audit)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.details["completed_total"], 1)
        self.assertEqual(result.details["coverage_pct"], 100.0)


class TestMetricM4(unittest.TestCase):
    # 6 days after reviewed_on 2026-05-09 → fresh, so the value axis governs.
    FRESH = date(2026, 5, 15)

    def test_ok_at_30_pct_fresh(self):
        result = gm.metric_m4({"aggregate_estimate_pct": 30, "reviewed_on": "2026-05-09"}, self.FRESH)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.details["days_since_review"], 6)
        self.assertFalse(result.details["revisit_overdue"])
        self.assertIsNone(result.details["recommended_action"])

    def test_warn_at_45_pct_fresh(self):
        result = gm.metric_m4({"aggregate_estimate_pct": 45, "reviewed_on": "2026-05-09"}, self.FRESH)
        self.assertEqual(result.status, "warn")

    def test_alert_above_50_pct(self):
        result = gm.metric_m4({"aggregate_estimate_pct": 60, "reviewed_on": "2026-05-09"}, self.FRESH)
        self.assertEqual(result.status, "alert")
        self.assertIn("v3-readiness", result.details["recommended_action"])

    def test_alert_when_input_missing(self):
        result = gm.metric_m4({}, self.FRESH)
        self.assertEqual(result.status, "alert")
        self.assertIn("error", result.details)

    # --- R9: 季度 revisit 逾期偵測 (freshness axis) ---

    def test_ok_when_reviewed_today(self):
        result = gm.metric_m4({"aggregate_estimate_pct": 30, "reviewed_on": "2026-06-14"}, date(2026, 6, 14))
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.details["days_since_review"], 0)

    def test_warn_when_review_due_soon(self):
        # 30% (value ok) but 80 days since review → freshness warn, not yet overdue.
        result = gm.metric_m4({"aggregate_estimate_pct": 30, "reviewed_on": "2026-05-09"}, date(2026, 7, 28))
        self.assertEqual(result.details["days_since_review"], 80)
        self.assertEqual(result.status, "warn")
        self.assertFalse(result.details["revisit_overdue"])

    def test_alert_when_review_overdue(self):
        # 30% (value ok) but > 90 days since review → freshness alert + R10 pointer.
        result = gm.metric_m4({"aggregate_estimate_pct": 30, "reviewed_on": "2026-05-09"}, date(2026, 9, 1))
        self.assertGreater(result.details["days_since_review"], 90)
        self.assertEqual(result.status, "alert")
        self.assertTrue(result.details["revisit_overdue"])
        self.assertIn("v3-readiness", result.details["recommended_action"])

    def test_unparseable_reviewed_on_no_freshness_escalation(self):
        # reviewed_on unparseable → days_since None, no freshness alert; value axis governs.
        result = gm.metric_m4({"aggregate_estimate_pct": 30, "reviewed_on": "(unknown)"}, self.FRESH)
        self.assertIsNone(result.details["days_since_review"])
        self.assertEqual(result.status, "ok")


class TestDecisionRevisitMerge(unittest.TestCase):
    """R9: collect_decision_revisit merges the R4 tracker (best-effort, no crash)."""

    def test_parses_due_decisions(self):
        fake = json.dumps({
            "summary": "DUE=1 OK=5 MANUAL=1",
            "metrics": {"overlap_pct": 30},
            "decisions": [
                {"decision_id": "D001", "verdict": "DUE", "detail": "進行中任務 3 / 門檻 2"},
                {"decision_id": "D006", "verdict": "OK", "detail": "logs/runs 現有 2 / 門檻 5"},
            ],
        })
        completed = subprocess.CompletedProcess(args=[], returncode=0, stdout=fake, stderr="")
        with mock.patch("governance_metrics.subprocess.run", return_value=completed):
            out = gm.collect_decision_revisit()
        self.assertTrue(out["available"])
        self.assertEqual(out["summary"], "DUE=1 OK=5 MANUAL=1")
        self.assertEqual([d["decision_id"] for d in out["due"]], ["D001"])

    def test_degrades_when_ruby_missing(self):
        with mock.patch("governance_metrics.subprocess.run", side_effect=FileNotFoundError("ruby")):
            out = gm.collect_decision_revisit()
        self.assertFalse(out["available"])
        self.assertIn("reason", out)

    def test_degrades_on_nonzero_exit(self):
        completed = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="boom")
        with mock.patch("governance_metrics.subprocess.run", return_value=completed):
            out = gm.collect_decision_revisit()
        self.assertFalse(out["available"])

    def test_degrades_on_bad_json(self):
        completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="not json", stderr="")
        with mock.patch("governance_metrics.subprocess.run", return_value=completed):
            out = gm.collect_decision_revisit()
        self.assertFalse(out["available"])

    def test_render_quarterly_handles_unavailable(self):
        m4 = gm.metric_m4({"aggregate_estimate_pct": 30, "reviewed_on": "2026-05-09"}, date(2026, 5, 15))
        md = gm.render_quarterly_revisit_markdown(m4, {"available": False, "reason": "no ruby"})
        self.assertIn("季度治理重評", md)
        self.assertIn("無法取得", md)

    def test_render_quarterly_shows_overdue_and_due(self):
        m4 = gm.metric_m4({"aggregate_estimate_pct": 60, "reviewed_on": "2026-01-01"}, date(2026, 6, 14))
        revisit = {
            "available": True,
            "summary": "DUE=1 OK=5 MANUAL=1",
            "due": [{"decision_id": "D003", "detail": "原生重疊 60% / 門檻 50%"}],
        }
        md = gm.render_quarterly_revisit_markdown(m4, revisit)
        self.assertIn("v3-readiness", md)
        self.assertIn("DUE D003", md)
        self.assertIn("逾期", md)


class TestLoadAuditTaskIds(unittest.TestCase):
    """Regression: load_audit_task_ids must accept any YAML quoting style.

    The original implementation regexed `^- task_id: "..."` only, so single-
    quoted or unquoted entries (which check_audit_format.py accepts) would be
    silently dropped from M3 coverage.
    """

    def _run_against(self, audit_text: str, tmp_path: Path) -> set[str]:
        original = gm.AUDIT_LOG
        try:
            audit_file = tmp_path / "AUDIT_LOG.md"
            audit_file.write_text(audit_text, encoding="utf-8")
            gm.AUDIT_LOG = audit_file
            return gm.load_audit_task_ids()
        finally:
            gm.AUDIT_LOG = original

    def test_picks_up_single_quoted_and_unquoted_ids(self):
        import tempfile
        audit = (
            "# Audit Log\n"
            "```yaml\n"
            "- task_id: \"20260501-001\"\n"
            "  date: \"2026-05-01\"\n"
            "  status: done\n"
            "```\n"
            "```yaml\n"
            "- task_id: '20260501-002'\n"
            "  date: '2026-05-01'\n"
            "  status: done\n"
            "```\n"
            "```yaml\n"
            "- task_id: 20260501-003\n"
            "  date: 2026-05-01\n"
            "  status: done\n"
            "```\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            ids = self._run_against(audit, Path(tmp))
        self.assertEqual(ids, {"20260501-001", "20260501-002", "20260501-003"})

    def test_skips_empty_template_entry(self):
        import tempfile
        audit = (
            "# Audit Log\n"
            "```yaml\n"
            "- task_id: \"\"\n"
            "  date: \"\"\n"
            "  status: \"\"\n"
            "```\n"
            "```yaml\n"
            "- task_id: \"20260501-001\"\n"
            "  date: \"2026-05-01\"\n"
            "  status: done\n"
            "```\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            ids = self._run_against(audit, Path(tmp))
        self.assertEqual(ids, {"20260501-001"})


class TestMainExitCode(unittest.TestCase):
    def test_main_runs_against_real_repo(self):
        # Smoke test: should not crash on the actual repo layout.
        import io
        from contextlib import redirect_stdout

        out = io.StringIO()
        with redirect_stdout(out):
            code = gm.main(["--today", "2026-05-09", "--json"])
        self.assertIn(code, (0, 1))  # 2 = collection error; we don't expect that
        # JSON parses
        import json
        parsed = json.loads(out.getvalue())
        self.assertEqual(len(parsed), 4)
        ids = {m["id"] for m in parsed}
        self.assertEqual(ids, {"M1", "M2", "M3", "M4"})


class TestObservability(unittest.TestCase):
    """R7: workflow / business / failure observability layers."""

    def test_parse_token_estimate(self):
        self.assertEqual(gm.parse_token_estimate("~16K"), 16000)
        self.assertEqual(gm.parse_token_estimate("~120K（含 3 子代理）"), 120000)
        self.assertEqual(gm.parse_token_estimate("1500"), 1500)
        self.assertIsNone(gm.parse_token_estimate(""))
        self.assertIsNone(gm.parse_token_estimate(None))

    def test_workflow_tally(self):
        runs = [
            {"status": "completed", "gate_results": {"schema_check": "pass", "rule_check": "pass"}, "checkpoints": [1, 2]},
            {"status": "failed", "gate_results": {"schema_check": "fail", "rule_check": "not_run"}, "checkpoints": [1]},
        ]
        wf = gm.observability_workflow(runs)
        self.assertEqual(wf["runs_total"], 2)
        self.assertEqual(wf["status_distribution"], {"completed": 1, "failed": 1})
        self.assertEqual(wf["gate_results"]["schema_check"], {"pass": 1, "fail": 1})
        self.assertEqual(wf["avg_checkpoints"], 1.5)

    def test_business_per_skill(self):
        audit = [
            {"task_id": "a", "skill_type": "ops", "estimated_tokens": "~10K",
             "tools_called": [{"tool_name": "file_read", "call_count": 3}]},
            {"task_id": "b", "skill_type": "ops", "estimated_tokens": "~20K",
             "tools_called": [{"tool_name": "file_read", "call_count": 5}]},
            {"task_id": "c", "skill_type": "analysis", "estimated_tokens": "~16K"},  # no tools_called -> None
        ]
        biz = gm.observability_business(audit)
        self.assertEqual(biz["ops"]["count"], 2)
        self.assertEqual(biz["ops"]["avg_tokens"], 15000)
        self.assertEqual(biz["ops"]["avg_tool_calls"], 4.0)
        self.assertEqual(biz["analysis"]["count"], 1)
        self.assertEqual(biz["analysis"]["avg_tokens"], 16000)
        self.assertIsNone(biz["analysis"]["avg_tool_calls"])

    def test_failures_distribution(self):
        fa = gm.observability_failures(["tool_failure", "schema_failure", "schema_failure"])
        self.assertEqual(fa["errors_total"], 3)
        self.assertEqual(fa["by_type"], {"tool_failure": 1, "schema_failure": 2})

    def test_main_observability_flag_real_repo(self):
        import io
        import json as _json
        from contextlib import redirect_stdout

        out = io.StringIO()
        with redirect_stdout(out):
            code = gm.main(["--observability", "--today", "2026-05-29"])
        self.assertEqual(code, 0)
        data = _json.loads(out.getvalue())
        self.assertEqual(set(data.keys()), {"workflow", "business", "failures"})

    def test_existing_json_still_four_metrics(self):
        """Guard: --json output must remain M1–M4 only (no regression)."""
        import io
        import json as _json
        from contextlib import redirect_stdout

        out = io.StringIO()
        with redirect_stdout(out):
            gm.main(["--json", "--today", "2026-05-29"])
        data = _json.loads(out.getvalue())
        self.assertEqual({m["id"] for m in data}, {"M1", "M2", "M3", "M4"})


if __name__ == "__main__":
    unittest.main()
