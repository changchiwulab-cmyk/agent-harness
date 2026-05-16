#!/usr/bin/env python3
"""PreToolUse hook: catch AUDIT_LOG <-> Task Card drift at `git commit` time.

Why:
    logs/AUDIT_LOG.md is now machine-derived by scripts/generate_audit_log.py
    from tasks/20*.yaml + git log. The known footgun (see AUDIT_LOG entries
    20260515-001/002): committing a new/edited Task Card without regenerating
    AUDIT_LOG leaves the audit silently stale. This guard makes that drift
    visible *before* the commit lands, so the fix is "regenerate + include
    AUDIT_LOG in the same commit" rather than a follow-up cleanup.

Scope (deliberately narrow):
    - Only acts on Bash commands that contain `git commit`. Every other Bash
      call is allowed immediately without shelling out to the generator.
    - Runs `scripts/generate_audit_log.py --check`. Clean -> allow.
    - Drift -> behaviour depends on mode (see below).

Rollout mode (AUDIT_DRIFT_GUARD env var):
    - "warn"  (default): drift prints a warning to stderr but ALLOWS the
      commit (exit 0). Safe first-rollout per the approved plan's risk note
      ("warn 一輪觀察，確認無誤報再切 hard-block").
    - "block": drift is one of the two sanctioned hard-blocks (the other is
      the PERMISSIONS deny-list in permissions_guard.py). Emits decision
      "block" + exit 2 so Claude Code refuses the commit.

Composes with permissions_guard.py: both are PreToolUse/Bash hooks. For a
`git commit`, permissions_guard allows (no deny pattern matches), then this
guard runs.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "scripts" / "generate_audit_log.py"

# git global options that consume the following token as their argument.
_GLOBAL_OPTS_WITH_ARG = {
    "-c", "-C", "--git-dir", "--work-tree", "--namespace", "--super-prefix"
}


def _mode() -> str:
    return os.environ.get("AUDIT_DRIFT_GUARD", "warn").strip().lower()


def is_git_commit(command: str) -> bool:
    """True if `command` invokes `git commit`. Heuristic token walk that
    tolerates pipelines (`cd x && git commit`), env/path prefixes, and global
    options with separate args (`git -c user.name=x commit`)."""
    if not command:
        return False
    for sep in ("&&", "||", ";", "|", "`", "(", ")"):
        command = command.replace(sep, " ")
    toks = command.split()
    i = 0
    while i < len(toks):
        if toks[i] == "git" or toks[i].endswith("/git"):
            j = i + 1
            while j < len(toks):
                t = toks[j]
                if t in _GLOBAL_OPTS_WITH_ARG:
                    j += 2
                    continue
                if t.startswith("-"):
                    j += 1
                    continue
                return t == "commit"
            return False
        i += 1
    return False


def check_drift() -> tuple[bool, str]:
    """Return (drift, detail). On any generator failure, fail OPEN (no drift)
    so the guard never bricks the commit workflow over its own bug."""
    try:
        proc = subprocess.run(
            [sys.executable, str(GENERATOR), "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (subprocess.SubprocessError, OSError) as e:
        return False, f"guard self-check skipped ({e})"
    if proc.returncode == 0:
        return False, proc.stdout.strip()
    return True, (proc.stderr.strip() or proc.stdout.strip() or "AUDIT_LOG drift")


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
    command = tool_input.get("command", "") if isinstance(tool_input, dict) else ""

    if tool_name not in ("Bash", "bash", "") or not is_git_commit(command):
        print(json.dumps({"decision": "allow"}))
        return 0

    drift, detail = check_drift()
    if not drift:
        print(json.dumps({"decision": "allow"}))
        return 0

    msg = (
        "AUDIT_LOG drift: logs/AUDIT_LOG.md is stale vs tasks/20*.yaml. "
        "Run `python3 scripts/generate_audit_log.py` and include logs/AUDIT_LOG.md "
        f"in this commit. Detail: {detail}"
    )
    if _mode() == "block":
        print(json.dumps({"decision": "block", "reason": msg}))
        print(f"BLOCKED by audit_drift_guard: {msg}", file=sys.stderr)
        return 2

    print(json.dumps({"decision": "allow", "warning": msg}))
    print(f"WARNING audit_drift_guard (warn mode): {msg}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
