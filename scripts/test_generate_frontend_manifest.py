#!/usr/bin/env python3
"""Unit tests for scripts/generate_frontend_manifest.py."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_frontend_manifest as gen


def write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


class TestGenerator(unittest.TestCase):
    def test_empty_repo_yields_empty_collections(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tasks").mkdir()
            (root / "logs" / "runs").mkdir(parents=True)
            (root / "memory" / "active_projects").mkdir(parents=True)

            payload = gen.build(root)

            self.assertEqual(payload, {
                "tasks": [],
                "logs": [],
                "decisions": [],
                "overview": {
                    "task_total": 0,
                    "task_status": {},
                    "task_skill": {},
                    "task_risk": {},
                    "run_total": 0,
                    "run_status": {},
                    "gate_results": {
                        "schema_check": {},
                        "rule_check": {},
                        "completion_check": {},
                        "risk_check": {},
                    },
                },
            })

    def test_multi_project_decisions_are_all_collected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for project in ("agent-harness", "vietnam-expansion"):
                write(
                    root / "memory" / "active_projects" / project / "decisions" / "20260101-D001_x.yaml",
                    'decision_id: "20260101-D001"\ndate: "2026-01-01"\ndecision: "stub"\nstatus: "active"\n',
                )

            payload = gen.build(root)
            projects = sorted(d["project"] for d in payload["decisions"])

            self.assertEqual(projects, ["agent-harness", "vietnam-expansion"])
            self.assertEqual(len(payload["decisions"]), 2)

    def test_idempotent_output_is_byte_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / "tasks" / "20260101_sample.yaml",
                'task_id: "20260101-001"\ndate: "2026-01-01"\nstatus: "done"\nskill_type: "ops"\ngoal: "sample"\nrisk_level: "low"\n',
            )
            write(
                root / "logs" / "runs" / "20260101-001_sample.yaml",
                'execution_log:\n  run_id: "RUN-1"\n  task_id: "20260101-001"\n  status: "completed"\n  started_at: "2026-01-01"\n  ended_at: "2026-01-01"\n',
            )
            write(
                root / "memory" / "active_projects" / "agent-harness" / "decisions" / "20260101-D001_x.yaml",
                'decision_id: "20260101-D001"\ndate: "2026-01-01"\ndecision: "stub"\nstatus: "active"\n',
            )

            first = gen.dump(gen.build(root))
            second = gen.dump(gen.build(root))

            self.assertEqual(first, second)
            json.loads(first)


class TestDriftCheck(unittest.TestCase):
    def test_check_mode_detects_missing_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tasks").mkdir()
            (root / "logs" / "runs").mkdir(parents=True)
            (root / "memory" / "active_projects").mkdir(parents=True)
            (root / "frontend").mkdir()

            original_root = gen.ROOT
            original_output = gen.OUTPUT
            try:
                gen.ROOT = root
                gen.OUTPUT = root / "frontend" / "data.json"
                self.assertEqual(gen.main(["--check"]), 1)
                gen.OUTPUT.write_text(gen.dump(gen.build(root)), encoding="utf-8")
                self.assertEqual(gen.main(["--check"]), 0)
            finally:
                gen.ROOT = original_root
                gen.OUTPUT = original_output


if __name__ == "__main__":
    unittest.main()
