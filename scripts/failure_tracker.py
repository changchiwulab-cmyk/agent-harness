#!/usr/bin/env python3
"""Failure Tracker — make the "stop after 3 consecutive failures" hard rule real
(workflow plan R12).

CLAUDE.md rule #3 ("連續失敗 3 次就停下來") and FAILURE_TAXONOMY SEC-03 / SPEC-02
were prompt-level only: nothing actually counted failures or forced a halt. This
script keeps a small persistent counter (logs/.failure_state.json). When three
consecutive failures accumulate it trips a circuit breaker: it writes a durable
error log under logs/errors/ and returns a non-zero exit code so the flow stops
instead of grinding on.

Subcommands:
    record-failure --task-id X [--error-type T] [--summary S]   # +1; trips at threshold
    record-success [--task-id X]                                # reset counter to 0
    check                                                        # non-zero exit if tripped
    status                                                       # print current state
    reset                                                        # force reset to 0

Exit code:
    0 = below threshold / ok
    1 = threshold reached → STOP (circuit breaker tripped)
    2 = usage / IO error
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STATE_PATH = ROOT / "logs" / ".failure_state.json"
DEFAULT_ERRORS_DIR = ROOT / "logs" / "errors"
THRESHOLD = 3  # CLAUDE.md hard rule #3: stop after 3 consecutive failures
VALID_ERROR_TYPES = {"tool_failure", "rule_violation", "schema_failure", "timeout", "unknown"}


# --- State -----------------------------------------------------------------


def empty_state() -> dict:
    return {"consecutive_failures": 0, "last_task_id": "", "last_failure_at": "", "history": []}


def load_state(path: Path) -> dict:
    if not path.exists():
        return empty_state()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return empty_state()
    base = empty_state()
    if isinstance(data, dict):
        base.update({k: data.get(k, base[k]) for k in base})
    return base


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# --- Transitions -----------------------------------------------------------


def record_failure(state: dict, task_id: str, error_type: str, summary: str, now: datetime) -> dict:
    state["consecutive_failures"] = int(state.get("consecutive_failures", 0)) + 1
    state["last_task_id"] = task_id or state.get("last_task_id", "")
    state["last_failure_at"] = now.strftime("%Y-%m-%d %H:%M")
    history = state.setdefault("history", [])
    history.append({
        "task_id": task_id,
        "error_type": error_type if error_type in VALID_ERROR_TYPES else "unknown",
        "summary": summary,
        "at": state["last_failure_at"],
    })
    # Keep history bounded — only the current streak matters for diagnosis.
    state["history"] = history[-THRESHOLD:]
    return state


def record_success(state: dict, task_id: str) -> dict:
    state["consecutive_failures"] = 0
    state["history"] = []
    if task_id:
        state["last_task_id"] = task_id
    return state


def tripped(state: dict, threshold: int = THRESHOLD) -> bool:
    return int(state.get("consecutive_failures", 0)) >= threshold


# --- Circuit-breaker error log ---------------------------------------------


def render_error_log(state: dict, now: datetime) -> str:
    """Emit an ERROR_LOG_TEMPLATE-shaped record so the trip leaves a durable trace."""
    task_id = state.get("last_task_id", "") or "(unknown)"
    streak = state.get("history", [])
    types = sorted({h.get("error_type", "unknown") for h in streak}) or ["unknown"]
    summaries = "；".join(h.get("summary", "") for h in streak if h.get("summary"))
    err_type = types[0] if len(types) == 1 else "unknown"
    body = {
        "error_id": f"ERR-{now.strftime('%Y%m%d')}-CB",
        "task_id": task_id,
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M"),
        "skill_type": "ops",
        "error_type": err_type,
        "error_summary": f"連續失敗達 {state.get('consecutive_failures', 0)} 次，circuit breaker 觸發停止"
                         + (f"；失敗摘要：{summaries}" if summaries else ""),
        "failure_count": int(state.get("consecutive_failures", 0)),
        "last_action": (streak[-1].get("summary", "") if streak else ""),
        "root_cause": "連續失敗達門檻（CLAUDE.md 硬規則 3：連續失敗 3 次就停下來）",
        "attempted_fixes": [h.get("summary", "") for h in streak if h.get("summary")] or ["(無紀錄)"],
        "related_rule": "CLAUDE.md 硬規則 #3；FAILURE_TAXONOMY SEC-03 成本失控 / SPEC-02 步驟重複",
        "resolution": "stopped",
        "user_notified": True,
        "follow_up": "由人工檢視失敗串並決定是否重啟；重啟前以 failure_tracker reset 歸零計數",
    }
    yaml_lines = []
    for k, v in body.items():
        if isinstance(v, list):
            yaml_lines.append(f"{k}:")
            for item in v:
                yaml_lines.append(f"  - {json.dumps(item, ensure_ascii=False)}")
        elif isinstance(v, bool):
            yaml_lines.append(f"{k}: {str(v).lower()}")
        elif isinstance(v, int):
            yaml_lines.append(f"{k}: {v}")
        else:
            yaml_lines.append(f"{k}: {json.dumps(v, ensure_ascii=False)}")
    yaml_block = "\n".join(yaml_lines)
    return (
        f"# Error Log — {task_id} circuit breaker（連續失敗 {body['failure_count']} 次自動停止）\n\n"
        f"> 由 scripts/failure_tracker.py 自動寫入：連續失敗達門檻，circuit breaker 觸發。\n\n"
        f"```yaml\n{yaml_block}\n```\n"
    )


def write_circuit_breaker_error_log(errors_dir: Path, state: dict, now: datetime) -> Path:
    errors_dir.mkdir(parents=True, exist_ok=True)
    task_id = (state.get("last_task_id") or "unknown").replace("/", "_")
    out = errors_dir / f"{now.strftime('%Y-%m-%d')}_{task_id}_circuit-breaker.md"
    out.write_text(render_error_log(state, now), encoding="utf-8")
    return out


# --- Main ------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Track consecutive failures (R12 circuit breaker).")
    parser.add_argument("command", choices=["record-failure", "record-success", "check", "status", "reset"])
    parser.add_argument("--task-id", default="")
    parser.add_argument("--error-type", default="unknown")
    parser.add_argument("--summary", default="")
    parser.add_argument("--threshold", type=int, default=THRESHOLD)
    parser.add_argument("--state", default=str(DEFAULT_STATE_PATH))
    parser.add_argument("--errors-dir", default=str(DEFAULT_ERRORS_DIR))
    parser.add_argument("--now", default="", help="ISO datetime override (testing).")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    state_path = Path(args.state)
    now = datetime.fromisoformat(args.now) if args.now else datetime.now()

    try:
        state = load_state(state_path)

        if args.command == "record-failure":
            record_failure(state, args.task_id, args.error_type, args.summary, now)
        elif args.command == "record-success":
            record_success(state, args.task_id)
        elif args.command == "reset":
            state = empty_state()

        if args.command in ("record-failure", "record-success", "reset"):
            save_state(state_path, state)

        is_tripped = tripped(state, args.threshold)
        error_log_path = None
        if args.command == "record-failure" and is_tripped:
            error_log_path = write_circuit_breaker_error_log(Path(args.errors_dir), state, now)
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    result = {
        "command": args.command,
        "consecutive_failures": state.get("consecutive_failures", 0),
        "threshold": args.threshold,
        "tripped": is_tripped,
        "last_task_id": state.get("last_task_id", ""),
    }
    if error_log_path is not None:
        result["error_log"] = str(error_log_path.relative_to(ROOT)) if error_log_path.is_relative_to(ROOT) else str(error_log_path)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"[failure_tracker] {args.command}: {result['consecutive_failures']}/{args.threshold} "
              f"consecutive failures (tripped={is_tripped})")
        if is_tripped:
            print("🚨 STOP: 連續失敗達門檻，circuit breaker 觸發。請人工檢視後再以 reset 歸零。", file=sys.stderr)
            if error_log_path is not None:
                print(f"   error log: {result.get('error_log')}", file=sys.stderr)

    return 1 if is_tripped else 0


if __name__ == "__main__":
    raise SystemExit(main())
