#!/usr/bin/env python3
"""Generate frontend/data.json from repository YAML files.

Parses tasks/, logs/runs/ and memory/active_projects/*/decisions/ with PyYAML
and writes a stable, deterministic JSON document for the static dashboard.
The output is byte-identical for identical inputs so CI can detect drift.
"""

from __future__ import annotations

import json
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
    "model_used",
    "status",
    "started_at",
    "ended_at",
    "gate_results",
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


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def pick(doc: dict[str, Any], fields: Iterable[str]) -> dict[str, Any]:
    return {k: doc.get(k) for k in fields if k in doc}


def load_model_routing(root: Path) -> dict[str, Any]:
    """Load system/MODEL_ROUTING.yaml — single source of truth for model tiers.

    Returns {} when absent so the generator stays root-parameterized and works
    on minimal test roots that have no routing file.
    """
    path = root / "system" / "MODEL_ROUTING.yaml"
    if not path.is_file():
        return {}
    return load_yaml(path)


def task_model_tier(doc: dict[str, Any], by_skill_default: dict[str, Any]) -> str:
    """Resolve a task's model tier for the dashboard distribution.

    Precedence mirrors MODEL_ROUTING.yaml resolution_order, collapsed to a single
    label: explicit model_routing.tier > phase_overrides > skill_type default >
    'unknown'. A task whose phase_overrides span more than one distinct tier is
    labelled 'mixed' (it genuinely runs on multiple models), so multi-stage tasks
    are not silently undercounted as their skill default. Deterministic.
    """
    routing = doc.get("model_routing")
    if isinstance(routing, dict):
        if routing.get("tier"):
            return str(routing["tier"])
        overrides = routing.get("phase_overrides")
        if isinstance(overrides, dict):
            tiers = {str(v) for v in overrides.values() if v}
            if len(tiers) == 1:
                return next(iter(tiers))
            if tiers:
                return "mixed"
    skill = doc.get("skill_type")
    if skill and skill in by_skill_default:
        return str(by_skill_default[skill])
    return "unknown"


def collect_tasks(root: Path) -> list[dict[str, Any]]:
    by_skill_default = (load_model_routing(root).get("routing") or {}).get("by_skill_default") or {}
    items = []
    for p in sorted(root.glob(TASKS_GLOB)):
        if not p.is_file():
            continue
        doc = load_yaml(p)
        item = {"path": rel(p, root), **pick(doc, TASK_FIELDS)}
        item["model_tier"] = task_model_tier(doc, by_skill_default)
        items.append(item)
    return items


def collect_logs(root: Path) -> list[dict[str, Any]]:
    items = []
    for p in sorted(root.glob(LOGS_GLOB)):
        if not p.is_file():
            continue
        doc = load_yaml(p)
        log = doc.get("execution_log") if isinstance(doc.get("execution_log"), dict) else doc
        items.append({"path": rel(p, root), **pick(log, LOG_FIELDS)})
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


OVERVIEW_GATES = ("schema_check", "rule_check", "completion_check", "risk_check")


def _tally(items: list[dict[str, Any]], key: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for it in items:
        v = it.get(key) or "unknown"
        out[v] = out.get(v, 0) + 1
    return out


def build_overview(tasks: list[dict[str, Any]], logs: list[dict[str, Any]]) -> dict[str, Any]:
    """Governance overview for the dashboard panel (R7 frontend).

    Derived purely from already-collected tasks + run logs — no extra file reads,
    so it stays root-parameterized and cheap. Distributions are deterministic for
    a given input, keeping `dump()` byte-identical (idempotent).
    """
    gate_results: dict[str, dict] = {g: {} for g in OVERVIEW_GATES}
    run_status: dict[str, int] = {}
    for log in logs:
        st = log.get("status") or "unknown"
        run_status[st] = run_status.get(st, 0) + 1
        gr = log.get("gate_results") or {}
        if isinstance(gr, dict):
            for g in OVERVIEW_GATES:
                v = gr.get(g)
                if v is not None:
                    gate_results[g][v] = gate_results[g].get(v, 0) + 1
    return {
        "task_total": len(tasks),
        "task_status": _tally(tasks, "status"),
        "task_skill": _tally(tasks, "skill_type"),
        "task_risk": _tally(tasks, "risk_level"),
        "task_model": _tally(tasks, "model_tier"),
        "run_total": len(logs),
        "run_status": run_status,
        "run_model": _tally(logs, "model_used"),
        "gate_results": gate_results,
    }


def build(root: Path) -> dict[str, Any]:
    tasks = collect_tasks(root)
    logs = collect_logs(root)
    return {
        "tasks": tasks,
        "logs": logs,
        "decisions": collect_decisions(root),
        "overview": build_overview(tasks, logs),
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
    print(f"Generated {OUTPUT.relative_to(ROOT)} ({len(payload['tasks'])} tasks, {len(payload['logs'])} logs, {len(payload['decisions'])} decisions)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
