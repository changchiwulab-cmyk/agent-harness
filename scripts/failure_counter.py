#!/usr/bin/env python3
"""Consecutive-failure counter — make the "stop after 3 failures" hard rule real.

The self-assessment (§3.1) flagged that硬規則 3「連續失敗 3 次就停下來」had **0%
deterministic enforcement** — no counter, no halt mechanism, purely a prompt
request. This script gives the harness an actual counter plus a PreToolUse hook
that halts further tool calls once the threshold is reached.

Counting is runtime-automatic (20260716-P12): ``--post-hook`` is registered on
both PostToolUse (success-only event) and PostToolUseFailure in
``.claude/settings.json``, so every failed Bash/write tool call +1s the ACTIVE
task (``state/active_task.yaml``) and every successful one clears the count.
The count is *consecutive*: a success clears it, so two failures followed by a
success then a later failure leaves the count at 1 — only 3 failures in a row
trip the hook. Once tripped, the ``--hook`` mode deterministically blocks
subsequent Bash/Write/Edit calls until ``--reset``. The manual
``--record``/``--success`` CLI remains for debugging and non-hook flows.
The post-hook input layer is fail-open (bookkeeping automation, not a security
boundary — bad payload must not mis-count or brick the session; SECURITY.md).

State lives in ``logs/.failure_state.json`` (gitignored).

CLI:
    failure_counter.py --record  <task_id>     # +1, prints count; exit 3 if tripped
    failure_counter.py --success <task_id>     # a step succeeded -> clear count (keeps it consecutive)
    failure_counter.py --check   <task_id>     # prints count;     exit 3 if tripped
    failure_counter.py --reset   <task_id>     # clear that task's count (human un-halt)
    failure_counter.py --status                # show all counts
    failure_counter.py --hook                  # PreToolUse mode (stdin JSON -> decision)
    failure_counter.py --post-hook             # PostToolUse/PostToolUseFailure mode (auto count)
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "logs" / ".failure_state.json"
THRESHOLD = 3   # 連續失敗 3 次就停下來 (CLAUDE.md hard rule 3 / Task Card max_retries default)


def _state_path(root: Path | None = None) -> Path:
    return (root / "logs" / ".failure_state.json") if root else STATE_PATH


def load_state(root: Path | None = None) -> dict:
    path = _state_path(root)
    if not path.exists():
        return {"threshold": THRESHOLD, "counts": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"threshold": THRESHOLD, "counts": {}}
    data.setdefault("threshold", THRESHOLD)
    data.setdefault("counts", {})
    return data


def save_state(state: dict, root: Path | None = None) -> None:
    path = _state_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    state["updated"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def record(task_id: str, root: Path | None = None) -> int:
    state = load_state(root)
    state["counts"][task_id] = state["counts"].get(task_id, 0) + 1
    save_state(state, root)
    return state["counts"][task_id]


def reset(task_id: str, root: Path | None = None) -> None:
    state = load_state(root)
    state["counts"].pop(task_id, None)
    save_state(state, root)


def check(task_id: str, root: Path | None = None) -> int:
    return load_state(root)["counts"].get(task_id, 0)


def tripped(root: Path | None = None) -> list[str]:
    """Return task_ids whose failure count has reached the threshold."""
    state = load_state(root)
    thr = state.get("threshold", THRESHOLD)
    return [tid for tid, n in state["counts"].items() if n >= thr]


# --- PreToolUse hook mode --------------------------------------------------


def _is_reset_command(payload: dict) -> bool:
    """Allow the operator's own reset call through even when tripped."""
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    command = tool_input.get("command", "") if isinstance(tool_input, dict) else ""
    return "failure_counter" in command and "--reset" in command


def hook_decision(payload: dict, root: Path | None = None) -> tuple[str, str | None]:
    blocked = tripped(root)
    if not blocked:
        return "allow", None
    if _is_reset_command(payload):
        return "allow", None
    return (
        "block",
        f"連續失敗達門檻（{', '.join(blocked)}）— 已依硬規則 3 停下。"
        f"請檢視 logs/errors/ 後人工處理，再 `failure_counter.py --reset <task_id>` 解除。",
    )


def run_hook(root: Path | None = None) -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        print(json.dumps({"decision": "allow"}))
        return 0
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        print(json.dumps({"decision": "allow", "warning": f"hook input not JSON: {e}"}))
        return 0
    decision, reason = hook_decision(payload, root)
    if decision == "block":
        print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
        print(f"BLOCKED by failure_counter: {reason}", file=sys.stderr)
        return 2
    print(json.dumps({"decision": "allow"}))
    return 0


