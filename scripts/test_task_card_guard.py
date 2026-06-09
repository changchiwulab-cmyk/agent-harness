#!/usr/bin/env python3
"""Unit tests for scripts/task_card_guard.py."""

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


def make_root(card_filename: str | None = None) -> Path:
    """Temp root with outputs/reports + optionally a Task Card declaring a filename."""
    root = Path(tempfile.mkdtemp())
    (root / "outputs" / "reports").mkdir(parents=True)
    (root / "outputs" / "drafts").mkdir(parents=True)
    (root / "tasks").mkdir()
    if card_filename:
        card = {
            "task_id": "20260609-X01",
            "expected_output": {"format": "md", "location": "outputs/reports/", "filename": card_filename},
        }
        (root / "tasks" / "card.yaml").write_text(
            yaml.safe_dump(card, allow_unicode=True), encoding="utf-8"
        )
    return root


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


class TestEvaluate(unittest.TestCase):
    def test_drafts_write_allowed(self):
        root = make_root()
        decision, _ = guard.evaluate(str(root / "outputs/drafts/foo.md"), root)
        self.assertEqual(decision, "allow")

    def test_unbacked_new_report_blocked(self):
        root = make_root()
        decision, reason = guard.evaluate(str(root / "outputs/reports/unbacked.md"), root)
        self.assertEqual(decision, "block")
        self.assertIn("Task Card", reason)

    def test_backed_new_report_allowed(self):
        root = make_root(card_filename="backed.md")
        decision, _ = guard.evaluate(str(root / "outputs/reports/backed.md"), root)
        self.assertEqual(decision, "allow")

    def test_existing_report_edit_allowed(self):
        root = make_root()
        existing = root / "outputs/reports/existing.md"
        existing.write_text("# already promoted\n", encoding="utf-8")
        decision, _ = guard.evaluate(str(existing), root)
        self.assertEqual(decision, "allow")

    def test_non_output_path_allowed(self):
        root = make_root()
        decision, _ = guard.evaluate(str(root / "scripts/foo.py"), root)
        self.assertEqual(decision, "allow")


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
