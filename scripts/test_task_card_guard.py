#!/usr/bin/env python3
"""Unit tests for scripts/task_card_guard.py (v2: active-task binding)."""

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
import task_card_guard as guard


def make_root() -> Path:
    """Temp root with outputs/reports + outputs/drafts + tasks/ + state/."""
    root = Path(tempfile.mkdtemp())
    (root / "outputs" / "reports").mkdir(parents=True)
    (root / "outputs" / "drafts").mkdir(parents=True)
    (root / "tasks").mkdir()
    (root / "state").mkdir()
    return root


def add_card(
    root: Path,
    task_id: str = "20260609-X01",
    filename: str = "backed.md",
    location: str = "outputs/reports/",
    status: str = "in_progress",
    card_file: str | None = None,
) -> None:
    card = {
        "task_id": task_id,
        "status": status,
        "expected_output": {"format": "md", "location": location, "filename": filename},
    }
    (root / "tasks" / (card_file or f"{task_id}.yaml")).write_text(
        yaml.safe_dump(card, allow_unicode=True), encoding="utf-8"
    )


def set_state(root: Path, task_id: str, status: str = "active") -> None:
    """直接寫 state 檔（不經 active_task.set_active 的存活檢查），模擬手改/過期狀態。"""
    (root / "state" / "active_task.yaml").write_text(
        yaml.safe_dump(
            {"task_id": task_id, "status": status, "activated_at": "2026-07-10", "note": ""}
        ),
        encoding="utf-8",
    )


def run_main(payload: dict) -> tuple[int, dict, str]:
    sys.stdin = io.StringIO(json.dumps(payload))
    out, err = io.StringIO(), io.StringIO()
    try:
        with redirect_stdout(out), redirect_stderr(err):
            code = guard.main()
    finally:
        sys.stdin = sys.__stdin__
    text = out.getvalue().strip()
    return code, (json.loads(text) if text else {}), err.getvalue()


class TestFrictionlessPaths(unittest.TestCase):
    """非 reports 路徑與既有報告維持零摩擦（99% 低風險路徑不上鎖）。"""

    def test_drafts_write_allowed(self):
        root = make_root()
        decision, _ = guard.evaluate(str(root / "outputs/drafts/foo.md"), root)
        self.assertEqual(decision, "allow")

    def test_non_output_path_allowed(self):
        root = make_root()
        decision, _ = guard.evaluate(str(root / "scripts/foo.py"), root)
        self.assertEqual(decision, "allow")

    def test_existing_report_edit_allowed(self):
        root = make_root()
        existing = root / "outputs/reports/existing.md"
        existing.write_text("# already promoted\n", encoding="utf-8")
        decision, _ = guard.evaluate(str(existing), root)
        self.assertEqual(decision, "allow")


class TestActiveTaskBinding(unittest.TestCase):
    """新建正式報告的三段綁定：active task → 卡存活 → 精確路徑。"""

    def test_missing_state_file_blocked(self):
        root = make_root()
        (root / "state" / "active_task.yaml").unlink(missing_ok=True)
        decision, reason = guard.evaluate(str(root / "outputs/reports/new.md"), root)
        self.assertEqual(decision, "block")
        self.assertIn("active_task.yaml", reason)

    def test_idle_state_blocked_with_set_hint(self):
        root = make_root()
        add_card(root, filename="new.md")
        set_state(root, "", status="idle")
        decision, reason = guard.evaluate(str(root / "outputs/reports/new.md"), root)
        self.assertEqual(decision, "block")
        self.assertIn("--set", reason)

    def test_active_card_exact_path_allowed(self):
        root = make_root()
        add_card(root, task_id="20260710-T01", filename="backed.md")
        set_state(root, "20260710-T01")
        decision, _ = guard.evaluate(str(root / "outputs/reports/backed.md"), root)
        self.assertEqual(decision, "allow")

    def test_stale_done_card_blocked(self):
        # v1 的 stale authorization 破口：done 卡永久授權同名檔 — v2 必須擋。
        root = make_root()
        add_card(root, task_id="20260710-T01", filename="backed.md", status="done")
        set_state(root, "20260710-T01")
        decision, reason = guard.evaluate(str(root / "outputs/reports/backed.md"), root)
        self.assertEqual(decision, "block")
        self.assertIn("stale", reason)

    def test_failed_card_blocked(self):
        root = make_root()
        add_card(root, task_id="20260710-T01", filename="backed.md", status="failed")
        set_state(root, "20260710-T01")
        decision, _ = guard.evaluate(str(root / "outputs/reports/backed.md"), root)
        self.assertEqual(decision, "block")

    def test_active_id_without_card_blocked(self):
        root = make_root()
        set_state(root, "20260710-GONE")
        decision, reason = guard.evaluate(str(root / "outputs/reports/new.md"), root)
        self.assertEqual(decision, "block")
        self.assertIn("找不到", reason)

    def test_path_mismatch_blocked(self):
        root = make_root()
        add_card(root, task_id="20260710-T01", filename="declared.md")
        set_state(root, "20260710-T01")
        decision, reason = guard.evaluate(str(root / "outputs/reports/other.md"), root)
        self.assertEqual(decision, "block")
        self.assertIn("精確路徑", reason)

    def test_draft_located_card_does_not_authorize_report(self):
        # codex P2 語意保留：宣告 drafts 輸出的卡不得授權同名正式報告。
        root = make_root()
        add_card(root, task_id="20260710-T01", filename="foo.md", location="outputs/drafts/")
        set_state(root, "20260710-T01")
        decision, _ = guard.evaluate(str(root / "outputs/reports/foo.md"), root)
        self.assertEqual(decision, "block")

    def test_basename_coincidence_on_other_card_blocked(self):
        # v1 核心破口回歸測試：非 active 的卡宣告了同名檔案，不得再放行。
        root = make_root()
        add_card(root, task_id="20260710-T01", filename="mine.md")
        add_card(root, task_id="20260101-OLD", filename="coincidence.md", status="done",
                 card_file="old.yaml")
        set_state(root, "20260710-T01")
        decision, _ = guard.evaluate(str(root / "outputs/reports/coincidence.md"), root)
        self.assertEqual(decision, "block")

    def test_card_without_expected_output_blocked(self):
        root = make_root()
        (root / "tasks" / "bare.yaml").write_text(
            yaml.safe_dump({"task_id": "20260710-T01", "status": "in_progress"}),
            encoding="utf-8",
        )
        set_state(root, "20260710-T01")
        decision, reason = guard.evaluate(str(root / "outputs/reports/new.md"), root)
        self.assertEqual(decision, "block")
        self.assertIn("未宣告 expected_output", reason)


class TestMain(unittest.TestCase):
    def test_non_write_tool_passes_through(self):
        code, payload, _ = run_main({"tool_name": "Bash", "tool_input": {"command": "ls"}})
        self.assertEqual(code, 0)
        self.assertEqual(payload["decision"], "allow")

    def test_empty_stdin_allows(self):
        sys.stdin = io.StringIO("")
        out = io.StringIO()
        try:
            with redirect_stdout(out):
                code = guard.main()
        finally:
            sys.stdin = sys.__stdin__
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out.getvalue())["decision"], "allow")

    def test_write_to_real_repo_drafts_allowed(self):
        # Against the real repo root: drafts writes must never be blocked.
        code, payload, _ = run_main(
            {"tool_name": "Write", "tool_input": {"file_path": "outputs/drafts/scratch.md"}}
        )
        self.assertEqual(code, 0)
        self.assertEqual(payload["decision"], "allow")


if __name__ == "__main__":
    unittest.main()