# --- PostToolUse / PostToolUseFailure hook mode ------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
POST_EVENTS = {"PostToolUse", "PostToolUseFailure"}


def _post_warn(message: str) -> int:
    print(f"failure_counter --post-hook: {message}（fail-open，見 SECURITY.md）", file=sys.stderr)
    return 0


def _read_active_task_id(root: Path | None = None) -> str:
    """ACTIVE task_id per state/active_task.yaml; '' when idle or unreadable."""
    try:
        if _SCRIPTS_DIR not in sys.path:
            sys.path.insert(0, _SCRIPTS_DIR)
        import active_task
        return active_task.active_task_id(root)
    except Exception as e:  # noqa: BLE001 — 記帳自動化，state 不可讀不得誤記
        _post_warn(f"active task 不可讀（{type(e).__name__}: {e}）— 不記數")
        return ""


def apply_post_event(payload: dict, root: Path | None = None) -> int:
    """Auto-count one tool result: failure -> +1, success -> clear (consecutive)."""
    event = payload.get("hook_event_name") or ""
    if event not in POST_EVENTS:
        return _post_warn(f"未知 hook_event_name {event!r} — 不記數")
    task_id = _read_active_task_id(root)
    if not task_id:
        return 0  # idle — 計數以 task_id 為鍵，無 active 卡不記帳
    if event == "PostToolUse":
        if check(task_id, root):
            reset(task_id, root)
        return 0
    if payload.get("is_interrupt"):
        return 0  # 使用者中斷不是任務失敗
    n = record(task_id, root)
    thr = load_state(root).get("threshold", THRESHOLD)
    if n >= thr:
        # PostToolUseFailure 的 exit 2 是 non-blocking、stderr 餵給 Claude：
        # 即時告知熔斷已武裝；真正攔阻由 PreToolUse --hook 負責。
        print(
            f"⛔ failure_counter: {task_id} 連續失敗 {n}/{thr} — 已達硬規則 3 門檻，"
            f"後續 Bash/寫入呼叫將被攔阻。請停下、寫 logs/errors/ 並通知使用者，"
            f"等人工 `failure_counter.py --reset {task_id}` 解除。",
            file=sys.stderr,
        )
        return 2
    return 0


def run_post_hook(root: Path | None = None) -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        return _post_warn("空 stdin — 無 payload 可判讀")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        return _post_warn(f"stdin 不是合法 JSON（{e}）")
    if not isinstance(payload, dict):
        return _post_warn("payload 不是 JSON object")
    return apply_post_event(payload, root)


def run_post_hook_guarded(root: Path | None = None) -> int:
    """記帳自動化不是安全邊界：任何內部錯誤都不得誤記或 brick session。"""
    try:
        return run_post_hook(root)
    except Exception as e:  # noqa: BLE001
        return _post_warn(f"內部錯誤（{type(e).__name__}: {e}）")


# --- CLI -------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="consecutive-failure counter + halt hook")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--record", metavar="TASK_ID")
    group.add_argument("--success", metavar="TASK_ID")
    group.add_argument("--check", metavar="TASK_ID")
    group.add_argument("--reset", metavar="TASK_ID")
    group.add_argument("--status", action="store_true")
    group.add_argument("--hook", action="store_true")
    group.add_argument("--post-hook", action="store_true", dest="post_hook")
    args = parser.parse_args(argv)

    if args.hook:
        return run_hook()
    if args.post_hook:
        return run_post_hook_guarded()

    thr = load_state().get("threshold", THRESHOLD)
    if args.record:
        n = record(args.record)
        print(f"{args.record}: {n}/{thr} consecutive failure(s)")
        if n >= thr:
            print("⛔ 已達門檻 — 依硬規則 3 停下，請人工介入後 --reset。")
            return 3
        return 0
    if args.success:
        reset(args.success)
        print(f"{args.success}: step succeeded — consecutive failure count cleared")
        return 0
    if args.check:
        n = check(args.check)
        print(f"{args.check}: {n}/{thr} consecutive failure(s)")
        return 3 if n >= thr else 0
    if args.reset:
        reset(args.reset)
        print(f"{args.reset}: reset to 0")
        return 0
    if args.status:
        state = load_state()
        if not state["counts"]:
            print("no recorded failures")
        else:
            for tid, n in sorted(state["counts"].items()):
                flag = " ⛔" if n >= thr else ""
                print(f"{tid}: {n}/{thr}{flag}")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
