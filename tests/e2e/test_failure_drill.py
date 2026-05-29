#!/usr/bin/env python3
"""R5 failure-drill regression test.

The self-assessment (Task Card 20260529-001) flagged that the failure path
(schema fail -> error log -> run log) had never been exercised on a real
failure — only happy-path runs existed in logs/runs/. This test pins that
contract so it cannot silently regress:

1. A deliberately schema-invalid Task Card fixture MUST be rejected by
   system/validate_task_card.py — the same check the runtime uses for the
   GATE_POLICY ``schema_check`` gate. The fixture lives under
   tests/e2e/fixtures/ (NOT tasks/) so check_spec_consistency.rb, which globs
   tasks/**/*.yaml, never validates it and CI stays green — yet it must remain
   parseable YAML so the repo-wide YAML-parse step is unaffected.
2. The controlled failure the drill produced MUST stay captured in
   logs/runs/ (status=failed, schema_check=fail) and logs/errors/.

If someone "fixes" the fixture or deletes the drill records, this fails.
"""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
VALIDATE_SCRIPT = ROOT / "system" / "validate_task_card.py"
BROKEN_FIXTURE = ROOT / "tests" / "e2e" / "fixtures" / "broken_schema_task.yaml"
RUN_LOG = ROOT / "logs" / "runs" / "RUN-20260529-003.yaml"
ERROR_LOG = ROOT / "logs" / "errors" / "2026-05-29_20260529-003_error.md"


class TestFailureDrill(unittest.TestCase):
    def test_broken_fixture_fails_schema_gate(self):
        """schema_check MUST reject the fixture and name the violations."""
        self.assertTrue(BROKEN_FIXTURE.exists(), "broken fixture is missing")
        result = subprocess.run(
            [sys.executable, str(VALIDATE_SCRIPT), str(BROKEN_FIXTURE)],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(
            result.returncode, 0, "fixture should FAIL schema validation (it is intentionally broken)"
        )
        out = result.stdout + result.stderr
        self.assertIn("definition_of_done", out)
        self.assertIn("skill_type", out)

    def test_fixture_is_parseable_yaml_and_not_under_tasks(self):
        """Must stay valid YAML (repo-wide parse step) and live outside tasks/."""
        with BROKEN_FIXTURE.open(encoding="utf-8") as f:
            yaml.safe_load(f)  # raises if not parseable
        rel = BROKEN_FIXTURE.relative_to(ROOT).as_posix()
        self.assertFalse(rel.startswith("tasks/"), "fixture must NOT live under tasks/")

    def test_drill_records_capture_the_failure(self):
        """The failed run log + error log produced by the drill must persist."""
        self.assertTrue(RUN_LOG.exists(), "run log RUN-20260529-003.yaml is missing")
        self.assertTrue(ERROR_LOG.exists(), "error log for 20260529-003 is missing")
        run = yaml.safe_load(RUN_LOG.read_text(encoding="utf-8"))
        log = run.get("execution_log", run)
        self.assertEqual(log.get("status"), "failed")
        self.assertEqual(log.get("gate_results", {}).get("schema_check"), "fail")
        self.assertTrue(str(log.get("error_summary", "")).strip(), "error_summary must be filled")
        self.assertIn("schema_failure", ERROR_LOG.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
