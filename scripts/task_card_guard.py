#!/usr/bin/env python3
"""PreToolUse hook: a *new* formal output requires the ACTIVE Task Card (v2).

The self-assessment (§3.1) flagged that硬規則 1「沒有 Task Card，不執行任何任務」
had **0% deterministic enforcement**. v1 made it real at one chokepoint but
authorized by *filename coincidence*: any card under ``tasks/`` naming the
basename — including done/failed ones — permanently authorized a same-named
report (stale authorization, 外部報告缺點三；驗證見 20260710-001). v2 binds
authorization to the active task (20260710-002):

Deterministic rule (Write/Edit tools):
    - Writes outside ``outputs/reports/`` → allow (drafts, logs, code, scratch
      stay frictionless — deliberately, to avoid the §3.3 trap of locking the
      99% low-risk path).
    - Editing a report that already exists → allow (it was promoted under
      governance already; amendments such as addenda are legitimate).
    - Creating a NEW file under ``outputs/reports/`` → allow only if ALL of:
        1. ``state/active_task.yaml`` names an active task
           (``scripts/active_task.py --set <task_id>``);
        2. that card exists and its status is not done/failed;
        3. the card's ``expected_output.location + filename`` resolves to the
           exact target path — basename coincidence no longer authorizes.

Like permissions_guard.py this is a deny-list at one chokepoint, not a sandbox:
false positives (blocking benign work) are worse than the occasional miss.

Output (JSON on stdout): {"decision": "allow"} or {"decision": "block", "reason": ...}
Exit code 2 signals a deterministic block to Claude Code.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import active_task

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = (ROOT / "outputs" / "reports").resolve()
WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}


def declared_output_path(card: dict, root: Path) -> Path | None:
    """The exact path a card's expected_output resolves to, or None."""
    out = card.get("expected_output") or {}
    location = str(out.get("location") or "").strip().rstrip("/")
    filename = str(out.get("filename") or "").strip()
    if not location or not filename:
        return None
    return (root / location / filename).resolve()


def evaluate(file_path: str, root: Path = ROOT) -> tuple[str, str | None]:
    """Return ('allow', None) or ('block', reason) for a Write/Edit target."""
    if not file_path:
        return "allow", None
    target = Path(file_path)
    if not target.is_absolute():
        target = (root / target)
    target = target.resolve()
    reports_dir = (root / "outputs" / "reports").resolve()

    try:
        target.relative_to(reports_dir)
    except ValueError:
        return "allow", None   # not a formal output — frictionless

    if target.exists():
        return "allow", None   # amend an already-promoted report

    # New formal report → three-stage binding to the ACTIVE task.
    state = active_task.read_state(root)
    if state is None:
        return (
            "block",
            "state/active_task.yaml 缺失或不可讀 — active task 真相來源不可用時"
            "不得建立正式報告。請修復該檔後 `python3 scripts/active_task.py --set <task_id>`。",
        )
    task_id = str(state.get("task_id") or "").strip()
    if state.get("status") != "active" or not task_id:
        return (
            "block",
            f"沒有 active task — 新建正式報告（{target.name}）需先綁定執行中的 Task Card"
            f"（硬規則 1）：`python3 scripts/active_task.py --set <task_id>`，"
            f"或改寫到 outputs/drafts/。",
        )
    card_path, card = active_task.find_card(task_id, root)
    if card is None:
        return (
            "block",
            f"active task {task_id} 在 tasks/ 下找不到對應卡片 — "
            f"請確認卡片存在或重新 `--set`。",
        )
    status = str(card.get("status") or "").strip()
    if status in active_task.TERMINAL_STATUS:
        return (
            "block",
            f"active task {task_id}（{card_path.name}）status={status} 已結案，"
            f"不得再授權新正式報告（stale authorization 防護）。請開新卡或更新 active task。",
        )
    declared = declared_output_path(card, root)
    if declared != target:
        return (
            "block",
            f"active task {task_id} 宣告的輸出是 "
            f"{'（未宣告 expected_output）' if declared is None else declared}，"
            f"與目標 {target} 不符 — 授權以精確路徑比對，檔名巧合不再放行。"
            f"請修正卡片 expected_output 或改寫到 outputs/drafts/。",
        )
    return "allow", None


def _extract_path(tool_input: dict) -> str:
    if not isinstance(tool_input, dict):
        return ""
    return (
        tool_input.get("file_path")
        or tool_input.get("path")
        or tool_input.get("notebook_path")
        or ""
    )


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
        print(json.dumps({"decision": "allow"}))
        return 0

    tool_input = payload.get("tool_input") or payload.get("input") or {}
    decision, reason = evaluate(_extract_path(tool_input))
    if decision == "block":
        print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
        print(f"BLOCKED by task_card_guard: {reason}", file=sys.stderr)
        return 2

    print(json.dumps({"decision": "allow"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
