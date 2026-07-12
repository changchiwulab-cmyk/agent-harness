#!/usr/bin/env python3
"""PreToolUse hook: enforce the ACTIVE Task Card's allowed_tools at call time (P1-1).

Before this hook, the Task Card whitelist was pure after-the-fact governance:
gate_check.py L2 compares a run log's ``tools_used`` against ``allowed_tools``
— *if* the agent honestly wrote a run log, and only after the task ended.
At the moment a tool actually ran, the card had zero enforcement power
（GATE_POLICY.yaml L2 automation 自承）. 20260712-P11 closes that gap at the
two mutating chokepoints that already have matchers:

    Bash                              → classified as run_tests / bash
    Write|Edit|MultiEdit|NotebookEdit → target path mapped to the same tool
                                        vocabulary gate_check L2 compares
                                        (file_write / write_drafts /
                                        write_reports / modify_system_rules …)

Scope rules (deliberate, per the 20260710-001 adjudications — not reopened):

1. **Idle ⇒ allow everything.** Enforcement binds only while a card is active
   (``state/active_task.yaml``). Global mutating-tool binding was explicitly
   rejected（20260710-001 §三-6，違反 99% 低風險路徑哲學）— the card's
   whitelist has teeth *當下*, i.e. while that card is being executed.
2. **Read-only tools are never gated.** No matcher is registered for
   Read/Grep/Glob/WebSearch; this guard also passes through any tool outside
   the two matchers above.
3. **The governance control plane is exempt.** Writes under ``tasks/``,
   ``state/``, ``logs/``; the harness protocol CLIs (active_task /
   failure_counter / gate_check / verification_loop / sync_derived /
   validate_task_card); and ``git`` (checkpoints + push are mandated by
   CLAUDE.md for every task). The whitelist scopes *work products*, not the
   protocol bookkeeping every card must perform. Note the exemptions are
   deliberately coarse (``git`` prefix match): this is 防呆 scope enforcement,
   not a security boundary — deny signatures stay with permissions_guard.
4. **Input layer is fail-open** (empty stdin / bad JSON / uncaught exception
   → allow + stderr warning). The write matcher's fail-closed owner is
   task_card_guard（20260710-003）, which blocks the same unparseable payload;
   the Bash matcher's established philosophy is fail-open (permissions_guard).
   Duplicating fail-closed here would add a second session-bricking point
   without adding protection. Locked by tests; rationale in SECURITY.md.

Output (JSON on stdout): {"decision": "allow"} or {"decision": "block", "reason": ...}
Exit code 2 signals a deterministic block to Claude Code.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import active_task

ROOT = Path(__file__).resolve().parents[1]
WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
GATED_TOOLS = WRITE_TOOLS | {"Bash"}

# --- write-target classification --------------------------------------------

# Bookkeeping paths every task touches regardless of its declared scope.
EXEMPT_WRITE_PREFIXES = ("tasks/", "state/", "logs/")

# repo-relative prefix → tokens that authorize the write (any one suffices).
# Vocabulary matches what cards/run logs already use (gate_check L2 operates on
# the same names). Ask-level areas need their dedicated token — generic
# file_write does NOT cover them; allow-level output areas accept the generic.
WRITE_TOKEN_MAP: tuple[tuple[str, frozenset[str]], ...] = (
    ("outputs/drafts/", frozenset({"write_drafts", "create_output_files", "file_write"})),
    ("outputs/reports/", frozenset({"write_reports", "create_output_files", "file_write"})),
    ("outputs/", frozenset({"create_output_files", "file_write"})),
    ("system/", frozenset({"modify_system_rules"})),
    ("skills/", frozenset({"modify_skills"})),
    ("memory/", frozenset({"write_long_term_memory"})),
    (".claude/", frozenset({"modify_settings_json"})),
)
CLAUDE_MD_TOKENS = frozenset({"modify_claude_md"})
DEFAULT_WRITE_TOKENS = frozenset({"file_write"})

# --- Bash classification -----------------------------------------------------

# Harness protocol CLIs: anchored, single command only (no ;|&`$ chaining), so
# `active_task.py --get; <anything>` falls through to the bash-token check.
HARNESS_CLI_RE = re.compile(
    r"""(?x)
    ^\s*
    (?:python3?|bash)\s+
    ["']?(?:\S*/)?
    (?:scripts/(?:active_task|failure_counter|gate_check|verification_loop)\.py
      |scripts/sync_derived\.sh
      |system/validate_task_card\.py
    )["']?
    (?:\s[^;&|`$<>]*)?
    $
    """
)

# git checkpoints/push are protocol steps（CLAUDE.md「每關鍵階段 git commit
# checkpoint」）; deny signatures (e.g. force-push) remain permissions_guard's job.
GIT_RE = re.compile(r"^\s*git\s")

TEST_RE = re.compile(
    r"\bpytest\b|-m\s+unittest\b|\b(?:python3?|ruby)\s+\S*test_?\S*\.(?:py|rb)\b"
)


def classify_write(rel_path: str) -> frozenset[str] | None:
    """Tokens authorizing a repo-relative write, or None if exempt."""
    if rel_path.startswith(EXEMPT_WRITE_PREFIXES):
        return None
    if rel_path == "CLAUDE.md":
        return CLAUDE_MD_TOKENS
    for prefix, tokens in WRITE_TOKEN_MAP:
        if rel_path.startswith(prefix):
            return tokens
    return DEFAULT_WRITE_TOKENS


def classify_bash(command: str) -> frozenset[str] | None:
    """Tokens authorizing a Bash command, or None if exempt/empty."""
    if not command.strip():
        return None
    if HARNESS_CLI_RE.match(command) or GIT_RE.match(command):
        return None
    if TEST_RE.search(command):
        return frozenset({"run_tests", "bash"})
    return frozenset({"bash"})


def _extract_path(tool_input: dict) -> str:
    if not isinstance(tool_input, dict):
        return ""
    return (
        tool_input.get("file_path")
        or tool_input.get("path")
        or tool_input.get("notebook_path")
        or ""
    )


def _required_tokens(tool_name: str, tool_input: dict, root: Path) -> frozenset[str] | None:
    """What the card must declare for this call; None ⇒ out of scope / exempt."""
    if tool_name == "Bash":
        command = tool_input.get("command") if isinstance(tool_input, dict) else ""
        return classify_bash(str(command or ""))
    file_path = _extract_path(tool_input)
    if not file_path:
        return None
    target = Path(file_path)
    if not target.is_absolute():
        target = root / target
    target = target.resolve()
    try:
        rel = target.relative_to(root.resolve())
    except ValueError:
        return None  # outside the repo (e.g. session scratchpad) — not project data
    return classify_write(rel.as_posix())


def evaluate(tool_name: str, tool_input: dict, root: Path = ROOT) -> tuple[str, str | None]:
    """Return ('allow', None) or ('block', reason) for one tool call."""
    if tool_name not in GATED_TOOLS:
        return "allow", None

    required = _required_tokens(tool_name, tool_input, root)
    if required is None:
        return "allow", None  # exempt before any state/card lookup — recovery stays possible

    state = active_task.read_state(root)
    if state is None:
        # Truth source unreadable: the report chokepoint stays fail-closed via
        # task_card_guard; bricking Bash/code-writes here would block the repair.
        print(
            "allowed_tools_guard: state/active_task.yaml 不可讀，跳過白名單強制（fail-open）",
            file=sys.stderr,
        )
        return "allow", None
    task_id = str(state.get("task_id") or "").strip()
    if state.get("status") != "active" or not task_id:
        return "allow", None  # idle — enforcement only binds while a card is active

    card_path, card = active_task.find_card(task_id, root)
    if card is None:
        return (
            "block",
            f"active task {task_id} 在 tasks/ 下找不到對應卡片，無法評估 allowed_tools — "
            f"請修復卡片或重新綁定（python3 scripts/active_task.py --set/--clear；"
            f"控制面路徑與指令不受本 guard 限制）。",
        )
    allowed_raw = card.get("allowed_tools")
    if not isinstance(allowed_raw, list) or not allowed_raw:
        return (
            "block",
            f"active task {task_id}（{card_path.name}）的 allowed_tools 缺失或非法"
            f"（須為非空 list）— 白名單不可評估時不得授權工作產出類動作；"
            f"請先修卡（tasks/ 為控制面路徑，可直接編修）。",
        )
    allowed = {str(t).strip() for t in allowed_raw}
    if allowed & required:
        return "allow", None

    action = (
        f"Bash 指令" if tool_name == "Bash" else f"{tool_name} → {_extract_path(tool_input)}"
    )
    return (
        "block",
        f"{action} 需要 allowed_tools 之一 {sorted(required)}，"
        f"但 active task {task_id}（{card_path.name}）只宣告 {sorted(allowed)} — "
        f"卡片白名單當下強制（20260712-P11）。請改用卡片宣告範圍內的做法，"
        f"或把所需工具補進卡片 allowed_tools（tasks/ 為控制面路徑，可直接編修）。",
    )


def _warn_allow(message: str) -> int:
    print(f"allowed_tools_guard: {message}（fail-open，見 SECURITY.md）", file=sys.stderr)
    print(json.dumps({"decision": "allow"}))
    return 0


def main() -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        return _warn_allow("空 stdin — 無 payload 可判讀；寫入 matcher 的 fail-closed 由 task_card_guard 專責")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        return _warn_allow(f"stdin 不是合法 JSON（{e}）")

    tool_name = payload.get("tool_name") or payload.get("name") or ""
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    decision, reason = evaluate(tool_name, tool_input)
    if decision == "block":
        print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
        print(f"BLOCKED by allowed_tools_guard: {reason}", file=sys.stderr)
        return 2
    print(json.dumps({"decision": "allow"}))
    return 0


def run_guarded() -> int:
    """Scope guard, not the security boundary: crashes stay non-blocking (fail-open)."""
    try:
        return main()
    except Exception as e:  # noqa: BLE001 — 任何內部錯誤都不得 brick session
        return _warn_allow(f"內部錯誤（{type(e).__name__}: {e}）")


if __name__ == "__main__":
    raise SystemExit(run_guarded())
