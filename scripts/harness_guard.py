#!/usr/bin/env python3
"""PreToolUse hook: warn (never block) on CLAUDE.md hard-rule 1 & 2 signals.

The two genuinely dangerous things are already hard-blocked elsewhere:
  - PERMISSIONS deny-list  -> scripts/permissions_guard.py
  - AUDIT_LOG drift commit -> scripts/audit_drift_guard.py

This guard covers the remaining two hard rules at the *advisory* level the
approved plan calls for ("預設 warn，不擋"):

  Rule 1  沒有 Task Card，不執行任何任務
          -> heuristic: a Write/Edit into a deliverable tree while the git
             working tree shows no Task Card activity (no tasks/*.yaml staged,
             modified, or untracked, and HEAD isn't a task/checkpoint commit).
  Rule 2  對外動作只產出草稿
          -> heuristic: a Write/Edit to outputs/ that is NOT under
             outputs/drafts/ (formal/external output bypassing draft-first).

Both paths only ever emit {"decision":"allow"} (optionally with a warning).
Heuristics are deliberately lenient — a missed warn is fine, a noisy false
warn is not. Any internal error fails open (allow, no warning).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Writing under these roots is "doing task work" for Rule-1 purposes.
_DELIVERABLE_ROOTS = (
    "outputs/", "system/", "skills/", "scripts/",
    ".github/", ".claude/", "frontend/", "memory/", "tests/",
)


def _rel(path: str) -> str:
    """Path relative to repo root using forward slashes, or '' if outside."""
    if not path:
        return ""
    try:
        p = Path(path)
        p = p if p.is_absolute() else (ROOT / p)
        return p.resolve().relative_to(ROOT).as_posix()
    except (ValueError, OSError):
        return ""


def _has_task_card_activity() -> bool:
    """True if the working tree / HEAD shows Task Card context.

    Lenient on purpose: any non-template tasks/*.yaml that is staged, modified
    or untracked, OR a HEAD commit subject that references a task/checkpoint.
    """
    try:
        st = subprocess.run(
            ["git", "status", "--porcelain", "--", "tasks/"],
            cwd=ROOT, capture_output=True, text=True, timeout=10,
        )
        for line in st.stdout.splitlines():
            name = line[3:].strip()
            if name.endswith(".yaml") and "TEMPLATE" not in name and "/" in name:
                return True
        head = subprocess.run(
            ["git", "log", "-1", "--pretty=%s"],
            cwd=ROOT, capture_output=True, text=True, timeout=10,
        )
        subj = head.stdout.strip()
        if "checkpoint: [" in subj or "[2" in subj:  # e.g. [20260515-004]
            return True
    except (subprocess.SubprocessError, OSError):
        # Fail open: assume context exists so we don't warn spuriously.
        return True
    return False


def evaluate(rel_path: str) -> str | None:
    """Return a warning string, or None."""
    if not rel_path:
        return None

    # Rule 2: formal output must go through outputs/drafts/ first.
    if rel_path.startswith("outputs/") and not rel_path.startswith("outputs/drafts/"):
        return (
            f"規則2 提醒：{rel_path} 不在 outputs/drafts/。對外/正式產出應先到 "
            "drafts/ 經人工確認再晉升（CLAUDE.md 硬規則2）。"
        )

    # Rule 1: deliverable write without visible Task Card context.
    if rel_path.startswith(_DELIVERABLE_ROOTS) and not rel_path.startswith("tasks/"):
        if not _has_task_card_activity():
            return (
                f"規則1 提醒：正在寫 {rel_path}，但 git working tree/HEAD 看不到 "
                "Task Card 活動。請確認本次動作有對應 tasks/*.yaml（CLAUDE.md 硬規則1）。"
            )
    return None


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
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if tool_name not in ("Write", "Edit", "NotebookEdit"):
        print(json.dumps({"decision": "allow"}))
        return 0

    path = ""
    if isinstance(tool_input, dict):
        path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""

    try:
        warning = evaluate(_rel(path))
    except Exception:  # never break a tool call over a guard bug
        warning = None

    if warning:
        print(json.dumps({"decision": "allow", "warning": warning}))
        print(f"WARNING harness_guard: {warning}", file=sys.stderr)
        return 0

    print(json.dumps({"decision": "allow"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
