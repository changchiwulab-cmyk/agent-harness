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
                "evals": [],
                "eval_overview": {
                    "eval_total": 0,
                    "verdict": {},
                    "by_skill": {},
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


class TestEvals(unittest.TestCase):
    def test_collect_and_overview(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / "evals" / "results" / "EVAL-1.yaml",
                'eval_record:\n  eval_id: "EVAL-1"\n  skill_type: "research"\n'
                '  target: "x.md"\n  verdict: "pass"\n  score_pct: 100.0\n',
            )
            write(
                root / "evals" / "results" / "EVAL-2.yaml",
                'eval_record:\n  eval_id: "EVAL-2"\n  skill_type: "research"\n'
                '  target: "y.md"\n  verdict: "partial"\n  score_pct: 70.0\n',
            )
            payload = gen.build(root)
            self.assertEqual(len(payload["evals"]), 2)
            ov = payload["eval_overview"]
            self.assertEqual(ov["eval_total"], 2)
            self.assertEqual(ov["verdict"], {"pass": 1, "partial": 1})
            self.assertEqual(ov["by_skill"]["research"]["count"], 2)
            self.assertEqual(ov["by_skill"]["research"]["avg_score_pct"], 85.0)


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
