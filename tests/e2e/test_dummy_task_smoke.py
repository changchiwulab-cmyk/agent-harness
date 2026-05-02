#!/usr/bin/env python3
"""End-to-end smoke test: drive a dummy Task Card through all four gates.

This is the test that the harness's own analysis flagged as missing — every
existing CI step verifies static structure (schema, drift, budgets) but none
exercises the full happy-path: build a Task Card, run the schema → rule →
completion → risk gates against it, and confirm the output lands in
``outputs/drafts/`` (never ``outputs/reports/``) when ``risk_level >= high``.

The four gates are simulated in-process here. The real Claude Code runtime
performs them via natural-language reasoning over GATE_POLICY.yaml; this
test pins the *contract* those gates implement so a regression in
PERMISSIONS.yaml / GATE_POLICY.yaml structure surfaces in CI.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
VALIDATE_SCRIPT = ROOT / "system" / "validate_task_card.py"
PERMISSIONS_PATH = ROOT / "system" / "PERMISSIONS.yaml"
GATE_POLICY_PATH = ROOT / "system" / "GATE_POLICY.yaml"


DUMMY_TASK = {
    "task_id": "20260502-E2E",
    "date": "2026-05-02",
    "status": "pending",
    "goal": "smoke-test all four gates against a dummy task card",
    "context": "synthetic fixture for e2e smoke",
    "input_data": ["fixture://dummy"],
    "definition_of_done": [
        "schema gate runs",
        "rule gate runs",
        "completion gate runs",
        "risk gate runs",
    ],
    "expected_output": {
        "format": "md",
        "location": "outputs/drafts/",
        "filename": "20260502-E2E_smoke.md",
    },
    "risk_level": "high",
    "approval_needed": True,
    "allowed_tools": ["file_read", "write_drafts"],
    "max_tool_calls": 5,
    "max_retries": 3,
    "max_web_searches": 0,
    "skill_type": "ops",
}


def gate_schema(card: dict, validate_script: Path) -> tuple[bool, str]:
    """Gate 1: shell out to validate_task_card.py — same path used in real runs."""
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        yaml.safe_dump(card, f, allow_unicode=True, sort_keys=False)
        path = f.name
    result = subprocess.run(
        [sys.executable, str(validate_script), path],
        capture_output=True,
        text=True,
    )
    Path(path).unlink(missing_ok=True)
    return result.returncode == 0, result.stdout + result.stderr


def gate_rule(card: dict, permissions: dict) -> tuple[bool, str]:
    """Gate 2: every allowed_tool is whitelisted; no overlap with deny list."""
    deny = set(permissions["permissions"]["deny"])
    allow_or_ask = set(permissions["permissions"]["allow"]) | set(permissions["permissions"]["ask"])
    bad = []
    for tool in card.get("allowed_tools") or []:
        if tool in deny:
            bad.append(f"{tool} is in deny list")
        elif tool not in allow_or_ask:
            # Unknown tools that aren't on any list are accepted — Bash, file_read
            # etc. are physical primitives, not policy entries. Only deny breach is
            # a hard fail.
            pass
    return not bad, "; ".join(bad) or "ok"


def gate_completion(card: dict, produced_output: Path) -> tuple[bool, list[str]]:
    """Gate 3: every DoD line gets pass/fail. Missing output => all fail."""
    if not produced_output.exists():
        return False, ["output not produced"]
    body = produced_output.read_text(encoding="utf-8")
    misses = []
    for item in card.get("definition_of_done") or []:
        # Trivial heuristic: each DoD must appear by keyword in the produced
        # artifact OR be acknowledged via a `pass:` line. The real flow uses
        # LLM judgement; this test is just verifying the gate runs, not its
        # accuracy.
        if item not in body:
            misses.append(item)
    return not misses, misses


def gate_risk(card: dict, output_path: Path) -> tuple[bool, str]:
    """Gate 4: risk_level >= high must land in outputs/drafts/, not reports/."""
    if card.get("risk_level") in ("high", "critical"):
        if "outputs/drafts/" not in output_path.as_posix():
            return False, f"high-risk output must be in drafts/, got {output_path}"
    return True, "ok"


# All four gate names that GATE_POLICY.yaml is contractually required to define.
# Pinned here so renaming or removing any of them surfaces in CI rather than
# silently passing — this is the regression the codex P2 review flagged.
EXPECTED_GATES = frozenset({"schema_check", "rule_check", "completion_check", "risk_check"})


class TestDummyTaskSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.permissions = yaml.safe_load(PERMISSIONS_PATH.read_text(encoding="utf-8"))
        cls.gate_policy = yaml.safe_load(GATE_POLICY_PATH.read_text(encoding="utf-8"))

    def test_all_four_gates_fire_for_high_risk_dummy(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            drafts = tmp_path / "outputs" / "drafts"
            drafts.mkdir(parents=True)
            output = drafts / DUMMY_TASK["expected_output"]["filename"]
            # Synthesise a "produced" artefact that mentions every DoD line.
            output.write_text(
                "# smoke output\n\n"
                + "\n".join(f"- {d}" for d in DUMMY_TASK["definition_of_done"]),
                encoding="utf-8",
            )

            results = {
                "schema_check": gate_schema(DUMMY_TASK, VALIDATE_SCRIPT),
                "rule_check": gate_rule(DUMMY_TASK, self.permissions),
                "completion_check": gate_completion(DUMMY_TASK, output),
                "risk_check": gate_risk(DUMMY_TASK, output),
            }

        # Contract assertion: every gate runs and reports a verdict.
        self.assertEqual(set(results.keys()), EXPECTED_GATES)
        for name, (passed, _detail) in results.items():
            self.assertTrue(passed, f"{name} should pass for the dummy fixture: {_detail}")

    def test_policy_declares_all_four_gates(self):
        """Regression test for codex P2: all four gate names must exist in
        GATE_POLICY.yaml. Without this, three of the four gates could be
        renamed/removed silently and the smoke test would still pass."""
        declared = set(self.gate_policy.get("gates", {}).keys())
        missing = EXPECTED_GATES - declared
        self.assertFalse(
            missing,
            f"GATE_POLICY.yaml is missing required gates: {sorted(missing)}. "
            f"Declared: {sorted(declared)}",
        )

    def test_high_risk_output_in_reports_fails_risk_gate(self):
        wrong_path = Path("outputs/reports/E2E_smoke.md")
        passed, reason = gate_risk(DUMMY_TASK, wrong_path)
        self.assertFalse(passed)
        self.assertIn("drafts/", reason)

    def test_schema_gate_rejects_missing_dod(self):
        bad = {**DUMMY_TASK, "definition_of_done": []}
        passed, output = gate_schema(bad, VALIDATE_SCRIPT)
        self.assertFalse(passed)
        self.assertIn("definition_of_done", output)


if __name__ == "__main__":
    unittest.main()
