#!/usr/bin/env python3
"""Unit tests for scripts/failure_counter.py."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import failure_counter as fc


class TestCounter(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        (self.root / "logs").mkdir()

    def test_record_increments(self):
        self.assertEqual(fc.record("T1", self.root), 1)
        self.assertEqual(fc.record("T1", self.root), 2)
        self.assertEqual(fc.check("T1", self.root), 2)

    def test_threshold_trips(self):
        for _ in range(fc.THRESHOLD):
            fc.record("T1", self.root)
        self.assertIn("T1", fc.tripped(self.root))

    def test_below_threshold_not_tripped(self):
        fc.record("T1", self.root)
        self.assertEqual(fc.tripped(self.root), [])

    def test_reset_clears(self):
        for _ in range(fc.THRESHOLD):
            fc.record("T1", self.root)
        fc.reset("T1", self.root)
        self.assertEqual(fc.check("T1", self.root), 0)
        self.assertEqual(fc.tripped(self.root), [])

    def test_success_clears_so_count_is_consecutive(self):
        # codex P2: a success between failures must reset the count, so this is
        # *consecutive* failures, not cumulative.
        fc.record("T1", self.root)
        fc.record("T1", self.root)
        fc.reset("T1", self.root)          # success path (--success delegates to reset)
        self.assertEqual(fc.record("T1", self.root), 1)
        self.assertEqual(fc.tripped(self.root), [])

    def test_state_file_is_gitignored_location(self):
        fc.record("T1", self.root)
        self.assertTrue((self.root / "logs" / ".failure_state.json").exists())


class TestHookDecision(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        (self.root / "logs").mkdir()

    def test_allow_when_not_tripped(self):
        decision, _ = fc.hook_decision({"tool_name": "Bash", "tool_input": {"command": "ls"}}, self.root)
        self.assertEqual(decision, "allow")

    def test_block_when_tripped(self):
        for _ in range(fc.THRESHOLD):
            fc.record("T1", self.root)
        decision, reason = fc.hook_decision(
            {"tool_name": "Bash", "tool_input": {"command": "echo hi"}}, self.root
        )
        self.assertEqual(decision, "block")
        self.assertIn("T1", reason)

    def test_reset_command_allowed_even_when_tripped(self):
        for _ in range(fc.THRESHOLD):
            fc.record("T1", self.root)
        decision, _ = fc.hook_decision(
            {"tool_name": "Bash", "tool_input": {"command": "python3 scripts/failure_counter.py --reset T1"}},
            self.root,
        )
        self.assertEqual(decision, "allow")


class TestPostHook(unittest.TestCase):
    """--post-hook：PostToolUseFailure 自動 +1、PostToolUse 自動歸零（20260716-P12）。"""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        (self.root / "logs").mkdir()
        self.state_file = self.root / "logs" / ".failure_state.json"

    def _bind_active(self, task_id: str = "T1"):
        (self.root / "state").mkdir(exist_ok=True)
        (self.root / "state" / "active_task.yaml").write_text(
            f'task_id: "{task_id}"\nstatus: "active"\nactivated_at: "2026-07-16"\nnote: ""\n',
            encoding="utf-8",
        )

    def _post(self, raw: str) -> tuple[int, str]:
        err = io.StringIO()
        sys.stdin = io.StringIO(raw)
        try:
            with redirect_stdout(io.StringIO()), redirect_stderr(err):
                code = fc.run_post_hook_guarded(self.root)
        finally:
            sys.stdin = sys.__stdin__
        return code, err.getvalue()

    def _failure_payload(self, **extra) -> str:
        payload = {
            "hook_event_name": "PostToolUseFailure",
            "tool_name": "Bash",
            "tool_input": {"command": "npm test"},
            "error": "Command exited with code 1",
            "is_interrupt": False,
        }
        payload.update(extra)
        return json.dumps(payload)

    def _success_payload(self) -> str:
        return json.dumps(
            {
                "hook_event_name": "PostToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "npm test"},
                "tool_response": "ok",
            }
        )

    def test_failure_event_records(self):
        self._bind_active()
        code, _ = self._post(self._failure_payload())
        self.assertEqual(code, 0)
        self.assertEqual(fc.check("T1", self.root), 1)

    def test_third_failure_trips_with_exit_2_warning(self):
        self._bind_active()
        self._post(self._failure_payload())
        self._post(self._failure_payload())
        code, err = self._post(self._failure_payload())
        self.assertEqual(code, 2)  # non-blocking：stderr 餵給 Claude，攔阻仍在 PreToolUse
        self.assertIn("3/3", err)
        self.assertIn("T1", fc.tripped(self.root))

    def test_success_event_clears_count(self):
        self._bind_active()
        self._post(self._failure_payload())
        self._post(self._failure_payload())
        code, _ = self._post(self._success_payload())
        self.assertEqual(code, 0)
        self.assertEqual(fc.check("T1", self.root), 0)
        # 連續語意：歸零後再失敗只算 1
        self._post(self._failure_payload())
        self.assertEqual(fc.check("T1", self.root), 1)
        self.assertEqual(fc.tripped(self.root), [])

    def test_success_event_skips_write_when_count_zero(self):
        self._bind_active()
        code, _ = self._post(self._success_payload())
        self.assertEqual(code, 0)
        self.assertFalse(self.state_file.exists())  # 零計數不寫 state，避免每次成功都 churn

    def test_interrupt_not_recorded(self):
        self._bind_active()
        code, _ = self._post(self._failure_payload(is_interrupt=True))
        self.assertEqual(code, 0)
        self.assertEqual(fc.check("T1", self.root), 0)

    def test_idle_noop_both_directions(self):
        # 無 state 檔
        code, _ = self._post(self._failure_payload())
        self.assertEqual(code, 0)
        self.assertFalse(self.state_file.exists())
        # 明確 idle
        (self.root / "state").mkdir(exist_ok=True)
        (self.root / "state" / "active_task.yaml").write_text(
            'task_id: ""\nstatus: "idle"\nactivated_at: ""\nnote: ""\n', encoding="utf-8"
        )
        code, _ = self._post(self._failure_payload())
        self.assertEqual(code, 0)
        code, _ = self._post(self._success_payload())
        self.assertEqual(code, 0)
        self.assertFalse(self.state_file.exists())

    def test_unknown_event_fail_open(self):
        self._bind_active()
        code, err = self._post(json.dumps({"hook_event_name": "PreToolUse", "tool_name": "Bash"}))
        self.assertEqual(code, 0)
        self.assertIn("fail-open", err)
        self.assertFalse(self.state_file.exists())

    def test_empty_stdin_fail_open(self):
        self._bind_active()
        code, err = self._post("")
        self.assertEqual(code, 0)
        self.assertIn("fail-open", err)
        self.assertFalse(self.state_file.exists())

    def test_bad_json_fail_open(self):
        self._bind_active()
        code, err = self._post("{not json")
        self.assertEqual(code, 0)
        self.assertIn("fail-open", err)
        self.assertFalse(self.state_file.exists())

    def test_non_object_payload_fail_open(self):
        self._bind_active()
        code, err = self._post("[1, 2]")
        self.assertEqual(code, 0)
        self.assertIn("fail-open", err)
        self.assertFalse(self.state_file.exists())

    def test_internal_error_fail_open(self):
        from unittest import mock

        with mock.patch.object(fc, "run_post_hook", side_effect=RuntimeError("boom")):
            err = io.StringIO()
            with redirect_stderr(err):
                code = fc.run_post_hook_guarded(self.root)
        self.assertEqual(code, 0)
        self.assertIn("fail-open", err.getvalue())

    def test_cli_dispatch(self):
        # 空 stdin 走 fail-open，證明 --post-hook 佈線到 run_post_hook_guarded 且不觸真實 state
        sys.stdin = io.StringIO("")
        try:
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = fc.main(["--post-hook"])
        finally:
            sys.stdin = sys.__stdin__
        self.assertEqual(code, 0)


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()) / "logs" / ".failure_state.json"
        self.tmp.parent.mkdir(parents=True)
        self._orig = fc.STATE_PATH
        fc.STATE_PATH = self.tmp

    def tearDown(self):
        fc.STATE_PATH = self._orig

    def _run(self, argv: list[str]) -> tuple[int, str]:
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            code = fc.main(argv)
        return code, out.getvalue()

    def test_record_then_reset(self):
        code, out = self._run(["--record", "T1"])
        self.assertEqual(code, 0)
        self.assertIn("1/3", out)
        code, _ = self._run(["--reset", "T1"])
        self.assertEqual(code, 0)

    def test_success_cli_clears_count(self):
        self._run(["--record", "T1"])
        self._run(["--record", "T1"])
        code, out = self._run(["--success", "T1"])
        self.assertEqual(code, 0)
        self.assertIn("cleared", out)
        code, out = self._run(["--check", "T1"])
        self.assertIn("0/3", out)

    def test_record_to_threshold_exit_3(self):
        self._run(["--record", "T1"])
        self._run(["--record", "T1"])
        code, out = self._run(["--record", "T1"])
        self.assertEqual(code, 3)
        self.assertIn("3/3", out)

    def test_hook_block_returns_exit_2(self):
        for _ in range(fc.THRESHOLD):
            self._run(["--record", "T1"])
        sys.stdin = io.StringIO(json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls"}}))
        out, err = io.StringIO(), io.StringIO()
        try:
            with redirect_stdout(out), redirect_stderr(err):
                code = fc.main(["--hook"])
        finally:
            sys.stdin = sys.__stdin__
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(out.getvalue())["decision"], "block")


if __name__ == "__main__":
    unittest.main()
