#!/usr/bin/env python3
"""Unit tests for scripts/audit_drift_guard.py.

check_drift() is monkey-patched so tests never shell out to the real
generator/git (mirrors test_generate_audit_log.py's approach).
"""

from __future__ import annotations

import io
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit_drift_guard as g


def run(payload: dict, *, drift: bool, mode: str = "warn") -> tuple[int, dict]:
    stdin = io.StringIO(json.dumps(payload))
    stdout = io.StringIO()
    with mock.patch.object(g.sys, "stdin", stdin), mock.patch.object(
        g.sys, "stdout", stdout
    ), mock.patch.object(g, "check_drift", return_value=(drift, "detail")), mock.patch.dict(
        g.os.environ, {"AUDIT_DRIFT_GUARD": mode}
    ):
        code = g.main()
    return code, json.loads(stdout.getvalue().splitlines()[0])


class AuditDriftGuardTests(unittest.TestCase):
    def test_non_commit_bash_allowed_without_generator(self) -> None:
        with mock.patch.object(g, "check_drift") as cd:
            code, out = run(
                {"tool_name": "Bash", "tool_input": {"command": "ls -la"}},
                drift=True,
            )
        self.assertEqual(code, 0)
        self.assertEqual(out["decision"], "allow")
        cd.assert_not_called()  # never paid the generator cost

    def test_non_bash_tool_allowed(self) -> None:
        code, out = run(
            {"tool_name": "Edit", "tool_input": {"file_path": "x"}}, drift=True
        )
        self.assertEqual(code, 0)
        self.assertEqual(out["decision"], "allow")

    def test_commit_clean_allowed(self) -> None:
        code, out = run(
            {"tool_name": "Bash", "tool_input": {"command": "git commit -m x"}},
            drift=False,
        )
        self.assertEqual(code, 0)
        self.assertEqual(out["decision"], "allow")

    def test_commit_drift_warn_mode_allows_with_warning(self) -> None:
        code, out = run(
            {"tool_name": "Bash", "tool_input": {"command": "git commit -m x"}},
            drift=True,
            mode="warn",
        )
        self.assertEqual(code, 0)
        self.assertEqual(out["decision"], "allow")
        self.assertIn("drift", out["warning"].lower())

    def test_commit_drift_block_mode_blocks(self) -> None:
        code, out = run(
            {"tool_name": "Bash", "tool_input": {"command": "git commit -m x"}},
            drift=True,
            mode="block",
        )
        self.assertEqual(code, 2)
        self.assertEqual(out["decision"], "block")

    def test_git_commit_detection(self) -> None:
        self.assertTrue(g.is_git_commit("git commit -m 'x'"))
        self.assertTrue(g.is_git_commit("cd foo && git commit -am y"))
        self.assertTrue(g.is_git_commit("git -c user.name=x commit -m y"))
        self.assertFalse(g.is_git_commit("git status"))
        self.assertFalse(g.is_git_commit("legitimate_commit_tool"))
        self.assertFalse(g.is_git_commit(""))


if __name__ == "__main__":
    unittest.main()
