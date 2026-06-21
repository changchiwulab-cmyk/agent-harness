#!/usr/bin/env python3
"""Unit tests for scripts/failure_tracker.py (R12)."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import failure_tracker as ft

NOW = "2026-06-20T10:00:00"


def run_main(argv: list[str]) -> tuple[int, dict, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = ft.main(argv)
    text = out.getvalue().strip()
    parsed = json.loads(text) if text.startswith("{") else {}
    return code, parsed, err.getvalue()


class TestTransitions(unittest.TestCase):
    def test_record_failure_increments(self):
        st = ft.empty_state()
        ft.record_failure(st, "T1", "schema_failure", "boom", ft.datetime.fromisoformat(NOW))
        self.assertEqual(st["consecutive_failures"], 1)
        self.assertEqual(st["last_task_id"], "T1")

    def test_success_resets(self):
        st = ft.empty_state()
        ft.record_failure(st, "T1", "unknown", "x", ft.datetime.fromisoformat(NOW))
        ft.record_failure(st, "T1", "unknown", "y", ft.datetime.fromisoformat(NOW))
        ft.record_success(st, "T1")
        self.assertEqual(st["consecutive_failures"], 0)
        self.assertEqual(st["history"], [])

    def test_tripped_at_threshold(self):
        st = ft.empty_state()
        for _ in range(3):
            ft.record_failure(st, "T1", "unknown", "x", ft.datetime.fromisoformat(NOW))
        self.assertTrue(ft.tripped(st))
        self.assertFalse(ft.tripped({"consecutive_failures": 2}))


class TestCli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state = str(Path(self.tmp.name) / "state.json")
        self.errors = str(Path(self.tmp.name) / "errors")

    def tearDown(self):
        self.tmp.cleanup()

    def _fail(self):
        return run_main([
            "record-failure", "--task-id", "T9", "--summary", "boom",
            "--error-type", "schema_failure",
            "--state", self.state, "--errors-dir", self.errors, "--now", NOW, "--json",
        ])

    def test_three_failures_trip_and_exit_1(self):
        c1, p1, _ = self._fail()
        c2, p2, _ = self._fail()
        self.assertEqual((c1, c2), (0, 0))
        self.assertFalse(p2["tripped"])
        c3, p3, err = self._fail()
        self.assertEqual(c3, 1)
        self.assertTrue(p3["tripped"])
        # circuit breaker wrote a durable error log
        self.assertIn("error_log", p3)
        self.assertTrue((Path(self.tmp.name) / Path(p3["error_log"]).name).exists()
                        or Path(p3["error_log"]).exists())

    def test_check_reports_tripped_state(self):
        for _ in range(3):
            self._fail()
        code, payload, _ = run_main(["check", "--state", self.state, "--json"])
        self.assertEqual(code, 1)
        self.assertTrue(payload["tripped"])

    def test_success_resets_after_failures(self):
        self._fail()
        self._fail()
        run_main(["record-success", "--task-id", "T9", "--state", self.state, "--json"])
        code, payload, _ = run_main(["check", "--state", self.state, "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(payload["consecutive_failures"], 0)

    def test_reset(self):
        self._fail()
        code, payload, _ = run_main(["reset", "--state", self.state, "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(payload["consecutive_failures"], 0)

    def test_circuit_breaker_error_log_has_template_fields(self):
        for _ in range(3):
            self._fail()
        produced = list(Path(self.errors).glob("*_circuit-breaker.md"))
        self.assertEqual(len(produced), 1)
        text = produced[0].read_text(encoding="utf-8")
        for field in ("error_id:", "task_id:", "error_type:", "failure_count:",
                      "resolution:", "user_notified:"):
            self.assertIn(field, text)


if __name__ == "__main__":
    unittest.main()
