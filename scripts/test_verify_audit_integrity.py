#!/usr/bin/env python3
"""Unit tests for verify_audit_integrity.py (AGI-3: 20260606-B01)."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify_audit_integrity as vai  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def make_memory_root(tmp: str) -> Path:
    root = Path(tmp)
    dec = root / "memory" / "active_projects" / "proj" / "decisions"
    dec.mkdir(parents=True)
    (root / "memory" / "active_projects" / "proj" / "context.md").write_text("ctx v1", encoding="utf-8")
    (dec / "20260101-D001_x.yaml").write_text("decision_id: D001\n", encoding="utf-8")
    return root


class TestMemoryIntegrity(unittest.TestCase):
    def test_intact_after_update(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_memory_root(tmp)
            vai.main(["--update", "--root", str(root)])
            self.assertEqual(vai.check_memory(root), [])

    def test_tamper_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_memory_root(tmp)
            vai.main(["--update", "--root", str(root)])
            (root / "memory" / "active_projects" / "proj" / "context.md").write_text("ctx POISONED", encoding="utf-8")
            fails = vai.check_memory(root)
            self.assertTrue(any("TAMPERED" in f for f in fails), fails)

    def test_untracked_injection_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_memory_root(tmp)
            vai.main(["--update", "--root", str(root)])
            # Inject a new decision file not present when the manifest was built.
            (root / "memory" / "active_projects" / "proj" / "decisions" / "20260102-D002_evil.yaml").write_text(
                "decision_id: D002\n", encoding="utf-8"
            )
            fails = vai.check_memory(root)
            self.assertTrue(any("UNTRACKED" in f for f in fails), fails)

    def test_deletion_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_memory_root(tmp)
            vai.main(["--update", "--root", str(root)])
            (root / "memory" / "active_projects" / "proj" / "context.md").unlink()
            fails = vai.check_memory(root)
            self.assertTrue(any("MISSING" in f for f in fails), fails)


class TestCheckExitCodes(unittest.TestCase):
    def _run(self, root: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "verify_audit_integrity.py"), "--check", "--root", str(root)],
            capture_output=True, text=True,
        )

    def test_check_passes_when_intact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_memory_root(tmp)
            vai.main(["--update", "--root", str(root)])
            self.assertEqual(self._run(root).returncode, 0)

    def test_check_fails_when_tampered(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_memory_root(tmp)
            vai.main(["--update", "--root", str(root)])
            (root / "memory" / "active_projects" / "proj" / "context.md").write_text("evil", encoding="utf-8")
            self.assertEqual(self._run(root).returncode, 1)

    def test_coverage_gap_is_soft_not_fatal(self):
        """A done card absent from AUDIT_LOG is a WARN — must NOT fail --check."""
        with tempfile.TemporaryDirectory() as tmp:
            root = make_memory_root(tmp)
            (root / "tasks").mkdir()
            (root / "logs").mkdir()
            (root / "logs" / "AUDIT_LOG.md").write_text("# Audit Log\n", encoding="utf-8")
            (root / "tasks" / "20260101-done.yaml").write_text(
                "task_id: '20260101-001'\nstatus: done\n", encoding="utf-8"
            )
            vai.main(["--update", "--root", str(root)])
            self.assertEqual(self._run(root).returncode, 0)

    def test_live_repo_check_passes(self):
        """Regression guard for CI: the real repo's memory must be intact."""
        self.assertEqual(self._run(ROOT).returncode, 0)


if __name__ == "__main__":
    unittest.main()
