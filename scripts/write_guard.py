#!/usr/bin/env python3
"""PreToolUse hook: enforce PERMISSIONS.yaml *ask-tier* paths for file writes
(workflow plan R13).

permissions_guard.py only guards Bash deny-list commands. Nothing stopped the
agent from writing straight into ask-tier locations (system/, skills/, memory/,
outputs/reports/, CLAUDE.md), so CLAUDE.md hard rule #2 ("對外動作只產出草稿") and
the PERMISSIONS ask tier were ~30% enforced. This hook covers Write/Edit/MultiEdit:
it blocks writes to ask-tier paths by default, forcing the human-confirmation path.

Input (stdin JSON): {"tool_name": "Write", "tool_input": {"file_path": "...", ...}}
Output (stdout JSON): {"decision": "allow"} | {"decision": "block", "reason": "..."}

Design choices, consistent with permissions_guard.py:
- Deny-list-by-path, not a sandbox: anything not on the ask-tier list is allowed.
- Conservative: false positives (blocking legit work) are worse than a miss, so the
  blocked set is exactly the PERMISSIONS ask tier — no speculative paths.
- Override: an approved ask-tier change can be let through by exporting
  HARNESS_WRITE_GUARD_OVERRIDE=1 (this *is* the runtime expression of "ask → 已確認").
- Hard rule #1 ("no Task Card, no execution") is NOT enforced here: at file-write
  time there is no reliable signal of whether a task was carded. It stays prompt-level
  (documented honestly in README "Runtime 強制力").
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRITE_TOOLS = {"Write", "Edit", "MultiEdit"}
OVERRIDE_ENV = "HARNESS_WRITE_GUARD_OVERRIDE"

# Ask-tier paths from system/PERMISSIONS.yaml (permissions.ask). Writing here needs
# human confirmation, so block by default. (prefix, PERMISSIONS rule id)
ASK_DIR_PREFIXES: tuple[tuple[str, str], ...] = (
    ("system/", "modify_system_rules"),
    ("skills/", "modify_skills"),
    ("memory/", "write_long_term_memory"),
    ("outputs/reports/", "write_reports"),
)
ASK_EXACT_FILES: dict[str, str] = {
    "CLAUDE.md": "modify_claude_md",
}


def relpath(file_path: str) -> str | None:
    """Return the repo-relative POSIX path, or None if outside the repo / empty."""
    if not file_path:
        return None
    p = Path(file_path)
    try:
        if p.is_absolute():
            return p.resolve().relative_to(ROOT).as_posix()
        # Relative path → interpret against repo root.
        return (ROOT / p).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        # Outside the repo tree — not our concern.
        return None


def evaluate(file_path: str) -> tuple[str, str | None]:
    """Return ('allow', None) or ('block', reason) for a target path."""
    rel = relpath(file_path)
    if rel is None:
        return "allow", None
    if rel in ASK_EXACT_FILES:
        rule = ASK_EXACT_FILES[rel]
        return "block", f"{rule}: '{rel}' 屬 PERMISSIONS ask 級，需人工確認（或設 {OVERRIDE_ENV}=1）"
    for prefix, rule in ASK_DIR_PREFIXES:
        if rel.startswith(prefix):
            return "block", f"{rule}: 寫入 '{rel}' 屬 PERMISSIONS ask 級，需人工確認（或設 {OVERRIDE_ENV}=1）"
    return "allow", None


def main() -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        print(json.dumps({"decision": "allow"}))
        return 0

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        print(json.dumps({"decision": "allow", "warning": f"hook input not JSON: {e}"}))
        return 0

    tool_name = payload.get("tool_name") or payload.get("name") or ""
    if tool_name not in WRITE_TOOLS:
        # Bash is handled by permissions_guard.py; reads etc. pass through.
        print(json.dumps({"decision": "allow"}))
        return 0

    tool_input = payload.get("tool_input") or payload.get("input") or {}
    file_path = tool_input.get("file_path") or tool_input.get("path") or "" if isinstance(tool_input, dict) else ""

    decision, reason = evaluate(file_path)

    if decision == "block":
        if os.environ.get(OVERRIDE_ENV) == "1":
            print(json.dumps({"decision": "allow", "warning": f"ask-tier override active: {reason}"}))
            print(f"OVERRIDE: write_guard allowed ask-tier write ({reason})", file=sys.stderr)
            return 0
        print(json.dumps({"decision": "block", "reason": reason}))
        print(f"BLOCKED by write_guard: {reason}", file=sys.stderr)
        return 2

    print(json.dumps({"decision": "allow"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
