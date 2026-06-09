#!/usr/bin/env python3
"""Generate frontend/data.json from repository YAML files.

Parses tasks/, logs/runs/ and memory/active_projects/*/decisions/ with PyYAML
and writes a stable, deterministic JSON document for the static dashboard.
The output is byte-identical for identical inputs so CI can detect drift.
"""

from __future__ import annotations

import json
import math
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
        "run_total": len(logs),
        "run_status": run_status,
        "gate_results": gate_results,
    }


CONTEXT_BUDGET_FILES = ("CLAUDE.md", "system/GLOBAL_RULES.md")
CONTEXT_TOKEN_BUDGET = 3000
SKILL_GLOB = "skills/*/SKILL.md"
SKILL_TOKEN_BUDGET = 1500
ASCII_CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    """Token estimate, byte-for-byte consistent with scripts/check_context_budget.rb.

    Formula: ASCII chars / 4 + non-ASCII chars × 1, then ceil. Keeping it identical
    to the Ruby gate means the dashboard and the CI budget check never disagree.
    """
    ascii_count = sum(1 for ch in text if ord(ch) < 128)
    non_ascii = len(text) - ascii_count
    return math.ceil(ascii_count / ASCII_CHARS_PER_TOKEN + non_ascii)


def build_budget(root: Path) -> dict[str, Any]:
    """Context-budget panel data (R-roadmap Phase 2 frontend).

    Derived from on-disk prompt files with the same estimator as the Ruby gate.
    Missing files are skipped, so an empty repo yields empty collections and the
    output stays root-parameterized + deterministic (idempotent).
    """
    ctx_files: list[dict[str, Any]] = []
    ctx_total = 0
    for rel_path in CONTEXT_BUDGET_FILES:
        p = root / rel_path
        if not p.is_file():
            continue
        tokens = estimate_tokens(p.read_text(encoding="utf-8"))
        ctx_files.append({"path": rel_path, "tokens": tokens})
        ctx_total += tokens

    skills: list[dict[str, Any]] = []
    for p in sorted(root.glob(SKILL_GLOB)):
        if not p.is_file():
            continue
        skills.append({"path": rel(p, root), "tokens": estimate_tokens(p.read_text(encoding="utf-8"))})

    return {
        "context": {"budget": CONTEXT_TOKEN_BUDGET, "total": ctx_total, "files": ctx_files},
        "skills": {"budget": SKILL_TOKEN_BUDGET, "items": skills},
    }


def build(root: Path) -> dict[str, Any]:
    tasks = collect_tasks(root)
    logs = collect_logs(root)
    return {
        "tasks": tasks,
        "logs": logs,
        "decisions": collect_decisions(root),
        "overview": build_overview(tasks, logs),
        "budget": build_budget(root),
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
