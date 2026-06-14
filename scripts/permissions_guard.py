#!/usr/bin/env python3
"""PreToolUse hook: enforce PERMISSIONS.yaml at runtime.

Claude Code invokes this script before Bash / Write / Edit / MultiEdit /
NotebookEdit tool calls. It receives the tool input on stdin as JSON
({"tool_name": "...", "tool_input": {...}}) and emits a decision on stdout.

Two enforcement layers:

1. **Bash deny-list** — matches the command against deny patterns derived from
   PERMISSIONS.yaml (rm -rf, email/webhook/payment APIs, force-push). A match
   blocks (exit 2). Non-matching commands pass: this is a deny-list, not a
   sandbox.

2. **Write path ask-list** — maps the write target path to PERMISSIONS.yaml
   "ask" entries (system/, skills/, memory/, CLAUDE.md, outputs/reports/) and
   returns an "ask" decision so the human confirms before the write lands. This
   turns the previously prose-only ask tier into runtime enforcement (gap B1).

Output format (JSON), with both the legacy `decision` key and the current
`hookSpecificOutput.permissionDecision` form for forward-compat:
    {"decision": "allow"}
    {"decision": "block", "reason": "...", "hookSpecificOutput": {...}}
    {"decision": "ask",   "reason": "...", "hookSpecificOutput": {...}}
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PERMISSIONS_PATH = ROOT / "system" / "PERMISSIONS.yaml"


@dataclass(frozen=True)
class DenyRule:
    rule_id: str            # e.g. "shell_delete"
    pattern: re.Pattern     # compiled regex matched against the full command
    description: str        # human-readable reason


# Deny rules map PERMISSIONS.yaml deny entries to runtime command patterns.
# Each rule lists shell-level signatures that clearly fall under the named deny.
# Patterns are deliberately conservative: false positives (blocking benign work)
# are worse than false negatives (a sneakier command slipping through), because
# the harness itself is the second line of defence.
DENY_RULES: tuple[DenyRule, ...] = (
    DenyRule(
        rule_id="shell_delete",
        pattern=re.compile(
            r"""(?x)
            (^|[\s;&|`])              # boundary
            (
              rm\s+(-[a-zA-Z]*[rRfF][a-zA-Z]*\s+|--recursive\s+|--force\s+)  # rm with -r/-f/-rf
              | rmdir\s+
              | shred\s+
              | find\s+\S+.*-delete\b
            )
            """
        ),
        description="rm/rmdir/shred/find -delete blocked (PERMISSIONS deny: shell_delete)",
    ),
    DenyRule(
        rule_id="send_email",
        pattern=re.compile(
            r"""(?x)
            (^|[\s;&|`])
            (
              mail\s+-s
              | mailx\b
              | sendmail\b
              | curl\s+.*\b(api\.sendgrid|api\.mailgun|api\.postmark)\b
            )
            """
        ),
        description="mail/sendmail/email-API call blocked (PERMISSIONS deny: send_email)",
    ),
    DenyRule(
        rule_id="send_message_external",
        pattern=re.compile(
            r"""(?x)
            curl\s+.*\b(
              hooks\.slack\.com
              | api\.telegram\.org
              | notify-api\.line\.me
              | discord\.com/api/webhooks
            )\b
            """
        ),
        description="external messaging webhook blocked (PERMISSIONS deny: send_message_external)",
    ),
    DenyRule(
        rule_id="execute_payment",
        pattern=re.compile(
            r"""(?x)
            curl\s+.*\b(api\.stripe\.com|api-m\.paypal\.com|api\.square)\b
            """
        ),
        description="payment API call blocked (PERMISSIONS deny: execute_payment)",
    ),
    DenyRule(
        rule_id="git_force_push",
        pattern=re.compile(
            r"""(?x)
            git\s+push\s+.*(--force\b|-f\b)
            """
        ),
        description="git force-push blocked (production-data protection)",
    ),
)


def evaluate(command: str) -> tuple[str, str | None]:
    """Return ('allow', None) or ('block', reason)."""
    if not command:
        return "allow", None
    for rule in DENY_RULES:
        if rule.pattern.search(command):
            return "block", f"{rule.rule_id}: {rule.description}"
    return "allow", None


# Tools that write to the filesystem and therefore go through the path ask-list.
WRITE_TOOLS = ("Write", "Edit", "MultiEdit", "NotebookEdit")

# Path-prefix → PERMISSIONS.yaml "ask" entry. A write whose repo-relative target
# starts with one of these requires human confirmation. Prefixes ending in "/"
# match a directory subtree; bare names (CLAUDE.md) match that file exactly so
# memory/CLAUDE.md etc. are not caught by the root-CLAUDE.md rule.
ASK_PATH_RULES: tuple[tuple[str, str, str], ...] = (
    ("modify_system_rules", "system/", "writes under system/ need approval (PERMISSIONS ask: modify_system_rules)"),
    ("modify_skills", "skills/", "writes under skills/ need approval (PERMISSIONS ask: modify_skills)"),
    ("write_long_term_memory", "memory/", "writes under memory/ need approval (PERMISSIONS ask: write_long_term_memory)"),
    ("write_reports", "outputs/reports/", "formal reports need approval (PERMISSIONS ask: write_reports)"),
    ("modify_claude_md", "CLAUDE.md", "editing CLAUDE.md needs approval (PERMISSIONS ask: modify_claude_md)"),
)


def _repo_relative(file_path: str) -> str | None:
    """Return the repo-relative POSIX path, or None if the target is outside ROOT.

    Absolute paths are resolved and checked against ROOT; relative paths are
    normalised (leading './' stripped) and assumed repo-relative.
    """
    if not file_path:
        return None
    p = Path(file_path)
    if p.is_absolute():
        try:
            return p.resolve().relative_to(ROOT).as_posix()
        except ValueError:
            return None
    rel = p.as_posix()
    return rel[2:] if rel.startswith("./") else rel


def classify_write_path(file_path: str) -> tuple[str, str | None]:
    """Return ('allow', None) or ('ask', reason) for a write target path."""
    rel = _repo_relative(file_path)
    if rel is None:
        return "allow", None
    for rule_id, prefix, desc in ASK_PATH_RULES:
        matched = rel.startswith(prefix) if prefix.endswith("/") else rel == prefix
        if matched:
            return "ask", f"{rule_id}: {desc}"
    return "allow", None


def main() -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        # No input → nothing to decide. Default allow so the hook never breaks
        # benign tool calls due to upstream framing changes.
        print(json.dumps({"decision": "allow"}))
        return 0

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        print(json.dumps({"decision": "allow", "warning": f"hook input not JSON: {e}"}))
        return 0

    tool_name = payload.get("tool_name") or payload.get("name") or ""
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if not isinstance(tool_input, dict):
        tool_input = {}

    # --- Write path ask-list (Write/Edit/MultiEdit/NotebookEdit) ---
    if tool_name in WRITE_TOOLS:
        file_path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
        decision, reason = classify_write_path(file_path)
        if decision == "ask":
            print(json.dumps({
                "decision": "ask",
                "reason": reason,
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask",
                    "permissionDecisionReason": reason,
                },
            }))
            return 0
        print(json.dumps({"decision": "allow"}))
        return 0

    # --- Bash deny-list ("" treated as Bash for forward-compat framing) ---
    if tool_name in ("Bash", "bash", ""):
        command = tool_input.get("command") or tool_input.get("cmd") or ""
        decision, reason = evaluate(command)
        if decision == "block":
            # Exit code 2 signals deterministic block to Claude Code.
            print(json.dumps({
                "decision": "block",
                "reason": reason,
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                },
            }))
            print(f"BLOCKED by permissions_guard: {reason}", file=sys.stderr)
            return 2
        print(json.dumps({"decision": "allow"}))
        return 0

    # Any other tool (Read, Grep, web, MCP, …) is not guarded here.
    print(json.dumps({"decision": "allow"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
