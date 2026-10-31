#!/usr/bin/env python3
"""Unit tests for scripts/mcp_guard.py（20261031-P01）。"""

from __future__ import annotations

import io
import json
import subprocess
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import mcp_guard as guard  # noqa: E402


def run_raw(raw: str) -> tuple[int, dict, str]:
    sys.stdin = io.StringIO(raw)
    out, err = io.StringIO(), io.StringIO()
    try:
        with redirect_stdout(out), redirect_stderr(err):
            code = guard.run_guarded()
    finally:
        sys.stdin = sys.__stdin__
    text = out.getvalue().strip()
    return code, (json.loads(text) if text else {}), err.getvalue()


def run_tool(name: str) -> tuple[int, dict, str]:
    return run_raw(json.dumps({"tool_name": name, "tool_input": {}}))


def is_ask(out: dict) -> bool:
    return out.get("hookSpecificOutput", {}).get("permissionDecision") == "ask"


class TestClassify(unittest.TestCase):
    DENY = [
        "mcp__github__merge_pull_request",
        "mcp__github__push_files",
        "mcp__github__delete_file",
        "mcp__github__create_or_update_file",
        "mcp__github__enable_pr_auto_merge",
        "mcp__github__fork_repository",
        "mcp__Google_Drive__share_file",
        "mcp__Google_Drive__trash_file",
        "mcp__Claude_Docs__delete",
        "mcp__gmail__send_email",
        "mcp__slack__post_message",
        "mcp__stripe__create_payment",
        "mcp__claude-code-remote__delete_trigger",
    ]
    ASK = [
        "mcp__github__create_pull_request",
        "mcp__github__add_issue_comment",
        "mcp__github__issue_write",
        "mcp__github__update_pull_request",
        "mcp__github__disable_pr_auto_merge",
        "mcp__Google_Drive__create_file",
        "mcp__Claude_Docs__batch",
        "mcp__claude-code-remote__send_message",
        "mcp__claude-code-remote__send_later",
        "mcp__gmail__create_email_draft",
        "mcp__some_new_server__frobnicate",
    ]
    def test_deny(self):
        for name in self.DENY:
            with self.subTest(name=name):
                self.assertEqual(guard.classify(name)[0], "deny")

    def test_ask(self):
        for name in self.ASK:
            with self.subTest(name=name):
                self.assertEqual(guard.classify(name)[0], "ask")

    def test_read_verbs_allow(self):
        for name in [
            "mcp__github__get_file_contents",
            "mcp__github__list_pull_requests",
            "mcp__github__search_code",
            "mcp__Google_Drive__read_file_content",
            "mcp__Google_Drive__download_file_content",
            "mcp__gmail__read_email",          # 受詞含 email 不誤擋
            "mcp__Google_Drive__get_file_permissions",
            "mcp__claude-code-remote__read_documentation",
        ]:
            with self.subTest(name=name):
                self.assertEqual(guard.classify(name)[0], "allow")

    def test_non_leading_read_verb_is_ask(self):
        # 唯讀動詞不在開頭 → 保守 ask，不推測
        self.assertEqual(guard.classify("mcp__github__pull_request_read")[0], "ask")

    def test_unparseable_name_is_ask(self):
        for name in ["", "Bash", "mcp__onlyserver", "mcp____"]:
            with self.subTest(name=name):
                self.assertEqual(guard.classify(name)[0], "ask")


class TestMainIO(unittest.TestCase):
    def test_deny_exit2_and_stderr(self):
        code, out, err = run_tool("mcp__github__merge_pull_request")
        self.assertEqual(code, 2)
        self.assertEqual(out["decision"], "block")
        self.assertIn("BLOCKED by mcp_guard", err)

    def test_ask_emits_permission_decision(self):
        code, out, _ = run_tool("mcp__github__create_pull_request")
        self.assertEqual(code, 0)
        self.assertTrue(is_ask(out))
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "PreToolUse")

    def test_allow_silent(self):
        code, out, _ = run_tool("mcp__github__list_branches")
        self.assertEqual((code, out), (0, {}))

    def test_bad_input_fails_to_ask_not_open(self):
        for raw in ["", "not json", "[1,2]"]:
            with self.subTest(raw=raw):
                code, out, _ = run_raw(raw)
                self.assertEqual(code, 0)
                self.assertTrue(is_ask(out))

    def test_internal_crash_fails_to_ask(self):
        orig = guard.classify
        guard.classify = lambda _n: (_ for _ in ()).throw(RuntimeError("boom"))
        try:
            code, out, _ = run_tool("mcp__github__list_branches")
        finally:
            guard.classify = orig
        self.assertEqual(code, 0)
        self.assertTrue(is_ask(out))

    def test_subprocess_stdlib_only(self):
        # -I：隔離模式，不吃使用者 site-packages；確保無第三方依賴
        r = subprocess.run(
            [sys.executable, "-I", str(HERE / "mcp_guard.py")],
            input=json.dumps({"tool_name": "mcp__Google_Drive__trash_file"}),
            capture_output=True, text=True,
        )
        self.assertEqual(r.returncode, 2, r.stderr)


class TestWiring(unittest.TestCase):
    def test_settings_registers_mcp_matcher(self):
        settings = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        entries = settings["hooks"]["PreToolUse"]
        hit = [
            e for e in entries
            if e.get("matcher") == "mcp__.*"
            and any("scripts/mcp_guard.py" in h.get("command", "") for h in e.get("hooks", []))
        ]
        self.assertEqual(len(hit), 1, "PreToolUse 必須有唯一一組 matcher=mcp__.* 掛 mcp_guard.py")

    def test_permissions_enforcement_registered(self):
        text = (ROOT / "system" / "PERMISSIONS.yaml").read_text(encoding="utf-8")
        self.assertIn("scripts/mcp_guard.py", text)


if __name__ == "__main__":
    unittest.main()
