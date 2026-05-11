#!/usr/bin/env python3
"""Generate frontend/data.json from repository YAML files.

Parses tasks/, logs/runs/ and memory/active_projects/*/decisions/ with PyYAML
and writes a stable, deterministic JSON document for the static dashboard.
The output is byte-identical for identical inputs so CI can detect drift.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

import yaml

ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT / "frontend"
OUTPUT = FRONTEND_DIR / "data.json"

TASKS_GLOB = "tasks/20*.yaml"
LOGS_GLOB = "logs/runs/*.yaml"
DECISIONS_GLOB = "memory/active_projects/*/decisions/*.yaml"
ERRORS_GLOB = "logs/errors/*.md"
ERRORS_EXCLUDE = {"ERROR_LOG_TEMPLATE.md"}

TASK_FIELDS = (
    "task_id",
    "date",
    "status",
    "skill_type",
    "risk_level",
    "approval_needed",
    "goal",
)

LOG_FIELDS = (
    "run_id",
    "task_id",
    "skill_type",
    "status",
    "started_at",
    "ended_at",
    "gate_results",
    "error_summary",
)

DECISION_FIELDS = (
    "decision_id",
    "date",
    "decision",
    "reasoning",
    "status",
    "related_task",
    "revisit_trigger",
)

ERROR_FIELDS = (
    "error_id",
    "task_id",
    "date",
    "skill_type",
    "error_type",
    "error_summary",
    "failure_count",
    "related_rule",
    "resolution",
)

TAXONOMY_RE = re.compile(r"\b(?:SPEC|COORD|VAL|SEC)-\d{2}\b")
YAML_FENCE_RE = re.compile(r"```yaml\s*\n(.*?)\n```", re.DOTALL)
VALID_RISK = {"low", "medium", "high", "critical"}
VALID_SKILL = {"research", "writing", "ops", "review", "analysis"}


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def pick(doc: dict[str, Any], fields: Iterable[str]) -> dict[str, Any]:
    return {k: doc.get(k) for k in fields if k in doc}


def parse_error_markdown(text: str) -> dict[str, Any] | None:
    """Extract first ```yaml fenced block and parse as dict; return None if absent/invalid."""
    match = YAML_FENCE_RE.search(text)
    if not match:
        return None
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None
    if not isinstance(data, dict):
        return None
    return data


def collect_errors(root: Path) -> list[dict[str, Any]]:
    """Walk logs/errors/*.md, exclude template, parse, project to ERROR_FIELDS + taxonomy_codes."""
    items = []
    for p in sorted(root.glob(ERRORS_GLOB)):
        if not p.is_file():
            continue
        if p.name in ERRORS_EXCLUDE:
            continue
        if p.name == ".gitkeep":
            continue
        text = p.read_text(encoding="utf-8")
        doc = parse_error_markdown(text)
        if doc is None:
            print(f"WARNING: skipping {p.name}: no valid yaml fenced block", file=sys.stderr)
            continue
        item = {"path": rel(p, root), **pick(doc, ERROR_FIELDS)}
        # Derive taxonomy_codes from related_rule
        related_rule = doc.get("related_rule") or ""
        codes = sorted(set(TAXONOMY_RE.findall(str(related_rule))))
        item["taxonomy_codes"] = codes
        items.append(item)
    # Sort by (date desc, error_id desc) for stable output
    items.sort(key=lambda e: (e.get("date") or "", e.get("error_id") or ""), reverse=True)
    return items


def detect_task_schema_issues(doc: dict[str, Any]) -> list[str]:
    """Return list of issue codes per plan §3.3 rules. Pure function for easy testing."""
    issues = []
    goal = doc.get("goal")
    if not goal or not str(goal).strip():
        issues.append("missing_goal")

    dod = doc.get("definition_of_done")
    if (
        dod is None
        or not isinstance(dod, list)
        or len(dod) == 0
        or all(not str(item).strip() for item in dod)
    ):
        issues.append("missing_dod")

    risk_level = doc.get("risk_level")
    if risk_level not in VALID_RISK:
        issues.append("invalid_risk_level")

    skill_type = doc.get("skill_type")
    if skill_type not in VALID_SKILL:
        issues.append("invalid_skill_type")

    status = doc.get("status")
    if status == "failed":
        issues.append("task_failed")
    elif status == "blocked":
        issues.append("task_blocked")

    return issues


def derive_gate_failures(gate_results: dict[str, str] | None) -> tuple[bool, list[str]]:
    """Return (has_gate_failure, failed_gates)."""
    if not gate_results or not isinstance(gate_results, dict):
        return (False, [])
    gate_order = ["schema_check", "rule_check", "completion_check", "risk_check"]
    failed = [g for g in gate_order if gate_results.get(g) == "fail"]
    return (len(failed) > 0, failed)


def collect_tasks(root: Path) -> list[dict[str, Any]]:
    items = []
    for p in sorted(root.glob(TASKS_GLOB)):
        if not p.is_file():
            continue
        doc = load_yaml(p)
        item = {"path": rel(p, root), **pick(doc, TASK_FIELDS)}
        item["schema_issues"] = detect_task_schema_issues(doc)
        items.append(item)
    return items


def collect_logs(root: Path) -> list[dict[str, Any]]:
    items = []
    for p in sorted(root.glob(LOGS_GLOB)):
        if not p.is_file():
            continue
        doc = load_yaml(p)
        log = doc.get("execution_log") if isinstance(doc.get("execution_log"), dict) else doc
        item = {"path": rel(p, root), **pick(log, LOG_FIELDS)}
        has_gate_failure, failed_gates = derive_gate_failures(item.get("gate_results"))
        item["has_gate_failure"] = has_gate_failure
        item["failed_gates"] = failed_gates
        items.append(item)
    return items


def collect_decisions(root: Path) -> list[dict[str, Any]]:
    items = []
    for p in sorted(root.glob(DECISIONS_GLOB)):
        if not p.is_file():
            continue
        doc = load_yaml(p)
        items.append({
            "path": rel(p, root),
            "project": p.parts[p.parts.index("active_projects") + 1],
            **pick(doc, DECISION_FIELDS),
        })
    return items


def build(root: Path) -> dict[str, Any]:
    return {
        "decisions": collect_decisions(root),
        "errors": collect_errors(root),
        "logs": collect_logs(root),
        "tasks": collect_tasks(root),
    }


def dump(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    check = "--check" in args

    payload = build(ROOT)
    rendered = dump(payload)

    if check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != rendered:
            print(f"DRIFT: {OUTPUT.relative_to(ROOT)} is out of date. Re-run scripts/generate_frontend_manifest.py.", file=sys.stderr)
            return 1
        print(f"OK: {OUTPUT.relative_to(ROOT)} is up to date.")
        return 0

    OUTPUT.write_text(rendered, encoding="utf-8")
    print(f"Generated {OUTPUT.relative_to(ROOT)} ({len(payload['tasks'])} tasks, {len(payload['logs'])} logs, {len(payload['decisions'])} decisions, {len(payload['errors'])} errors)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
