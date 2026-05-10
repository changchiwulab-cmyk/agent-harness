#!/usr/bin/env python3
"""Unit tests for scripts/governance_metrics.py."""

from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path

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
    def test_ok_at_30_pct(self):
        result = gm.metric_m4({"aggregate_estimate_pct": 30, "reviewed_on": "2026-05-09"})
        self.assertEqual(result.status, "ok")

    def test_warn_at_45_pct(self):
        result = gm.metric_m4({"aggregate_estimate_pct": 45, "reviewed_on": "2026-05-09"})
        self.assertEqual(result.status, "warn")

    def test_alert_above_50_pct(self):
        result = gm.metric_m4({"aggregate_estimate_pct": 60, "reviewed_on": "2026-05-09"})
        self.assertEqual(result.status, "alert")

    def test_alert_when_input_missing(self):
        result = gm.metric_m4({})
        self.assertEqual(result.status, "alert")
        self.assertIn("error", result.details)


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


if __name__ == "__main__":
    unittest.main()
