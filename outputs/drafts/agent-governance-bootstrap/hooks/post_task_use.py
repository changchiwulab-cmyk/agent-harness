#!/usr/bin/env python3
"""PostTaskUse hook — invoked after a Task Card execution completes.

Reads task_id and produced_output_path from stdin as JSON, runs the 4-stage
gate-check via the bundled validator, and emits a structured verdict on
stdout. Non-zero exit (2) signals fail; the host runtime decides whether to
block the next step.

Behaviour:
  - schema gate: shell out to validators/validate_task_card.py
  - rule gate: ensure allowed_tools in the card don't intersect deny-list
  - completion gate: every DoD line keyword-present in produced output
  - risk gate: risk_level in {high, critical} ⇒ output path must contain "outputs/drafts/"

This is the v0.1.0 stub: it implements the contract surface so the plugin
can wire up CI smoke tests immediately. The full LLM-assisted completion
gate (semantic DoD coverage) is delegated to the host runtime.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
PLUGIN_ROOT = HERE.parent
VALIDATE_TC = PLUGIN_ROOT / "validators" / "validate_task_card.py"

EXPECTED_GATES = ("schema_check", "rule_check", "completion_check", "risk_check")


def gate_schema(card_path: Path) -> tuple[str, str]:
    if not VALIDATE_TC.exists():
        return "n/a", f"validator missing: {VALIDATE_TC}"
    result = subprocess.run(
        [sys.executable, str(VALIDATE_TC), str(card_path)],
        capture_output=True,
        text=True,
    )
    return ("pass" if result.returncode == 0 else "fail"), (result.stdout + result.stderr).strip()


def gate_rule(card: dict, deny_tools: set[str]) -> tuple[str, str]:
    bad = [t for t in (card.get("allowed_tools") or []) if t in deny_tools]
    return ("fail" if bad else "pass"), ("blocked: " + ", ".join(bad) if bad else "ok")


def gate_completion(card: dict, output_path: Path) -> tuple[str, str]:
    if not output_path or not output_path.exists():
        return "fail", "output not produced"
    body = output_path.read_text(encoding="utf-8")
    misses = [line for line in (card.get("definition_of_done") or []) if line not in body]
    if misses:
        return "warn", f"missing DoD keywords: {misses}"
    return "pass", "ok"


def gate_risk(card: dict, output_path: Path) -> tuple[str, str]:
    if card.get("risk_level") in ("high", "critical"):
        if not output_path or "outputs/drafts/" not in output_path.as_posix():
            return "fail", f"high-risk output must be in drafts/, got {output_path}"
    return "pass", "ok"


def run(task_card_path: Path, output_path: Path | None, deny_tools: set[str]) -> dict:
    if not task_card_path.exists():
        return {"verdict": "fail", "reason": f"task card not found: {task_card_path}"}
    card = yaml.safe_load(task_card_path.read_text(encoding="utf-8"))
    if not isinstance(card, dict):
        return {"verdict": "fail", "reason": "task card not a YAML mapping"}

    schema = gate_schema(task_card_path)
    rule = gate_rule(card, deny_tools)
    completion = gate_completion(card, output_path) if output_path else ("n/a", "no output path provided")
    risk = gate_risk(card, output_path) if output_path else ("n/a", "no output path provided")

    results = dict(zip(
        EXPECTED_GATES,
        [
            {"status": schema[0], "detail": schema[1]},
            {"status": rule[0], "detail": rule[1]},
            {"status": completion[0], "detail": completion[1]},
            {"status": risk[0], "detail": risk[1]},
        ],
    ))
    failed = [g for g, r in results.items() if r["status"] == "fail"]
    return {
        "task_id": card.get("task_id", ""),
        "results": results,
        "verdict": "fail" if failed else ("warn" if any(r["status"] == "warn" for r in results.values()) else "pass"),
        "failed_gates": failed,
    }


def main() -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        print(json.dumps({"verdict": "n/a", "reason": "no input"}))
        return 0
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        print(json.dumps({"verdict": "n/a", "warning": f"input not JSON: {e}"}))
        return 0

    card_path_str = payload.get("task_card_path") or ""
    output_path_str = payload.get("output_path") or ""
    deny_tools = set(payload.get("deny_tools") or [])

    if not card_path_str:
        print(json.dumps({"verdict": "n/a", "reason": "task_card_path missing"}))
        return 0

    verdict = run(Path(card_path_str), Path(output_path_str) if output_path_str else None, deny_tools)
    print(json.dumps(verdict, ensure_ascii=False))
    return 2 if verdict.get("verdict") == "fail" else (1 if verdict.get("verdict") == "warn" else 0)


if __name__ == "__main__":
    raise SystemExit(main())
