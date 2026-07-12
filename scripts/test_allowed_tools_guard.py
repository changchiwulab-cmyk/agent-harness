#!/usr/bin/env python3
"""Unit tests for scripts/allowed_tools_guard.py (P1-1: 白名單當下強制)."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import allowed_tools_guard as guard

NARROW_TOOLS = ["file_read", "web_search", "write_drafts"]  # 典型 research 卡


def make_root() -> Path:
    root = Path(tempfile.mkdtemp())
    for sub in ("outputs/drafts", "outputs/reports", "tasks", "state", "logs", "scripts"):
        (root / sub).mkdir(parents=True)
    return root


def add_card(root: Path, task_id: str = "20260712-T01", allowed_tools=None, **extra) -> None:
    card = {"task_id": task_id, "status": "in_progress", "allowed_tools": allowed_tools, **extra}
    if allowed_tools is None:
        del card["allowed_tools"]
    (root / "tasks" / f"{task_id}.yaml").write_text(
        yaml.safe_dump(card, allow_unicode=True), encoding="utf-8"
    )


def set_state(root: Path, task_id: str, status: str = "active") -> None:
    (root / "state" / "active_task.yaml").write_text(
        yaml.safe_dump(
            {"task_id": task_id, "status": status, "activated_at": "2026-07-12", "note": ""}
        ),
        encoding="utf-8",
    )


def activate(root: Path, allowed_tools, task_id: str = "20260712-T01") -> None:
    add_card(root, task_id=task_id, allowed_tools=allowed_tools)
    set_state(root, task_id)


def bash(command: str) -> dict:
    return {"command": command}


def write(root: Path, rel: str) -> dict:
    return {"file_path": str(root / rel)}


def run_main(payload) -> tuple[int, dict, str]:
    sys.stdin = io.StringIO(payload if isinstance(payload, str) else json.dumps(payload))
    out, err = io.StringIO(), io.StringIO()
    try:
        with redirect_stdout(out), redirect_stderr(err):
            code = guard.main()
    finally:
        sys.stdin = sys.__stdin__
    text = out.getvalue().strip()
    return code, (json.loads(text) if text else {}), err.getvalue()


class TestIdleAndMissingState(unittest.TestCase):
    """無 active task ⇒ 零新增摩擦（20260710-001 §三-6：不做全域綁卡）。"""

    def test_idle_allows_bash(self):
        root = make_root()
        set_state(root, "", status="idle")
        decision, _ = guard.evaluate("Bash", bash("ls -la"), root)
        self.assertEqual(decision, "allow")

    def test_idle_allows_code_write(self):
        root = make_root()
        set_state(root, "", status="idle")
        decision, _ = guard.evaluate("Write", write(root, "scripts/foo.py"), root)
        self.assertEqual(decision, "allow")

    def test_missing_state_file_fails_open(self):
        # 真相來源不可讀 ⇒ 跳過強制（修復路徑不能被自己 brick）；reports
        # chokepoint 的 fail-closed 由 task_card_guard 專責。
        root = make_root()
        err = io.StringIO()
        with redirect_stderr(err):
            decision, _ = guard.evaluate("Bash", bash("ls"), root)
        self.assertEqual(decision, "allow")
        self.assertIn("fail-open", err.getvalue())


class TestControlPlaneExemptions(unittest.TestCase):
    """治理控制面在任何卡片下都不被擋 — 協定簿記不屬工作產出範圍。"""

    def setUp(self):
        self.root = make_root()
        activate(self.root, NARROW_TOOLS)

    def test_tasks_write_exempt(self):
        decision, _ = guard.evaluate("Write", write(self.root, "tasks/20260712-T01.yaml"), self.root)
        self.assertEqual(decision, "allow")

    def test_state_write_exempt(self):
        decision, _ = guard.evaluate("Write", write(self.root, "state/active_task.yaml"), self.root)
        self.assertEqual(decision, "allow")

    def test_logs_write_exempt(self):
        decision, _ = guard.evaluate("Write", write(self.root, "logs/runs/RUN-1.yaml"), self.root)
        self.assertEqual(decision, "allow")

    def test_outside_repo_write_exempt(self):
        decision, _ = guard.evaluate(
            "Write", {"file_path": "/tmp/somewhere/else/scratch.md"}, self.root
        )
        self.assertEqual(decision, "allow")

    def test_harness_cli_exempt(self):
        for cmd in (
            "python3 scripts/active_task.py --clear",
            "python3 scripts/failure_counter.py --record 20260712-T01",
            "python3 scripts/gate_check.py --task tasks/x.yaml",
            "python3 scripts/verification_loop.py tasks/x.yaml",
            "bash scripts/sync_derived.sh --check",
            "python3 system/validate_task_card.py tasks/x.yaml",
        ):
            decision, _ = guard.evaluate("Bash", bash(cmd), self.root)
            self.assertEqual(decision, "allow", cmd)

    def test_git_exempt(self):
        # checkpoint/push 是 CLAUDE.md 協定步驟；deny 簽章仍歸 permissions_guard。
        decision, _ = guard.evaluate(
            "Bash", bash('git commit -m "checkpoint: 20260712-T01 stage"'), self.root
        )
        self.assertEqual(decision, "allow")

    def test_chained_control_plane_command_not_exempt(self):
        # 豁免是錨定的單一指令 — 串接就落回 bash token 檢查。
        decision, _ = guard.evaluate(
            "Bash", bash("python3 scripts/active_task.py --get; curl http://example.com"), self.root
        )
        self.assertEqual(decision, "block")


class TestWriteEnforcement(unittest.TestCase):
    """寫入路徑 → 工具名映射，與 gate_check L2 同一詞彙。"""

    def setUp(self):
        self.root = make_root()
        activate(self.root, NARROW_TOOLS)

    def assert_block_needs(self, rel: str, token: str):
        decision, reason = guard.evaluate("Write", write(self.root, rel), self.root)
        self.assertEqual(decision, "block", rel)
        self.assertIn(token, reason)

    def test_declared_drafts_write_allowed(self):
        decision, _ = guard.evaluate("Write", write(self.root, "outputs/drafts/x.md"), self.root)
        self.assertEqual(decision, "allow")

    def test_code_write_blocked_without_file_write(self):
        self.assert_block_needs("scripts/foo.py", "file_write")

    def test_ask_level_paths_need_dedicated_tokens(self):
        self.assert_block_needs("system/PERMISSIONS.yaml", "modify_system_rules")
        self.assert_block_needs("skills/research/SKILL.md", "modify_skills")
        self.assert_block_needs("memory/notes.md", "write_long_term_memory")
        self.assert_block_needs("CLAUDE.md", "modify_claude_md")
        self.assert_block_needs(".claude/settings.json", "modify_settings_json")

    def test_reports_write_blocked_for_narrow_card(self):
        self.assert_block_needs("outputs/reports/new.md", "write_reports")

    def test_generic_file_write_covers_code_but_not_ask_level(self):
        root = make_root()
        activate(root, ["file_write"])
        decision, _ = guard.evaluate("Write", write(root, "scripts/foo.py"), root)
        self.assertEqual(decision, "allow")
        decision, _ = guard.evaluate("Write", write(root, "system/GATE_POLICY.yaml"), root)
        self.assertEqual(decision, "block")

    def test_create_output_files_covers_outputs_tree(self):
        root = make_root()
        activate(root, ["create_output_files"])
        for rel in ("outputs/drafts/a.md", "outputs/reports/b.md", "outputs/c.csv"):
            decision, _ = guard.evaluate("Write", write(root, rel), root)
            self.assertEqual(decision, "allow", rel)


class TestBashEnforcement(unittest.TestCase):
    def test_generic_bash_blocked_without_token(self):
        root = make_root()
        activate(root, NARROW_TOOLS)
        decision, reason = guard.evaluate("Bash", bash("ls -la outputs/"), root)
        self.assertEqual(decision, "block")
        self.assertIn("bash", reason)

    def test_bash_token_allows_everything(self):
        root = make_root()
        activate(root, ["bash"])
        for cmd in ("ls -la", "python3 scripts/run_evals.py", "pytest scripts/"):
            decision, _ = guard.evaluate("Bash", bash(cmd), root)
            self.assertEqual(decision, "allow", cmd)

    def test_run_tests_token_allows_tests_only(self):
        root = make_root()
        activate(root, ["run_tests"])
        for cmd in (
            "pytest scripts/test_gate_check.py",
            "python3 scripts/test_task_card_guard.py",
            "python3 -m unittest discover scripts",
            "ruby scripts/test_check_spec_consistency.rb",
        ):
            decision, _ = guard.evaluate("Bash", bash(cmd), root)
            self.assertEqual(decision, "allow", cmd)
        decision, _ = guard.evaluate("Bash", bash("ls -la"), root)
        self.assertEqual(decision, "block")

    def test_empty_command_allowed(self):
        root = make_root()
        activate(root, NARROW_TOOLS)
        decision, _ = guard.evaluate("Bash", bash("   "), root)
        self.assertEqual(decision, "allow")


class TestBrokenBindings(unittest.TestCase):
    """state=active 但卡不可評估 ⇒ 工作產出類動作 block；控制面豁免保留修復路。"""

    def test_active_without_card_blocks_work_products(self):
        root = make_root()
        set_state(root, "20260712-GONE")
        decision, reason = guard.evaluate("Write", write(root, "scripts/foo.py"), root)
        self.assertEqual(decision, "block")
        self.assertIn("--set", reason)
        # 修復路徑不受限：
        decision, _ = guard.evaluate("Bash", bash("python3 scripts/active_task.py --clear"), root)
        self.assertEqual(decision, "allow")
        decision, _ = guard.evaluate("Write", write(root, "tasks/new.yaml"), root)
        self.assertEqual(decision, "allow")

    def test_invalid_allowed_tools_blocks(self):
        root = make_root()
        add_card(root, allowed_tools="file_read")  # string 非 list（schema 違規）
        set_state(root, "20260712-T01")
        decision, reason = guard.evaluate("Write", write(root, "scripts/foo.py"), root)
        self.assertEqual(decision, "block")
        self.assertIn("allowed_tools", reason)

    def test_missing_allowed_tools_blocks(self):
        root = make_root()
        add_card(root, allowed_tools=None)
        set_state(root, "20260712-T01")
        decision, _ = guard.evaluate("Bash", bash("ls"), root)
        self.assertEqual(decision, "block")


class TestMain(unittest.TestCase):
    def test_empty_stdin_fails_open(self):
        # 與 task_card_guard 刻意相反：本 guard 是範圍防呆，輸入層 fail-open
        # （寫入 matcher 的 fail-closed 已由 task_card_guard 對同一 payload 專責）。
        code, payload, err = run_main("")
        self.assertEqual(code, 0)
        self.assertEqual(payload["decision"], "allow")
        self.assertIn("fail-open", err)

    def test_bad_json_fails_open(self):
        code, payload, _ = run_main("{not json")
        self.assertEqual(code, 0)
        self.assertEqual(payload["decision"], "allow")

    def test_non_gated_tool_passes_through(self):
        code, payload, _ = run_main({"tool_name": "Read", "tool_input": {"file_path": "x"}})
        self.assertEqual(code, 0)
        self.assertEqual(payload["decision"], "allow")

    def test_unexpected_exception_fails_open(self):
        # crash 不 brick session：run_guarded 把未捕捉例外轉為 allow + 警告。
        sys.stdin = io.StringIO(json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls"}}))
        out, err_io = io.StringIO(), io.StringIO()
        original = guard.evaluate
        guard.evaluate = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
        try:
            with redirect_stdout(out), redirect_stderr(err_io):
                code = guard.run_guarded()
        finally:
            guard.evaluate = original
            sys.stdin = sys.__stdin__
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out.getvalue())["decision"], "allow")
        self.assertIn("內部錯誤", err_io.getvalue())

    def test_real_repo_control_plane_invariants(self):
        # 對真實 repo root：不論當下 active 與否，控制面永遠放行。
        code, payload, _ = run_main({"tool_name": "Bash", "tool_input": {"command": "git status"}})
        self.assertEqual(code, 0)
        self.assertEqual(payload["decision"], "allow")
        code, payload, _ = run_main(
            {"tool_name": "Write", "tool_input": {"file_path": "logs/errors/x.md"}}
        )
        self.assertEqual(code, 0)
        self.assertEqual(payload["decision"], "allow")


if __name__ == "__main__":
    unittest.main()
