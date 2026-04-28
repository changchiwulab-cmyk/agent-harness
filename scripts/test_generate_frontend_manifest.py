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


def make_skeleton(root: Path) -> None:
    (root / "tasks").mkdir(parents=True, exist_ok=True)
    (root / "logs" / "runs").mkdir(parents=True, exist_ok=True)
    (root / "memory" / "active_projects").mkdir(parents=True, exist_ok=True)
    (root / "system").mkdir(parents=True, exist_ok=True)


class TestGenerator(unittest.TestCase):
    def test_empty_repo_yields_empty_collections(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_skeleton(root)

            payload = gen.build(root)

            self.assertEqual(
                payload,
                {"tasks": [], "logs": [], "decisions": [], "system_meta": {}},
            )

    def test_multi_project_decisions_are_all_collected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_skeleton(root)
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
            make_skeleton(root)
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

    def test_log_gate_results_round_trip(self):
        """Nested gate_results dict survives extraction and JSON round-trip."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_skeleton(root)
            write(
                root / "logs" / "runs" / "20260201-001_run.yaml",
                (
                    "execution_log:\n"
                    '  run_id: "RUN-2"\n'
                    '  task_id: "20260201-001"\n'
                    '  status: "completed"\n'
                    "  gate_results:\n"
                    '    schema_check: "pass"\n'
                    '    rule_check: "pass"\n'
                    '    completion_check: "fail"\n'
                    '    risk_check: "pass"\n'
                ),
            )

            payload = gen.build(root)
            self.assertEqual(len(payload["logs"]), 1)
            log = payload["logs"][0]
            self.assertEqual(log["gate_results"]["schema_check"], "pass")
            self.assertEqual(log["gate_results"]["completion_check"], "fail")

            parsed = json.loads(gen.dump(payload))
            self.assertEqual(parsed["logs"][0]["gate_results"], log["gate_results"])

    def test_log_approvals_array_preserved(self):
        """approvals[] list of dicts is preserved as-is, including order."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_skeleton(root)
            write(
                root / "logs" / "runs" / "20260201-002_run.yaml",
                (
                    "execution_log:\n"
                    '  run_id: "RUN-3"\n'
                    '  task_id: "20260201-002"\n'
                    '  status: "completed"\n'
                    "  approvals:\n"
                    '    - action: "建立 Task Card"\n'
                    '      status: "approved"\n'
                    '      approved_by: "human"\n'
                    '      timestamp: "2026-02-01"\n'
                    '    - action: "修改 system/"\n'
                    '      status: "pending"\n'
                    '      approved_by: "human"\n'
                    '      timestamp: "2026-02-02"\n'
                    "  tools_used:\n"
                    "    - tool: file_read\n"
                    "      call_count: 9\n"
                    "  checkpoints:\n"
                    '    - commit: "abc1234"\n'
                    '      stage: "stage 1"\n'
                ),
            )

            payload = gen.build(root)
            log = payload["logs"][0]
            self.assertEqual(len(log["approvals"]), 2)
            self.assertEqual(log["approvals"][0]["status"], "approved")
            self.assertEqual(log["approvals"][1]["status"], "pending")
            self.assertEqual(log["tools_used"][0]["tool"], "file_read")
            self.assertEqual(log["checkpoints"][0]["commit"], "abc1234")

    def test_system_meta_loads_three_files(self):
        """system_meta loads GATE_POLICY, APPROVAL_POLICY, FAILURE_TAXONOMY."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_skeleton(root)
            write(
                root / "system" / "GATE_POLICY.yaml",
                "gates:\n  schema_check:\n    description: \"x\"\n",
            )
            write(
                root / "system" / "APPROVAL_POLICY.yaml",
                "triggers:\n  - condition: \"x\"\n    method: human_confirm\n",
            )
            write(
                root / "system" / "FAILURE_TAXONOMY.yaml",
                "categories:\n  spec:\n    - id: SPEC-01\n      name: \"x\"\n",
            )

            payload = gen.build(root)
            meta = payload["system_meta"]
            self.assertIn("gate_policy", meta)
            self.assertIn("approval_policy", meta)
            self.assertIn("failure_taxonomy", meta)
            self.assertIn("schema_check", meta["gate_policy"]["gates"])

    def test_failure_taxonomy_real_file_complete(self):
        """Real system/FAILURE_TAXONOMY.yaml has the documented 4 groups and >=14 entries.

        Docs (GLOBAL_RULES.md) cite 14 categories; the file may carry >=14 if security
        entries grow (SEC-04 added 2026-04-09 per RUN-20260409-001). We pin the floor
        plus structural invariants the Failure Map panel depends on.
        """
        repo_root = Path(__file__).resolve().parents[1]
        meta = gen.collect_system_meta(repo_root)
        taxonomy = meta.get("failure_taxonomy", {})
        categories = taxonomy.get("categories", {})

        self.assertEqual(set(categories.keys()), {"spec", "coordination", "validation", "security"})
        flat_ids = [item["id"] for group in categories.values() for item in group]
        self.assertGreaterEqual(len(flat_ids), 14)
        self.assertEqual(len(set(flat_ids)), len(flat_ids), "duplicate failure ids")
        for group in categories.values():
            for item in group:
                self.assertTrue(item.get("id"), "missing id")
                self.assertTrue(item.get("name"), f"missing name for {item.get('id')}")
                self.assertTrue(item.get("mitigation"), f"missing mitigation for {item.get('id')}")

    def test_decision_extended_fields_collected(self):
        """Decision extraction surfaces options_considered, risk, revisit_trigger."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_skeleton(root)
            write(
                root / "memory" / "active_projects" / "agent-harness" / "decisions" / "20260301-D001_x.yaml",
                (
                    'decision_id: "20260301-D001"\n'
                    'date: "2026-03-01"\n'
                    'decision: "pick A"\n'
                    'status: "active"\n'
                    'risk: "rollback cost is medium"\n'
                    'revisit_trigger: "if X happens"\n'
                    'related_task: "20260301-O01"\n'
                    "options_considered:\n"
                    '  - option: "A"\n'
                    '    pros: "simple"\n'
                    '    cons: "limited"\n'
                    '  - option: "B"\n'
                    '    pros: "powerful"\n'
                    '    cons: "complex"\n'
                ),
            )

            payload = gen.build(root)
            decision = payload["decisions"][0]
            self.assertEqual(len(decision["options_considered"]), 2)
            self.assertEqual(decision["options_considered"][0]["option"], "A")
            self.assertEqual(decision["risk"], "rollback cost is medium")
            self.assertEqual(decision["revisit_trigger"], "if X happens")
            self.assertEqual(decision["related_task"], "20260301-O01")


class TestDriftCheck(unittest.TestCase):
    def test_check_mode_detects_missing_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_skeleton(root)
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
