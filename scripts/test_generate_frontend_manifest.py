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

            self.assertEqual(payload, {"tasks": [], "logs": [], "decisions": [], "errors": []})

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
                'task_id: "20260101-001"\ndate: "2026-01-01"\nstatus: "done"\nskill_type: "ops"\ngoal: "sample"\nrisk_level: "low"\ndefinition_of_done:\n  - "done"\n',
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


class TestErrorCollection(unittest.TestCase):
    def test_errors_parse_and_exclude_template(self):
        """errors 解析成功且排除 template/gitkeep"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tasks").mkdir()
            (root / "logs" / "runs").mkdir(parents=True)
            (root / "memory" / "active_projects").mkdir(parents=True)
            errors_dir = root / "logs" / "errors"
            errors_dir.mkdir(parents=True)

            # Template file — must be excluded
            write(
                errors_dir / "ERROR_LOG_TEMPLATE.md",
                '# Template\n\n```yaml\nerror_id: "ERR-TEMPLATE"\ntask_id: "TEMPLATE"\ndate: "2099-01-01"\nskill_type: "ops"\nerror_type: "unknown"\nerror_summary: "template"\nfailure_count: 0\nrelated_rule: ""\nresolution: "stopped"\n```\n',
            )

            # .gitkeep — must be excluded
            (errors_dir / ".gitkeep").write_text("", encoding="utf-8")

            # Real error file — must be included
            write(
                errors_dir / "2026-04-04_S01_error.md",
                '# Error Log\n\n```yaml\nerror_id: "ERR-20260404-001"\ntask_id: "20260404-S01"\ndate: "2026-04-04"\nskill_type: "research"\nerror_type: "tool_failure"\nerror_summary: "rate limit hit"\nfailure_count: 1\nrelated_rule: "SEC-03 boundary; COORD-02 applies"\nresolution: "retried_success"\n```\n',
            )

            payload = gen.build(root)

            self.assertEqual(len(payload["errors"]), 1)
            err = payload["errors"][0]
            self.assertEqual(err["error_id"], "ERR-20260404-001")
            self.assertIn("SEC-03", err["taxonomy_codes"])
            self.assertIn("COORD-02", err["taxonomy_codes"])


class TestSchemaIssues(unittest.TestCase):
    def test_detect_task_schema_issues(self):
        """detect_task_schema_issues 對缺 DoD / 缺 risk_level / status=failed 各能命中"""
        # Missing DoD (empty list)
        issues = gen.detect_task_schema_issues({"goal": "x", "definition_of_done": []})
        self.assertIn("missing_dod", issues)

        # Missing goal and invalid risk_level
        issues = gen.detect_task_schema_issues({"goal": "", "risk_level": "extreme"})
        self.assertIn("missing_goal", issues)
        self.assertIn("invalid_risk_level", issues)

        # Status failed with all other fields valid
        issues = gen.detect_task_schema_issues({
            "status": "failed",
            "goal": "x",
            "definition_of_done": ["a"],
            "risk_level": "low",
            "skill_type": "ops",
        })
        self.assertEqual(issues, ["task_failed"])

    def test_logs_derive_gate_failures(self):
        """gate_results 中任一 fail 即 has_gate_failure=true 且 failed_gates 列出該欄位"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tasks").mkdir()
            (root / "memory" / "active_projects").mkdir(parents=True)
            log_dir = root / "logs" / "runs"
            log_dir.mkdir(parents=True)

            write(
                log_dir / "20260101-001_run.yaml",
                "execution_log:\n"
                "  run_id: \"RUN-20260101-001\"\n"
                "  task_id: \"20260101-001\"\n"
                "  status: \"failed\"\n"
                "  started_at: \"2026-01-01\"\n"
                "  ended_at: \"2026-01-01\"\n"
                "  gate_results:\n"
                "    schema_check: \"pass\"\n"
                "    rule_check: \"fail\"\n"
                "    completion_check: \"pass\"\n"
                "    risk_check: \"fail\"\n",
            )

            payload = gen.build(root)
            self.assertEqual(len(payload["logs"]), 1)
            log = payload["logs"][0]
            self.assertTrue(log["has_gate_failure"])
            self.assertEqual(log["failed_gates"], ["rule_check", "risk_check"])

    def test_idempotent_with_errors(self):
        """含 task + log + decision + error 的 fixture，連續呼叫 dump(build(root)) 兩次結果 byte-identical"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            # Task
            write(
                root / "tasks" / "20260101_sample.yaml",
                'task_id: "20260101-001"\ndate: "2026-01-01"\nstatus: "done"\nskill_type: "ops"\ngoal: "sample"\nrisk_level: "low"\ndefinition_of_done:\n  - "done"\n',
            )

            # Log
            write(
                root / "logs" / "runs" / "20260101-001_run.yaml",
                "execution_log:\n"
                "  run_id: \"RUN-20260101-001\"\n"
                "  task_id: \"20260101-001\"\n"
                "  status: \"completed\"\n"
                "  started_at: \"2026-01-01\"\n"
                "  ended_at: \"2026-01-01\"\n"
                "  gate_results:\n"
                "    schema_check: \"pass\"\n"
                "    rule_check: \"pass\"\n"
                "    completion_check: \"pass\"\n"
                "    risk_check: \"pass\"\n",
            )

            # Decision
            write(
                root / "memory" / "active_projects" / "agent-harness" / "decisions" / "20260101-D001_x.yaml",
                'decision_id: "20260101-D001"\ndate: "2026-01-01"\ndecision: "stub"\nstatus: "active"\n',
            )

            # Error
            errors_dir = root / "logs" / "errors"
            errors_dir.mkdir(parents=True)
            write(
                errors_dir / "2026-01-01_001_error.md",
                '# Error\n\n```yaml\nerror_id: "ERR-20260101-001"\ntask_id: "20260101-001"\ndate: "2026-01-01"\nskill_type: "ops"\nerror_type: "tool_failure"\nerror_summary: "test error"\nfailure_count: 1\nrelated_rule: "SPEC-01"\nresolution: "stopped"\n```\n',
            )

            first = gen.dump(gen.build(root))
            second = gen.dump(gen.build(root))

            self.assertEqual(first, second)
            parsed = json.loads(first)
            self.assertIsInstance(parsed["errors"], list)
            self.assertEqual(len(parsed["errors"]), 1)


if __name__ == "__main__":
    unittest.main()
