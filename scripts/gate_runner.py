#!/usr/bin/env python3
"""Gate Runner — turn GATE_POLICY.yaml's four-layer checklist into an executable
post-execution validator (workflow plan R11).

Until now the four gates (schema / rule / completion / risk) defined in
system/GATE_POLICY.yaml were a *prompt checklist* the agent ran by self-discipline.
This script re-runs them deterministically against a completed task — a task card
plus its run log plus the produced output — so a violation surfaces as a non-zero
exit code instead of relying on the model to police itself (self-assessment §四.1:
"no post-execution validation script").

Re-checking is independent: the verdict here can differ from the value recorded in
a run log's ``gate_results``. e.g. the R5 failure drill (RUN-20260529-003) recorded
schema_check=fail because a *broken fixture* was the subject; re-validating that
run's actual task card passes schema. That divergence is the point — gate_runner is
a cross-check, not a transcriber.

Usage:
    python scripts/gate_runner.py --run-log logs/runs/RUN-XXXX.yaml
    python scripts/gate_runner.py --task-card tasks/your-task.yaml   # schema gate only
    python scripts/gate_runner.py --all                              # every run log
    python scripts/gate_runner.py --run-log ... --json

Exit code:
    0 = all run gates pass
    1 = at least one gate failed
    2 = collection error (missing file, unparseable YAML)
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = ROOT / "tasks"
RUNS_DIR = ROOT / "logs" / "runs"
SYSTEM_DIR = ROOT / "system"
PERMISSIONS_PATH = SYSTEM_DIR / "PERMISSIONS.yaml"
DRAFTS_PREFIX = "outputs/drafts/"

# Reuse the single source of truth for schema validation instead of re-implementing it.
sys.path.insert(0, str(SYSTEM_DIR))
import validate_task_card  # noqa: E402  (path insert must precede import)

GATE_ORDER = ("schema_check", "rule_check", "completion_check", "risk_check")
HIGH_RISK = {"high", "critical"}
CHECKPOINT_TOOL_THRESHOLD = 5  # GATE_POLICY rule_check: >5 tool calls require a checkpoint


@dataclass
class GateResult:
    name: str
    status: str                       # pass / fail / skip
    reason: str = ""
    details: dict = field(default_factory=dict)


# --- Loaders ---------------------------------------------------------------


def load_run_log(path: Path) -> dict:
    """Return the execution_log dict (unwraps the ``execution_log:`` top key)."""
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        raise ValueError(f"{path}: run log is not a mapping")
    log = doc.get("execution_log") if isinstance(doc.get("execution_log"), dict) else doc
    return log


def load_task_card(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: task card is not a mapping")
    return data


def find_task_card(task_id: str) -> Path | None:
    """Locate the task card whose ``task_id`` field equals ``task_id``."""
    if not task_id:
        return None
    for p in sorted(TASKS_DIR.glob("*.yaml")):
        if p.name in {"TASK_CARD_TEMPLATE.yaml", "DECISION_LOG_TEMPLATE.yaml"}:
            continue
        try:
            data = yaml.safe_load(p.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            continue
        if isinstance(data, dict) and data.get("task_id") == task_id:
            return p
    return None


def load_deny_actions() -> set[str]:
    if not PERMISSIONS_PATH.exists():
        return set()
    data = yaml.safe_load(PERMISSIONS_PATH.read_text(encoding="utf-8")) or {}
    deny = (data.get("permissions") or {}).get("deny") or []
    return {str(x) for x in deny}


# --- Gates -----------------------------------------------------------------


def gate_schema(task_card_path: Path | None) -> GateResult:
    """Layer 1 — Task Card field completeness via system/validate_task_card.py."""
    if task_card_path is None:
        return GateResult("schema_check", "fail", "task card not found for this run")
    errors = validate_task_card.validate(str(task_card_path))
    if errors:
        return GateResult("schema_check", "fail", "; ".join(errors), {"errors": errors})
    return GateResult("schema_check", "pass", f"validated {task_card_path.name}")


def gate_rule(run_log: dict, task_card: dict, deny_actions: set[str] | None = None) -> GateResult:
    """Layer 2 — tools ⊆ allowed_tools, no deny action, checkpoint past threshold."""
    deny_actions = deny_actions if deny_actions is not None else load_deny_actions()
    tools_used = run_log.get("tools_used") or []
    used_names = [t.get("tool") for t in tools_used if isinstance(t, dict) and t.get("tool")]
    allowed = set(task_card.get("allowed_tools") or [])

    problems: list[str] = []

    out_of_whitelist = sorted(n for n in used_names if n not in allowed)
    if out_of_whitelist:
        problems.append(f"tools used outside allowed_tools whitelist: {out_of_whitelist}")

    denied = sorted(n for n in used_names if n in deny_actions)
    if denied:
        problems.append(f"tools used hit PERMISSIONS deny list: {denied}")

    total_calls = sum(
        int(t.get("call_count", 0)) for t in tools_used if isinstance(t, dict)
    )
    checkpoints = run_log.get("checkpoints") or []
    if total_calls > CHECKPOINT_TOOL_THRESHOLD and not checkpoints:
        problems.append(
            f"{total_calls} tool calls (> {CHECKPOINT_TOOL_THRESHOLD}) but no checkpoint recorded"
        )

    details = {
        "tools_used": used_names,
        "allowed_tools": sorted(allowed),
        "total_calls": total_calls,
        "checkpoints": len(checkpoints),
    }
    if problems:
        return GateResult("rule_check", "fail", "; ".join(problems), details)
    return GateResult("rule_check", "pass", "tools within whitelist, no deny, checkpoint ok", details)


def gate_completion(run_log: dict) -> GateResult:
    """Layer 3 — the declared output_path must actually exist on disk."""
    output_path = (run_log.get("output_path") or "").strip()
    if not output_path:
        return GateResult("completion_check", "fail", "output_path is empty")
    resolved = (ROOT / output_path).resolve()
    if not resolved.exists():
        return GateResult(
            "completion_check", "fail", f"output_path does not exist: {output_path}",
            {"output_path": output_path},
        )
    return GateResult("completion_check", "pass", f"output exists: {output_path}",
                      {"output_path": output_path})


def gate_risk(run_log: dict, task_card: dict) -> GateResult:
    """Layer 4 — high/critical output must be parked under outputs/drafts/."""
    risk = (task_card.get("risk_level") or "").strip().lower()
    output_path = (run_log.get("output_path") or "").strip()
    details = {"risk_level": risk, "output_path": output_path}
    if risk in HIGH_RISK and not output_path.startswith(DRAFTS_PREFIX):
        return GateResult(
            "risk_check", "fail",
            f"risk_level={risk} but output not under {DRAFTS_PREFIX}: {output_path or '(empty)'}",
            details,
        )
    return GateResult("risk_check", "pass", f"risk_level={risk or 'low'} consistent", details)


# --- Orchestration ---------------------------------------------------------


def run_all(run_log_path: Path) -> list[GateResult]:
    """Run the four gates in GATE_POLICY order; schema fail stops the rest (skip)."""
    run_log = load_run_log(run_log_path)
    task_id = run_log.get("task_id", "")
    card_path = find_task_card(task_id)

    schema = gate_schema(card_path)
    if schema.status == "fail":
        # GATE_POLICY: schema fail → stop. Subsequent gates are not run.
        return [schema] + [GateResult(g, "skip", "schema_check failed → not run")
                           for g in GATE_ORDER[1:]]

    task_card = load_task_card(card_path)  # card_path is not None when schema passed
    return [
        schema,
        gate_rule(run_log, task_card),
        gate_completion(run_log),
        gate_risk(run_log, task_card),
    ]


def overall_pass(results: list[GateResult]) -> bool:
    return all(r.status != "fail" for r in results)


# --- Reporters -------------------------------------------------------------

BADGE = {"pass": "✅ pass", "fail": "🚨 fail", "skip": "⏭️ skip"}


def render_markdown(subject: str, results: list[GateResult]) -> str:
    lines = [f"# Gate Runner — {subject}", ""]
    verdict = "✅ ALL PASS" if overall_pass(results) else "🚨 FAIL"
    lines.append(f"- 整體：**{verdict}**")
    lines.append("")
    lines.append("| gate | status | reason |")
    lines.append("|------|:------:|--------|")
    for r in results:
        lines.append(f"| {r.name} | {BADGE.get(r.status, r.status)} | {r.reason} |")
    return "\n".join(lines) + "\n"


# --- Main ------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run GATE_POLICY four-layer gates (R11).")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--run-log", type=str, help="Path to a logs/runs/*.yaml run log.")
    group.add_argument("--task-card", type=str, help="Path to a task card (schema gate only).")
    group.add_argument("--all", action="store_true", help="Run every run log under logs/runs/.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of markdown.")
    args = parser.parse_args(argv)

    try:
        if args.task_card:
            results = [gate_schema(Path(args.task_card))]
            subject = args.task_card
            batches = [(subject, results)]
        elif args.run_log:
            results = run_all(Path(args.run_log))
            batches = [(args.run_log, results)]
        else:  # --all
            run_logs = sorted(p for p in RUNS_DIR.glob("*.yaml"))
            batches = [(str(p.relative_to(ROOT)), run_all(p)) for p in run_logs]
    except (OSError, yaml.YAMLError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.json:
        payload = [
            {"subject": s, "overall_pass": overall_pass(rs), "gates": [asdict(r) for r in rs]}
            for s, rs in batches
        ]
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for s, rs in batches:
            print(render_markdown(s, rs))

    all_pass = all(overall_pass(rs) for _, rs in batches)
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
