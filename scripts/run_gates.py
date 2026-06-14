#!/usr/bin/env python3
"""Executable four-layer gate runner — codifies GATE_POLICY.yaml (gap B4).

GATE_POLICY.yaml describes four gates (schema → rule → completion → risk) as a
prose checklist the LLM is expected to follow. This script makes them runnable so
they can be enforced in CI and from a Stop hook, instead of relying on the model
to remember.

Usage:
    python3 scripts/run_gates.py <task_card.yaml> [--output <produced_file>] [--json]

Exit code: 0 = all gates pass/skip, 1 = at least one gate fails, 2 = load error.

Gate verdicts: "pass" / "fail" / "skip" (skip = cannot evaluate without runtime
artefacts, e.g. completion_check with no --output supplied).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PERMISSIONS_PATH = ROOT / "system" / "PERMISSIONS.yaml"

# Reuse the existing schema validator rather than re-implementing it.
sys.path.insert(0, str(ROOT / "system"))
import validate_task_card  # noqa: E402

GATE_ORDER = ("schema_check", "rule_check", "completion_check", "risk_check")
HIGH_RISK = {"high", "critical"}


def gate_schema(card_path: Path) -> tuple[str, str]:
    """Gate 1 — Task Card field/format validity (reuses validate_task_card.validate)."""
    errors = validate_task_card.validate(str(card_path))
    if errors:
        return "fail", "; ".join(errors)
    return "pass", "schema ok"


def _load_deny() -> set[str]:
    try:
        perms = yaml.safe_load(PERMISSIONS_PATH.read_text(encoding="utf-8"))
        return set(perms["permissions"]["deny"])
    except Exception:
        return set()


def gate_rule(card: dict) -> tuple[str, str]:
    """Gate 2 — allowed_tools whitelist present and clear of the deny list."""
    tools = card.get("allowed_tools") or []
    if not isinstance(tools, list) or not tools:
        return "fail", "allowed_tools must be a non-empty whitelist"
    deny = _load_deny()
    bad = [t for t in tools if t in deny]
    if bad:
        return "fail", f"allowed_tools overlap deny list: {bad}"
    mtc = card.get("max_tool_calls")
    if mtc is not None and (not isinstance(mtc, int) or mtc <= 0):
        return "fail", f"max_tool_calls must be a positive int, got {mtc!r}"
    return "pass", "rule ok"


def gate_completion(card: dict, output: Path | None) -> tuple[str, str]:
    """Gate 3 — definition_of_done present; if an output is given, each line is checked."""
    dod = card.get("definition_of_done") or []
    if not isinstance(dod, list) or not dod:
        return "fail", "definition_of_done is empty"
    if output is None:
        return "skip", "no --output supplied; structural DoD ok, runtime check deferred"
    if not output.exists():
        return "fail", f"output not produced: {output}"
    body = output.read_text(encoding="utf-8", errors="ignore")
    misses = [d for d in dod if isinstance(d, str) and d and d not in body]
    if misses:
        return "fail", f"DoD lines not evidenced in output: {misses}"
    return "pass", "all DoD lines evidenced"


def gate_risk(card: dict, output: Path | None) -> tuple[str, str]:
    """Gate 4 — high/critical output must live under outputs/drafts/, never reports/."""
    if card.get("risk_level") not in HIGH_RISK:
        return "pass", "risk below high; no drafts constraint"
    location = (card.get("expected_output") or {}).get("location", "")
    declared_ok = "outputs/drafts" in str(location)
    if not declared_ok:
        return "fail", f"high-risk expected_output.location must be outputs/drafts/, got {location!r}"
    if output is not None and "outputs/drafts/" not in output.as_posix():
        return "fail", f"high-risk output must be in drafts/, got {output}"
    return "pass", "high-risk output constrained to drafts/"


def run_gates(card_path: Path, output: Path | None) -> dict[str, tuple[str, str]]:
    try:
        card = yaml.safe_load(card_path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise SystemExit(f"ERROR: cannot load {card_path}: {exc}")
    if not isinstance(card, dict):
        raise SystemExit(f"ERROR: {card_path} root is not a mapping")
    return {
        "schema_check": gate_schema(card_path),
        "rule_check": gate_rule(card),
        "completion_check": gate_completion(card, output),
        "risk_check": gate_risk(card, output),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the four GATE_POLICY gates on a Task Card.")
    parser.add_argument("task_card", help="path to the Task Card YAML")
    parser.add_argument("--output", help="path to the produced output artefact (enables completion/risk runtime checks)")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = parser.parse_args(argv)

    card_path = Path(args.task_card)
    if not card_path.exists():
        print(f"ERROR: task card not found: {card_path}", file=sys.stderr)
        return 2
    output = Path(args.output) if args.output else None

    results = run_gates(card_path, output)
    failed = [g for g in GATE_ORDER if results[g][0] == "fail"]

    if args.json:
        print(json.dumps({g: {"status": s, "detail": d} for g, (s, d) in results.items()},
                         ensure_ascii=False, indent=2))
    else:
        print(f"Gate run: {card_path}")
        for g in GATE_ORDER:
            status, detail = results[g]
            badge = {"pass": "✅", "fail": "❌", "skip": "⏭️"}[status]
            print(f"  {badge} {g}: {status} — {detail}")
        print(f"Result: {'FAIL' if failed else 'PASS'}" + (f" ({', '.join(failed)})" if failed else ""))

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
