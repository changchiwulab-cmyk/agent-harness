#!/usr/bin/env python3
"""PreToolUse hook — runtime deny-list guard.

Ported from agent-harness scripts/permissions_guard.py (PR #63 Phase A).
Reads tool input from stdin as JSON, matches Bash commands against deny
patterns, emits {"decision": "allow"|"block", ...} on stdout.

Deny patterns ship with the plugin under config/deny_patterns.yaml; this
file inlines the v0.1.0 default set for self-containment.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class DenyRule:
    rule_id: str
    pattern: re.Pattern
    description: str


DENY_RULES: tuple[DenyRule, ...] = (
    DenyRule(
        rule_id="shell_delete",
        pattern=re.compile(
            r"""(?x)
            (^|[\s;&|`])
            (
              rm\s+(-[a-zA-Z]*[rRfF][a-zA-Z]*\s+|--recursive\s+|--force\s+)
              | rmdir\s+
              | shred\s+
              | find\s+\S+.*-delete\b
            )
            """
        ),
        description="rm/rmdir/shred/find -delete blocked (deny: shell_delete)",
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
        description="mail/sendmail/email-API call blocked (deny: send_email)",
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
        description="external messaging webhook blocked (deny: send_message_external)",
    ),
    DenyRule(
        rule_id="execute_payment",
        pattern=re.compile(
            r"""(?x)
            curl\s+.*\b(api\.stripe\.com|api-m\.paypal\.com|api\.square)\b
            """
        ),
        description="payment API call blocked (deny: execute_payment)",
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
    if not command:
        return "allow", None
    for rule in DENY_RULES:
        if rule.pattern.search(command):
            return "block", f"{rule.rule_id}: {rule.description}"
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
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    command = ""
    if isinstance(tool_input, dict):
        command = tool_input.get("command") or tool_input.get("cmd") or ""

    if tool_name not in ("Bash", "bash", ""):
        print(json.dumps({"decision": "allow"}))
        return 0

    decision, reason = evaluate(command)
    if decision == "block":
        print(json.dumps({"decision": "block", "reason": reason}))
        print(f"BLOCKED by pre_tool_use: {reason}", file=sys.stderr)
        return 2

    print(json.dumps({"decision": "allow"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
