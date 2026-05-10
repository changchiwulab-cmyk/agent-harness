#!/usr/bin/env bash
# Routes PreToolUse hook payload to agent-governance plugin if installed,
# else to in-repo fallback (scripts/permissions_guard.py). Inherits stdin
# (hook payload JSON) and stdout (decision JSON) via exec.
#
# Wired from .claude/settings.json after N06b (task 20260509-N09) approval.
set -euo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
PLUGIN_HOOK="${HOME}/.claude/plugins/agent-governance/hooks/pre_tool_use.py"
FALLBACK_HOOK="${PROJECT_DIR}/scripts/permissions_guard.py"

if [ -r "$PLUGIN_HOOK" ]; then
  exec python3 "$PLUGIN_HOOK"
elif [ -r "$FALLBACK_HOOK" ]; then
  exec python3 "$FALLBACK_HOOK"
else
  echo "check_plugin_present: neither plugin nor fallback hook found; defaulting to allow" >&2
  echo '{"decision":"allow"}'
  exit 0
fi
