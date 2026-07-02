#!/usr/bin/env python3
"""Unit tests for scripts/generate_audit_log.py.

Git interactions (`find_checkpoints`) are monkey-patched rather than driven by
real `git commit`, because the test sandbox enforces commit signing that
shouldn't be triggered for ephemeral fixtures. Real-world checkpoint detection
is exercised by the integration `tests/e2e/` smoke test.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_audit_log as gen


def write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


SAMPLE_TASK = """task_id: "20260501-X01"
date: "2026-05-01"
status: "done"
goal: "demo task"
skill_type: "ops"
risk_level: "low"
approval_needed: false
expected_output:
  format: "md"
  location: "outputs/drafts/"
  filename: "demo.md"
definition_of_done:
  - "demo done"
result_summary: "ok"
completion_time: "2026-05-01"
actual_tool_calls: 3
"""


class TestDeriveRecord(unittest.TestCase):
    def test_record_pulls_fields_from_task_card(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "tasks" / "20260501_demo.yaml", SAMPLE_TASK)

            tasks = gen.collect_tasks(root)
            self.assertEqual(len(tasks), 1)
            with mock.patch.object(gen, "find_checkpoints", return_value=[]):
                rec = gen.derive_record(tasks[0], root)
            self.assertEqual(rec["task_id"], "20260501-X01")
            self.assertEqual(rec["status"], "done")
            self.assertEqual(rec["output_path"], "outputs/drafts/demo.md")
            self.assertEqual(rec["actual_tool_calls"], 3)


class TestCheckpointDetection(unittest.TestCase):
    def test_find_checkpoints_invokes_git_log_with_correct_grep(self):
        with mock.patch("subprocess.run") as patched:
            patched.return_value = mock.Mock(
                stdout="abc1234\tcheckpoint: [20260501-X01] stage 1\n"
                       "def5678\tcheckpoint: [20260501-X01] stage 2\n",
                returncode=0,
            )
            checkpoints = gen.find_checkpoints("20260501-X01", Path("/tmp"))

        # Verify the subprocess was invoked with the right grep pattern.
        args, kwargs = patched.call_args
        cmd = args[0]
        self.assertIn("--grep=checkpoint: \\[20260501-X01\\]", cmd)
        self.assertEqual(len(checkpoints), 2)
        self.assertEqual(checkpoints[0]["commit"], "abc1234")
        self.assertTrue(all("20260501-X01" in c["subject"] for c in checkpoints))

    def test_missing_git_returns_empty_list(self):
        with mock.patch("subprocess.run", side_effect=FileNotFoundError):
            self.assertEqual(gen.find_checkpoints("X", Path("/tmp")), [])

    def test_card_recorded_checkpoints_take_precedence(self):
        # Card-first keeps --check deterministic across squash merges (codex P1):
        # git must not even be consulted when the card records its checkpoints.
        task = {
            "task_id": "20260501-X01",
            "checkpoints": [{"commit": "91277ad", "stage": "guard sync"}],
        }
        with mock.patch.object(gen, "find_checkpoints", side_effect=AssertionError("git consulted")):
            resolved = gen.resolve_checkpoints(task, Path("/tmp"))
        self.assertEqual(resolved, [{"commit": "91277ad", "stage": "guard sync"}])

    def test_string_checkpoints_preserved_as_notes(self):
        # Pre-R04 cards record checkpoints as free-form strings — keep them.
        task = {
            "task_id": "20260404-W01",
            "checkpoints": ["checkpoint: [20260404-W01] 草稿完成"],
        }
        with mock.patch.object(gen, "find_checkpoints", side_effect=AssertionError("git consulted")):
            resolved = gen.resolve_checkpoints(task, Path("/tmp"))
        self.assertEqual(resolved, [{"note": "checkpoint: [20260404-W01] 草稿完成"}])

    def test_empty_card_checkpoints_fall_back_to_git(self):
        sentinel = [{"commit": "abc1234", "subject": "checkpoint: [20260501-X01] s"}]
        for absent in ({"task_id": "20260501-X01"},
                       {"task_id": "20260501-X01", "checkpoints": []}):
            with mock.patch.object(gen, "find_checkpoints", return_value=sentinel) as patched:
                resolved = gen.resolve_checkpoints(absent, Path("/tmp"))
            patched.assert_called_once_with("20260501-X01", Path("/tmp"))
            self.assertEqual(resolved, sentinel)


class TestManualNotesPreservation(unittest.TestCase):
    def test_existing_manual_notes_survive_regeneration(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "tasks" / "20260501_demo.yaml", SAMPLE_TASK)

            output = root / "logs" / "AUDIT_LOG.md"
            existing = (
                "# Audit Log\n\n"
                f"{gen.AUTO_BEGIN}\n```yaml\nstale\n```\n{gen.AUTO_END}\n\n"
                "## 人工備註\n\n"
                "- 重要：上次部署後 retry 率上升，需追蹤\n"
            )
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(existing, encoding="utf-8")

            with mock.patch.object(gen, "find_checkpoints", return_value=[]):
                self.assertEqual(
                    gen.main(["--root", str(root), "--output", str(output)]),
                    0,
                )
            new = output.read_text(encoding="utf-8")
            self.assertIn("重要：上次部署後 retry 率上升", new)
            self.assertNotIn("stale", new)
            self.assertIn("20260501-X01", new)


class TestPreservationWithoutMarkers(unittest.TestCase):
    """Regression test for codex P1: when running against a hand-written
    AUDIT_LOG.md that has no AUTO_BEGIN/END markers, existing operator-authored
    records must survive into the manual notes section, not be silently dropped.
    """

    def test_unmarked_existing_body_is_preserved_as_manual_notes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "tasks" / "20260501_demo.yaml", SAMPLE_TASK)

            output = root / "logs" / "AUDIT_LOG.md"
            existing = (
                gen.HEADER.rstrip()
                + "\n\n```yaml\n"
                + '- task_id: "OLD-HANDWRITTEN-001"\n'
                + '  notes: "important historical record"\n'
                + "```\n"
            )
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(existing, encoding="utf-8")

            with mock.patch.object(gen, "find_checkpoints", return_value=[]):
                self.assertEqual(
                    gen.main(["--root", str(root), "--output", str(output)]),
                    0,
                )

            regenerated = output.read_text(encoding="utf-8")
            self.assertIn("OLD-HANDWRITTEN-001", regenerated, "existing record must survive")
            self.assertIn("important historical record", regenerated)
            self.assertIn("20260501-X01", regenerated, "new auto record present")
            # Ordering contract: auto section comes before manual notes.
            auto_pos = regenerated.index(gen.AUTO_BEGIN)
            manual_pos = regenerated.index("OLD-HANDWRITTEN-001")
            self.assertLess(auto_pos, manual_pos)


class TestDriftCheck(unittest.TestCase):
    def test_check_mode_detects_stale_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "tasks" / "20260501_demo.yaml", SAMPLE_TASK)

            output = root / "logs" / "AUDIT_LOG.md"
            with mock.patch.object(gen, "find_checkpoints", return_value=[]):
                self.assertEqual(
                    gen.main(["--root", str(root), "--output", str(output), "--check"]),
                    1,
                )
                self.assertEqual(
                    gen.main(["--root", str(root), "--output", str(output)]),
                    0,
                )
                self.assertEqual(
                    gen.main(["--root", str(root), "--output", str(output), "--check"]),
                    0,
                )


if __name__ == "__main__":
    unittest.main()
