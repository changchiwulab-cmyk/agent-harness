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
                "budget": {
                    "context": {"budget": 3000, "total": 0, "files": []},
                    "skills": {"budget": 1500, "items": []},
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


class TestCollectors(unittest.TestCase):
    def test_collect_tasks_whitelists_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / "tasks" / "20260101_a.yaml",
                'task_id: "20260101-001"\ndate: "2026-01-01"\nstatus: "done"\n'
                'skill_type: "ops"\nrisk_level: "low"\napproval_needed: false\n'
                'goal: "g"\nsecret: "should-not-leak"\nnotes: "drop me"\n',
            )
            tasks = gen.collect_tasks(root)
            self.assertEqual(len(tasks), 1)
            t = tasks[0]
            self.assertEqual(t["path"], "tasks/20260101_a.yaml")
            self.assertNotIn("secret", t)
            self.assertNotIn("notes", t)
            self.assertEqual(
                set(t) - {"path"},
                {"task_id", "date", "status", "skill_type", "risk_level", "approval_needed", "goal"},
            )

    def test_collect_logs_unwraps_execution_log_and_flat(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "logs" / "runs").mkdir(parents=True)
            write(
                root / "logs" / "runs" / "20260101-001_wrapped.yaml",
                'execution_log:\n  run_id: "RUN-1"\n  task_id: "20260101-001"\n  status: "completed"\n'
                "  gate_results: {schema_check: pass, rule_check: pass}\n",
            )
            write(
                root / "logs" / "runs" / "20260102-002_flat.yaml",
                'run_id: "RUN-2"\ntask_id: "20260102-002"\nstatus: "failed"\n',
            )
            logs = gen.collect_logs(root)
            self.assertEqual(logs[0]["run_id"], "RUN-1")
            self.assertEqual(logs[0]["gate_results"], {"schema_check": "pass", "rule_check": "pass"})
            self.assertEqual(logs[1]["run_id"], "RUN-2")
            self.assertEqual(logs[1]["status"], "failed")

    def test_collect_decisions_extracts_project_and_whitelists(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / "memory" / "active_projects" / "proj-x" / "decisions" / "20260101-D001_d.yaml",
                'decision_id: "20260101-D001"\ndate: "2026-01-01"\ndecision: "do x"\n'
                'status: "active"\nrelated_task: "20260101-001"\nextra: "drop"\n',
            )
            decs = gen.collect_decisions(root)
            self.assertEqual(len(decs), 1)
            d = decs[0]
            self.assertEqual(d["project"], "proj-x")
            self.assertEqual(d["related_task"], "20260101-001")
            self.assertNotIn("extra", d)

    def test_load_yaml_non_mapping_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "x.yaml"
            p.write_text("- a\n- b\n- c\n", encoding="utf-8")
            self.assertEqual(gen.load_yaml(p), {})

    def test_build_overview_distributions_and_gate_tally(self):
        tasks = [
            {"status": "done", "skill_type": "ops", "risk_level": "low"},
            {"status": "done", "skill_type": "review", "risk_level": "medium"},
            {"status": "failed"},  # missing skill/risk -> unknown
        ]
        logs = [
            {"status": "completed", "gate_results": {
                "schema_check": "pass", "rule_check": "pass",
                "completion_check": "pass", "risk_check": "pass"}},
            {"status": "failed", "gate_results": {"schema_check": "fail"}},
            {"status": "completed"},  # no gate_results
        ]
        ov = gen.build_overview(tasks, logs)
        self.assertEqual(ov["task_total"], 3)
        self.assertEqual(ov["task_status"], {"done": 2, "failed": 1})
        self.assertEqual(ov["task_skill"], {"ops": 1, "review": 1, "unknown": 1})
        self.assertEqual(ov["task_risk"], {"low": 1, "medium": 1, "unknown": 1})
        self.assertEqual(ov["run_total"], 3)
        self.assertEqual(ov["run_status"], {"completed": 2, "failed": 1})
        self.assertEqual(ov["gate_results"]["schema_check"], {"pass": 1, "fail": 1})
        self.assertEqual(ov["gate_results"]["risk_check"], {"pass": 1})


class TestBudget(unittest.TestCase):
    def test_estimate_tokens_matches_ruby_formula(self):
        # ASCII / 4 + non-ASCII × 1, then ceil (same as check_context_budget.rb)
        self.assertEqual(gen.estimate_tokens("abcd" * 10), 10)  # 40 ascii -> 10
        self.assertEqual(gen.estimate_tokens("中文字"), 3)        # 3 non-ascii -> 3
        self.assertEqual(gen.estimate_tokens("ab中"), 2)          # ceil(0.5 + 1) -> 2
        self.assertEqual(gen.estimate_tokens(""), 0)

    def test_build_budget_collects_context_and_skills(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "CLAUDE.md", "abcd" * 10)                 # 10 tokens
            write(root / "system" / "GLOBAL_RULES.md", "中文字")    # 3 tokens
            write(root / "skills" / "ops" / "SKILL.md", "ab中")     # 2 tokens

            budget = gen.build_budget(root)

            self.assertEqual(budget["context"], {
                "budget": 3000,
                "total": 13,
                "files": [
                    {"path": "CLAUDE.md", "tokens": 10},
                    {"path": "system/GLOBAL_RULES.md", "tokens": 3},
                ],
            })
            self.assertEqual(budget["skills"], {
                "budget": 1500,
                "items": [{"path": "skills/ops/SKILL.md", "tokens": 2}],
            })

    def test_build_budget_skips_missing_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            budget = gen.build_budget(Path(tmp))
            self.assertEqual(budget["context"]["files"], [])
            self.assertEqual(budget["context"]["total"], 0)
            self.assertEqual(budget["skills"]["items"], [])


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

    def test_check_mode_detects_changed_output(self):
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
                gen.OUTPUT.write_text("stale-content\n", encoding="utf-8")
                self.assertEqual(gen.main(["--check"]), 1)  # present but drifted
                gen.OUTPUT.write_text(gen.dump(gen.build(root)), encoding="utf-8")
                self.assertEqual(gen.main(["--check"]), 0)
            finally:
                gen.ROOT = original_root
                gen.OUTPUT = original_output


if __name__ == "__main__":
    unittest.main()
