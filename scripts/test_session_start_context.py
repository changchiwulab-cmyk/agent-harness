#!/usr/bin/env python3
"""Unit tests for the SessionStart / Stop / PreCompact hook scripts.

重點驗證：(1) 未結 Task Card 能被挑出、(2) 已完成的不列入、(3) fail-open
（壞 YAML / 不存在的目錄都不丟例外）。
"""
from __future__ import annotations

import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import session_start_context as ssc
import precompact_preserve as pcp


def _write_card(tasks_dir: Path, task_id: str, status: str, goal: str) -> None:
    (tasks_dir / f"{task_id}.yaml").write_text(
        textwrap.dedent(
            f"""\
            task_id: "{task_id}"
            status: "{status}"
            goal: "{goal}"
            definition_of_done:
              - "做完 A"
              - "做完 B"
            """
        ),
        encoding="utf-8",
    )


class TestOpenTaskCards(unittest.TestCase):
    def test_picks_open_skips_done(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            tasks = root / "tasks"
            tasks.mkdir()
            _write_card(tasks, "20260529-100", "in_progress", "進行中任務")
            _write_card(tasks, "20260529-101", "done", "已完成任務")
            rows = ssc.open_task_cards(root)
            self.assertEqual(len(rows), 1)
            self.assertIn("20260529-100", rows[0])
            self.assertNotIn("20260529-101", "\n".join(rows))

    def test_fail_open_on_bad_yaml(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            tasks = root / "tasks"
            tasks.mkdir()
            (tasks / "20260529-200.yaml").write_text("{:::not yaml", encoding="utf-8")
            # 不應丟例外
            self.assertEqual(ssc.open_task_cards(root), [])

    def test_build_context_handles_empty_repo(self):
        with TemporaryDirectory() as d:
            out = ssc.build_context(Path(d))
            self.assertIn("未結 Task Card：無", out)
            self.assertIn("RECOVERY_RUNBOOK", out)

    def test_build_context_caps_long_list(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            tasks = root / "tasks"
            tasks.mkdir()
            for i in range(12):
                _write_card(tasks, f"20260529-4{i:02d}", "review", f"任務{i}")
            out = ssc.build_context(root, limit=8)
            self.assertIn("還有 4 張", out)
            shown = [ln for ln in out.splitlines() if ln.startswith("  - 20260529-4")]
            self.assertEqual(len(shown), 8)


class TestPrecompactPreserve(unittest.TestCase):
    def test_includes_dod_for_open_card(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            tasks = root / "tasks"
            tasks.mkdir()
            _write_card(tasks, "20260529-300", "in_progress", "保全測試")
            out = pcp.build_state(root)
            self.assertIn("20260529-300", out)
            self.assertIn("DoD: 做完 A", out)

    def test_skips_done_card(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            tasks = root / "tasks"
            tasks.mkdir()
            _write_card(tasks, "20260529-301", "done", "已完成")
            out = pcp.build_state(root)
            self.assertNotIn("20260529-301", out)

    def test_build_state_caps(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            tasks = root / "tasks"
            tasks.mkdir()
            for i in range(8):
                _write_card(tasks, f"20260529-5{i:02d}", "in_progress", f"t{i}")
            out = pcp.build_state(root, limit=5)
            self.assertIn("其餘 3 張", out)


if __name__ == "__main__":
    unittest.main()
