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

import governance_metrics as gm

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


def collect_tasks(root: Path) -> list[dict[str, Any]]:
    items = []
    for p in sorted(root.glob(TASKS_GLOB)):
        if not p.is_file():
            continue
        doc = load_yaml(p)
        items.append({"path": rel(p, root), **pick(doc, TASK_FIELDS)})
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


def build_governance_alerts(tasks: list[dict[str, Any]], root: Path) -> list[dict[str, Any]]:
    """R14: snapshot of governance_metrics M2-M4 for the dashboard (R7 reinforcement).

    M1 (monthly task count trend) is intentionally excluded — it's a function of
    wall-clock "today", which would make data.json change on date alone and break
    the CI drift check (`generate_frontend_manifest.py --check` compares a fresh
    rebuild against the committed file with no notion of "as of which day"). M2-M4
    are pure snapshots of current repo file state, so they stay deterministic.
    M5 (open-PR backlog) is excluded for the same reason, stronger: it depends on
    live GitHub API state that a clean checkout cannot reproduce.
    """
    drafts = gm.count_dir_md_files(root / "outputs" / "drafts")
    reports = gm.count_dir_md_files(root / "outputs" / "reports")
    metrics = [
        gm.metric_m2(drafts, reports),
        gm.metric_m3(tasks, gm.load_audit_task_ids(root)),
        gm.metric_m4(gm.load_native_overlap(root)),
    ]
    return [{"id": m.id, "name": m.name, "status": m.status, "current": m.current} for m in metrics]


def build_overview(tasks: list[dict[str, Any]], logs: list[dict[str, Any]], root: Path) -> dict[str, Any]:
    """Governance overview for the dashboard panel (R7 frontend).

    Derived purely from already-collected tasks + run logs (plus the small,
    root-parameterized reads in build_governance_alerts) — distributions are
    deterministic for a given input, keeping `dump()` byte-identical (idempotent).
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
        "run_total": len(logs),
        "run_status": run_status,
        "gate_results": gate_results,
        "alerts": build_governance_alerts(tasks, root),
    }


def build(root: Path) -> dict[str, Any]:
    tasks = collect_tasks(root)
    logs = collect_logs(root)
    return {
        "tasks": tasks,
        "logs": logs,
        "decisions": collect_decisions(root),
        "overview": build_overview(tasks, logs, root),
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
