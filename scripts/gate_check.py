#!/usr/bin/env python3
"""Gate Verifier — automate GATE_POLICY.yaml's four layers post-execution.

The harness's own self-assessment (§3.6) flagged that of GATE_POLICY's four
gates, only layer 1 (schema) was automated (system/validate_task_card.py); the
rule / completion / risk layers ran purely through Claude's natural-language
reasoning at runtime. This script makes the other three checkable from a Task
Card (+ its optional execution log under logs/runs/).

Layers (mirrors GATE_POLICY.yaml + tests/e2e/test_dummy_task_smoke.py):
    L1 schema_check     — reuse system/validate_task_card.py validate()
    L2 rule_check       — run log's tools_used ⊆ Task Card allowed_tools
    L3 completion_check — the promised expected_output artifact exists
    L4 risk_check       — risk_level high/critical ⇒ output under outputs/drafts/

Honest degradation: not every layer is statically decidable.
    - L2 needs an execution log (logs/runs/*.yaml). Absent ⇒ "skipped".
    - L3 free-text DoD lines need human/LLM judgement; this script verifies the
      deterministic proxy (the artifact was produced) and lists DoD for review.
    - L4 is "n/a" for low/medium risk.
"skipped" / "n/a" never fail the run; only L1/L2/L3/L4 verdict == "fail" does.

Exit code:
    0 = all runnable gates passed
    1 = at least one gate failed
    2 = collection error (task card not found, parse error)

Usage:
    python3 scripts/gate_check.py 20260609-001            # by task_id
    python3 scripts/gate_check.py --card tasks/x.yaml     # by path
    python3 scripts/gate_check.py 20260609-001 --json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

# Reuse the schema validator (gate L1) rather than reimplementing it.
sys.path.insert(0, str(ROOT / "system"))
import validate_task_card  # noqa: E402

PASS, FAIL, SKIPPED, NA = "pass", "fail", "skipped", "n/a"

# Statuses at which the promised output is expected to already exist on disk.
_OUTPUT_EXPECTED_STATUS = {"done", "review"}
_RUN_DONE_STATUS = {"completed", "done", "review"}


@dataclass
class GateReport:
    task_id: str
    card_path: str
    run_log_path: str | None
    results: dict = field(default_factory=dict)   # gate_name -> {status, detail}

    @property
    def gate_results(self) -> dict:
        """The EXECUTION_LOG_SCHEMA-shaped gate_results block."""
        return {name: r["status"] for name, r in self.results.items()}

    @property
    def failed(self) -> bool:
        return any(r["status"] == FAIL for r in self.results.values())


# --- Loaders ---------------------------------------------------------------


def find_card(task_id: str, root: Path) -> Path | None:
    """Locate the Task Card whose task_id matches, under <root>/tasks/."""
    for path in sorted((root / "tasks").rglob("*.yaml")):
        if "TEMPLATE" in path.name:
            continue
        try:
            card = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            continue
        if isinstance(card, dict) and card.get("task_id") == task_id:
            return path
    return None


def find_run_log(task_id: str, root: Path) -> tuple[Path | None, dict | None]:
    """Locate an execution log under <root>/logs/runs/ for this task_id."""
    runs_dir = root / "logs" / "runs"
    if not runs_dir.exists():
        return None, None
    for path in sorted(runs_dir.glob("*.yaml")):
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            continue
        if not isinstance(doc, dict):
            continue
        log = doc.get("execution_log", doc)
        if isinstance(log, dict) and log.get("task_id") == task_id:
            return path, log
    return None, None


# --- Gates -----------------------------------------------------------------


def gate_schema(card_path: Path) -> dict:
    """L1: reuse validate_task_card.validate() — same path the runtime uses."""
    errors = validate_task_card.validate(str(card_path))
    if errors:
        return {"status": FAIL, "detail": "; ".join(errors)}
    return {"status": PASS, "detail": "schema valid"}


def gate_rule(card: dict, run_log: dict | None) -> dict:
    """L2: every tool actually used must be in the card's allowed_tools.

    Requires an execution log; without one there is nothing to check.
    """
    if not run_log:
        return {"status": SKIPPED, "detail": "no execution log under logs/runs/"}
    allowed = set(card.get("allowed_tools") or [])
    used = []
    for entry in run_log.get("tools_used") or []:
        if isinstance(entry, dict) and entry.get("tool"):
            used.append(entry["tool"])
    violations = [t for t in used if t not in allowed]
    if violations:
        return {
            "status": FAIL,
            "detail": f"tools used outside allowed_tools: {sorted(set(violations))}",
        }
    return {"status": PASS, "detail": f"all {len(used)} used tool(s) whitelisted"}


def gate_completion(card: dict, root: Path) -> dict:
    """L3: the promised output artifact exists (deterministic proxy).

    Free-text definition_of_done lines need human/LLM judgement, so this gate
    verifies the artifact was produced and surfaces the DoD list for review.
    """
    status = card.get("status", "")
    out = card.get("expected_output") or {}
    location = (out.get("location") or "").strip()
    filename = (out.get("filename") or "").strip()
    dod = card.get("definition_of_done") or []
    if not location or not filename:
        return {"status": FAIL, "detail": "expected_output.location/filename missing"}
    artifact = root / location.rstrip("/") / filename
    if status in _OUTPUT_EXPECTED_STATUS and not artifact.exists():
        return {
            "status": FAIL,
            "detail": f"status={status} but promised output not found: {location}{filename}",
        }
    if not artifact.exists():
        # Not yet expected (pending/in_progress) — plumbing OK, nothing produced.
        return {"status": SKIPPED, "detail": f"output not yet produced (status={status})"}
    return {
        "status": PASS,
        "detail": f"artifact present; {len(dod)} DoD line(s) need manual verdict",
    }


def gate_risk(card: dict, run_log: dict | None) -> dict:
    """L4: high/critical risk output must land in outputs/drafts/, not reports/."""
    if card.get("risk_level") not in ("high", "critical"):
        return {"status": NA, "detail": "risk_level below high"}
    paths = []
    out = card.get("expected_output") or {}
    if out.get("location"):
        paths.append(out["location"])
    if run_log and run_log.get("output_path"):
        paths.append(run_log["output_path"])
    bad = [p for p in paths if "outputs/drafts/" not in Path(p).as_posix().rstrip("/") + "/"]
    if bad:
        return {"status": FAIL, "detail": f"high-risk output must be in drafts/, got {bad}"}
    return {"status": PASS, "detail": "high-risk output confined to drafts/"}


def check_card(card_path: Path, root: Path) -> GateReport:
    """Run all four gates against a single Task Card path."""
    card = yaml.safe_load(card_path.read_text(encoding="utf-8")) or {}
    task_id = card.get("task_id", "")
    run_log_path, run_log = find_run_log(task_id, root) if task_id else (None, None)
    report = GateReport(
        task_id=task_id,
        card_path=str(card_path),
        run_log_path=str(run_log_path) if run_log_path else None,
    )
    report.results["schema_check"] = gate_schema(card_path)
    report.results["rule_check"] = gate_rule(card, run_log)
    report.results["completion_check"] = gate_completion(card, root)
    report.results["risk_check"] = gate_risk(card, run_log)
    return report


# --- Rendering / CLI -------------------------------------------------------


def render_markdown(report: GateReport) -> str:
    icon = {PASS: "✅", FAIL: "❌", SKIPPED: "➖", NA: "—"}
    lines = [
        f"# Gate Check — {report.task_id}",
        "",
        f"- card: `{report.card_path}`",
        f"- run log: `{report.run_log_path or 'none'}`",
        "",
        "| Gate | Status | Detail |",
        "|------|--------|--------|",
    ]
    for name, r in report.results.items():
        lines.append(f"| {name} | {icon.get(r['status'], '?')} {r['status']} | {r['detail']} |")
    lines.append("")
    lines.append(f"**Verdict:** {'FAIL' if report.failed else 'PASS'}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GATE_POLICY four-layer validator")
    parser.add_argument("task_id", nargs="?", help="Task Card task_id, e.g. 20260609-001")
    parser.add_argument("--card", help="path to a Task Card YAML (overrides task_id lookup)")
    parser.add_argument("--root", default=str(ROOT), help="repo root (for tests)")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of markdown")
    args = parser.parse_args(argv)

    root = Path(args.root)
    if args.card:
        card_path = Path(args.card)
        if not card_path.exists():
            print(f"ERROR: card not found: {card_path}", file=sys.stderr)
            return 2
    elif args.task_id:
        card_path = find_card(args.task_id, root)
        if card_path is None:
            print(f"ERROR: no Task Card with task_id={args.task_id}", file=sys.stderr)
            return 2
    else:
        parser.error("provide a task_id or --card")

    try:
        report = check_card(card_path, root)
    except yaml.YAMLError as e:
        print(f"ERROR: parse failure: {e}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(
            {
                "task_id": report.task_id,
                "card_path": report.card_path,
                "run_log_path": report.run_log_path,
                "gate_results": report.gate_results,
                "results": report.results,
                "verdict": "fail" if report.failed else "pass",
            },
            ensure_ascii=False,
            indent=2,
        ))
    else:
        print(render_markdown(report))

    return 1 if report.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
