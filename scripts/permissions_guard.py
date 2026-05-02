#!/usr/bin/env python3
"""PreToolUse hook: enforce PERMISSIONS.yaml deny list at runtime.

Claude Code invokes this script before each Bash tool call. It receives the
tool input on stdin as JSON ({"tool_name": "Bash", "tool_input": {"command": "..."}}),
matches the command against deny patterns derived from system/PERMISSIONS.yaml,
and emits a decision on stdout.

Output format (JSON):
    {"decision": "allow"}
    {"decision": "block", "reason": "matched deny rule: shell_delete (pattern: rm -rf)"}

Non-matching commands are allowed by default — this guard is a *deny-list*,
not a sandbox. The intent is to catch obvious violations of the harness's
explicit deny list, not to lock down every shell invocation.
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
    command = ""
    if isinstance(tool_input, dict):
        command = tool_input.get("command") or tool_input.get("cmd") or ""

    # Only evaluate Bash-style commands. Edit/Write are guarded by other layers.
    if tool_name not in ("Bash", "bash", ""):
        print(json.dumps({"decision": "allow"}))
        return 0

    decision, reason = evaluate(command)
    if decision == "block":
        # Exit code 2 signals deterministic block to Claude Code.
        print(json.dumps({"decision": "block", "reason": reason}))
        print(f"BLOCKED by permissions_guard: {reason}", file=sys.stderr)
        return 2

    print(json.dumps({"decision": "allow"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
