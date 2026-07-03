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
                    "task_model": {},
                    "run_total": 0,
                    "run_status": {},
                    "run_model": {},
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

    def test_task_model_tier_explicit_wins_then_skill_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / "system" / "MODEL_ROUTING.yaml",
                "routing:\n  by_skill_default:\n    ops: fast\n    analysis: strategy\n",
            )
            write(
                root / "tasks" / "20260101_explicit.yaml",
                'task_id: "20260101-001"\ndate: "2026-01-01"\nstatus: "done"\nskill_type: "ops"\ngoal: "x"\nrisk_level: "low"\nmodel_routing:\n  tier: "strategy"\n',
            )
            write(
                root / "tasks" / "20260102_default.yaml",
                'task_id: "20260102-001"\ndate: "2026-01-02"\nstatus: "done"\nskill_type: "analysis"\ngoal: "y"\nrisk_level: "low"\n',
            )
            write(
                root / "tasks" / "20260103_unknown.yaml",
                'task_id: "20260103-001"\ndate: "2026-01-03"\nstatus: "done"\nskill_type: "writing"\ngoal: "z"\nrisk_level: "low"\n',
            )

            payload = gen.build(root)
            tiers = {t["task_id"]: t["model_tier"] for t in payload["tasks"]}

            self.assertEqual(tiers["20260101-001"], "strategy")  # explicit tier wins over ops default
            self.assertEqual(tiers["20260102-001"], "strategy")  # analysis -> by_skill_default
            self.assertEqual(tiers["20260103-001"], "unknown")   # writing absent from this routing map
            self.assertEqual(payload["overview"]["task_model"], {"strategy": 2, "unknown": 1})

    def test_phase_overrides_resolve_before_skill_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / "system" / "MODEL_ROUTING.yaml",
                "routing:\n  by_skill_default:\n    research: fast\n",
            )
            # multi-tier phase_overrides -> 'mixed', not the research 'fast' default
            write(
                root / "tasks" / "20260201_multi.yaml",
                'task_id: "20260201-001"\ndate: "2026-02-01"\nstatus: "done"\nskill_type: "research"\ngoal: "m"\nrisk_level: "low"\nmodel_routing:\n  tier: ""\n  phase_overrides:\n    explore: fast\n    synthesize: strategy\n',
            )
            # single-tier phase_overrides -> that tier
            write(
                root / "tasks" / "20260202_single.yaml",
                'task_id: "20260202-001"\ndate: "2026-02-02"\nstatus: "done"\nskill_type: "research"\ngoal: "s"\nrisk_level: "low"\nmodel_routing:\n  tier: ""\n  phase_overrides:\n    synthesize: strategy\n    plan: strategy\n',
            )

            payload = gen.build(root)
            tiers = {t["task_id"]: t["model_tier"] for t in payload["tasks"]}

            self.assertEqual(tiers["20260201-001"], "mixed")     # spans fast + strategy
            self.assertEqual(tiers["20260202-001"], "strategy")  # all overrides agree
            self.assertEqual(payload["overview"]["task_model"], {"mixed": 1, "strategy": 1})

    def test_run_model_tally_from_logs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / "logs" / "runs" / "r1.yaml",
                'execution_log:\n  run_id: "RUN-1"\n  task_id: "t1"\n  status: "completed"\n  model_used: "claude-opus-4-8"\n',
            )
            write(
                root / "logs" / "runs" / "r2.yaml",
                'execution_log:\n  run_id: "RUN-2"\n  task_id: "t2"\n  status: "completed"\n  model_used: "claude-opus-4-8"\n',
            )
            write(
                root / "logs" / "runs" / "r3.yaml",
                'execution_log:\n  run_id: "RUN-3"\n  task_id: "t3"\n  status: "completed"\n',
            )

            payload = gen.build(root)

            self.assertEqual(payload["overview"]["run_model"], {"claude-opus-4-8": 2, "unknown": 1})


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
