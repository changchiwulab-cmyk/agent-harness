#!/usr/bin/env python3
"""Unit tests for scripts/session_recorder.py."""

from __future__ import annotations

import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import session_recorder as rec


class TestPureHelpers(unittest.TestCase):
    def test_target_of_bash(self):
        self.assertEqual(rec.target_of("Bash", {"command": "ls -la"}), "ls -la")

    def test_target_of_write(self):
        self.assertEqual(rec.target_of("Write", {"file_path": "a/b.md"}), "a/b.md")

    def test_target_of_search(self):
        self.assertEqual(rec.target_of("Grep", {"pattern": "foo"}), "foo")

    def test_target_truncated(self):
        long = "x" * 500
        self.assertEqual(len(rec.target_of("Bash", {"command": long})), 200)

    def test_outcome_ok_and_error(self):
        self.assertEqual(rec.outcome_of({"success": True}), "ok")
        self.assertEqual(rec.outcome_of({"success": False}), "error")
        self.assertEqual(rec.outcome_of({"error": "boom"}), "error")
        self.assertEqual(rec.outcome_of(None), "unknown")

    def test_build_record_shape(self):
        r = rec.build_record({
            "session_id": "s1",
            "tool_name": "Edit",
            "tool_input": {"file_path": "system/x"},
            "tool_response": {"success": True},
        })
        self.assertEqual(r["tool"], "Edit")
        self.assertEqual(r["target"], "system/x")
        self.assertEqual(r["outcome"], "ok")
        self.assertEqual(r["session_id"], "s1")
        self.assertIn("ts", r)

    def test_failure_event_records_error_outcome(self):
        r = rec.build_record({
            "session_id": "s1",
            "hook_event_name": "PostToolUseFailure",
            "tool_name": "Bash",
            "tool_input": {"command": "false"},
            "tool_response": {},
        })
        self.assertEqual(r["event"], "PostToolUseFailure")
        self.assertEqual(r["outcome"], "error")

    def test_default_event_is_posttooluse(self):
        r = rec.build_record({"tool_name": "Read", "tool_input": {"file_path": "x"},
                              "tool_response": {"success": True}})
        self.assertEqual(r["event"], "PostToolUse")
        self.assertEqual(r["outcome"], "ok")

    def test_session_file_sanitises_id(self):
        p = rec.session_file("../../etc/passwd")
        self.assertTrue(p.name.startswith("session-"))
        self.assertNotIn("/", p.name)


class TestMainRobustness(unittest.TestCase):
    def _run(self, raw: str) -> int:
        sys.stdin = io.StringIO(raw)
        try:
            with redirect_stdout(io.StringIO()):
                return rec.main()
        finally:
            sys.stdin = sys.__stdin__

    def test_empty_stdin_exits_zero(self):
        self.assertEqual(self._run(""), 0)

    def test_bad_json_exits_zero(self):
        self.assertEqual(self._run("not json {"), 0)

    def test_main_appends_line(self):
        tmp = Path(__file__).resolve().parent / ".tmp_session_test"
        tmp.mkdir(exist_ok=True)
        orig = rec.RUNS_DIR
        rec.RUNS_DIR = tmp
        try:
            code = self._run(json.dumps({
                "session_id": "unitsess", "tool_name": "Read",
                "tool_input": {"file_path": "x"}, "tool_response": {"success": True},
            }))
            self.assertEqual(code, 0)
            line = (tmp / "session-unitsess.jsonl").read_text(encoding="utf-8").strip()
            self.assertEqual(json.loads(line)["tool"], "Read")
        finally:
            for p in tmp.glob("*"):
                p.unlink()
            tmp.rmdir()
            rec.RUNS_DIR = orig


if __name__ == "__main__":
    unittest.main()
