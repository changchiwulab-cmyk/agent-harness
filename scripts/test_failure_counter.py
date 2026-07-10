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
