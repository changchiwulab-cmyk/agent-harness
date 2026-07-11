#!/usr/bin/env python3
"""Active-task pointer — 「現在正在執行哪張 Task Card」的單一真相來源。

外部報告驗證（20260710-001）確認 repo 內沒有任何檔案記錄 live task_id：
state/last_checkpoint.yaml 是 session 尾寫的 resume 快照（checkpoint_commit
必填，任務起點無值可填），而 task_card_guard 過去以「檔名巧合」授權新正式
報告 — 掃全部卡、不看 status，done/failed 的卡永久授權同名檔。

本 CLI 維護 state/active_task.yaml。--set 仍是 prompt 自律動作（與
failure_counter --record 同樣誠實定位），但強制力在 task_card_guard：
沒有 active task 綁定到宣告精確輸出路徑的存活卡，就無法新建
outputs/reports/ 檔 — 把「自律」翻轉成「不做就被擋」的結構性誘因。

CLI:
    active_task.py --set <task_id>   # 綁定；卡必須存在且 status ∉ {done,failed}
    active_task.py --clear           # 解除（status: idle）
    active_task.py --get             # 印出當前 task_id；idle 時 exit 1
    active_task.py --check <task_id> # 當前 active 即為該 id 時 exit 0，否則 exit 1
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TERMINAL_STATUS = {"done", "failed"}   # 已結案的卡不得成為 active task


def _state_path(root: Path | None = None) -> Path:
    return (root or ROOT) / "state" / "active_task.yaml"


def read_state(root: Path | None = None) -> dict | None:
    """回傳 active-task mapping；檔案缺失/不可讀/非 mapping 時回 None。

    guard 端據此區分「真相來源不可用」（block，要求修復）與
    「idle」（block，提示 --set）。
    """
    path = _state_path(root)
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None
    return doc if isinstance(doc, dict) else None


def active_task_id(root: Path | None = None) -> str:
    """當前 active 的 task_id；idle/缺檔/壞檔時回空字串。"""
    state = read_state(root)
    if not state or state.get("status") != "active":
        return ""
    return str(state.get("task_id") or "").strip()


def find_card(task_id: str, root: Path | None = None) -> tuple[Path | None, dict | None]:
    """以 task_id 定位 Task Card（跳過 TEMPLATE），找不到回 (None, None)。"""
    tasks_dir = (root or ROOT) / "tasks"
    if not task_id or not tasks_dir.exists():
        return None, None
    for path in sorted(tasks_dir.rglob("*.yaml")):
        if "TEMPLATE" in path.name:
            continue
        try:
            card = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            continue
        if isinstance(card, dict) and card.get("task_id") == task_id:
            return path, card
    return None, None


def _write_state(state: dict, root: Path | None = None) -> None:
    path = _state_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    body = yaml.safe_dump(state, allow_unicode=True, sort_keys=False)
    header = "# 由 scripts/active_task.py 維護；schema 見 state/active_task.SCHEMA.yaml。\n"
    path.write_text(header + body, encoding="utf-8")


def set_active(task_id: str, root: Path | None = None) -> str | None:
    """綁定 active task；成功回 None，失敗回錯誤訊息。"""
    task_id = (task_id or "").strip()
    if not task_id:
        return "task_id 不能為空"
    card_path, card = find_card(task_id, root)
    if card is None:
        return f"tasks/ 下找不到 task_id 為 {task_id} 的 Task Card"
    status = str(card.get("status") or "").strip()
    if status in TERMINAL_STATUS:
        return (
            f"卡片 {card_path.name} 的 status={status} 已結案，"
            f"不得成為 active task（stale authorization 防護）"
        )
    _write_state(
        {
            "task_id": task_id,
            "status": "active",
            "activated_at": date.today().isoformat(),
            "note": "",
        },
        root,
    )
    return None


def clear_active(root: Path | None = None) -> None:
    _write_state({"task_id": "", "status": "idle", "activated_at": "", "note": ""}, root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="active-task pointer (state/active_task.yaml)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--set", metavar="TASK_ID", dest="set_id")
    group.add_argument("--clear", action="store_true")
    group.add_argument("--get", action="store_true")
    group.add_argument("--check", metavar="TASK_ID", dest="check_id")
    args = parser.parse_args(argv)

    if args.set_id:
        error = set_active(args.set_id)
        if error:
            print(f"❌ {error}", file=sys.stderr)
            return 1
        print(f"active task ← {args.set_id}")
        return 0
    if args.clear:
        clear_active()
        print("active task cleared (idle)")
        return 0
    if args.get:
        current = active_task_id()
        if not current:
            print("(idle)")
            return 1
        print(current)
        return 0
    if args.check_id:
        current = active_task_id()
        if current == args.check_id.strip():
            print(f"active: {current}")
            return 0
        print(f"active task is {current or '(idle)'}, not {args.check_id}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
