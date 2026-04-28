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

SYSTEM_META_FILES = (
    "system/GATE_POLICY.yaml",
    "system/APPROVAL_POLICY.yaml",
    "system/FAILURE_TAXONOMY.yaml",
)

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
    "approvals",
    "tools_used",
    "checkpoints",
    "token_estimate",
    "error_summary",
    "notes",
)

DECISION_FIELDS = (
    "decision_id",
    "date",
    "decision",
    "reasoning",
    "status",
    "related_task",
    "revisit_trigger",
    "options_considered",
    "risk",
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


def collect_system_meta(root: Path) -> dict[str, Any]:
    """Load full system policy files for read-only reference in the frontend.

    Files are loaded as-is (no field whitelist) so the dashboard can render
    Gate descriptions, Failure Taxonomy categories, etc. without re-parsing
    YAML on the client side.
    """
    meta: dict[str, Any] = {}
    for rel_path in SYSTEM_META_FILES:
        p = root / rel_path
        if not p.is_file():
            continue
        key = Path(rel_path).stem.lower()
        meta[key] = load_yaml(p)
    return meta


def build(root: Path) -> dict[str, Any]:
    return {
        "tasks": collect_tasks(root),
        "logs": collect_logs(root),
        "decisions": collect_decisions(root),
        "system_meta": collect_system_meta(root),
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
