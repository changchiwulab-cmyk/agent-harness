#!/usr/bin/env python3
"""PostToolUse hook: auto-capture each tool call into a per-session JSONL log.

Closes observability gaps C1/C2: instead of reconstructing tool usage from
hand-written audit YAML, this records every tool call as it happens
(name, target, outcome, timestamp) to ``logs/runs/session-<id>.jsonl``.
``governance_metrics.py`` consumes these for real (not estimated) tool counts.

Contract: this hook must NEVER block a tool call. Any error is swallowed and the
process exits 0 — observability is best-effort and must not break the harness.
The JSONL files are gitignored (runtime artifacts), so they never cause CI drift.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "logs" / "runs"


def target_of(tool_name: str, tool_input: dict) -> str:
    """Best-effort human-readable target for the call (command / path / query)."""
    if not isinstance(tool_input, dict):
        return ""
    if tool_name in ("Bash", "bash"):
        return (tool_input.get("command") or tool_input.get("cmd") or "")[:200]
    for key in ("file_path", "notebook_path", "path", "pattern", "query", "url"):
        if tool_input.get(key):
            return str(tool_input[key])[:200]
    return ""


def outcome_of(tool_response) -> str:
    """Map the tool response into ok / error / unknown without assuming a schema."""
    if isinstance(tool_response, dict):
        if tool_response.get("error") or tool_response.get("is_error"):
            return "error"
        if "success" in tool_response:
            return "ok" if tool_response["success"] else "error"
        return "ok"
    return "unknown"


def build_record(payload: dict) -> dict:
    tool_name = payload.get("tool_name") or payload.get("name") or "unknown"
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    # PostToolUse fires after success; PostToolUseFailure fires after a failed call.
    # The recorder is registered for both so failures aren't dropped from the metric.
    event = payload.get("hook_event_name") or payload.get("hook_event") or "PostToolUse"
    outcome = "error" if event == "PostToolUseFailure" else outcome_of(payload.get("tool_response"))
    return {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "session_id": payload.get("session_id") or "unknown",
        "event": event,
        "tool": tool_name,
        "target": target_of(tool_name, tool_input),
        "outcome": outcome,
    }


def session_file(session_id: str) -> Path:
    safe = "".join(c for c in str(session_id) if c.isalnum() or c in "-_")[:40] or "unknown"
    return RUNS_DIR / f"session-{safe}.jsonl"


def main() -> int:
    try:
        raw = sys.stdin.read().strip()
        if not raw:
            return 0
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            return 0
        record = build_record(payload)
        RUNS_DIR.mkdir(parents=True, exist_ok=True)
        with session_file(record["session_id"]).open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        # Best-effort only: never break a tool call because logging failed.
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
