#!/usr/bin/env python3
"""PreCompact hook：壓縮前把治理狀態寫成持久快照（**fail-open**）。

背景：依 Claude Code hooks 規範，PreCompact 的 stdout 不會被注入壓縮後的 context
（只有 SessionStart / UserPromptSubmit 會）。因此「印到 stdout 保全狀態」行不通。
改採持久化路徑：壓縮前把未結 Task Card 的 goal / definition_of_done 與最後
checkpoint 寫到 gitignored 的 `logs/.session_state.md`，成為可被 RECOVERY_RUNBOOK
（scenario C：context 重置後續跑）與人工/agent 讀取的復原產物，緩解 SPEC-03。
另以 JSON `systemMessage` 提示使用者快照位置。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import yaml

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
OPEN_STATUSES = ("in_progress", "checkpoint", "review")
SNAPSHOT_REL = "logs/.session_state.md"


def open_cards(root: Path) -> list[dict]:
    out = []
    for p in sorted(Path(root).glob("tasks/20*.yaml")):
        try:
            doc = yaml.safe_load(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(doc, dict) and str(doc.get("status", "")) in OPEN_STATUSES:
            out.append(doc)
    return out


def build_state(root: Path, limit: int = 5) -> str:
    lines = ["# 壓縮前治理狀態保全（PreCompact hook）", ""]
    try:
        last = subprocess.run(
            ["git", "log", "-1", "--pretty=%h %s"], cwd=root,
            capture_output=True, text=True, timeout=5,
        ).stdout.strip()
        if last:
            lines.append(f"最後 checkpoint：{last}")
    except Exception:
        pass
    cards = sorted(open_cards(root), key=lambda d: str(d.get("task_id", "")), reverse=True)
    for doc in cards[:limit]:
        lines.append(f"- {doc.get('task_id', '?')}：{doc.get('goal', '')}")
        for d in (doc.get("definition_of_done") or [])[:6]:
            lines.append(f"    DoD: {d}")
    if len(cards) > limit:
        lines.append(f"（其餘 {len(cards) - limit} 張未列；見 tasks/）")
    return "\n".join(lines)


def write_snapshot(root: Path) -> Path | None:
    """把治理狀態寫到 logs/.session_state.md（持久、gitignored）。回傳路徑或 None。"""
    snapshot = Path(root) / SNAPSHOT_REL
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    snapshot.write_text(build_state(root) + "\n", encoding="utf-8")
    return snapshot


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args, _ = parser.parse_known_args(argv)
    try:
        write_snapshot(args.root)
        msg = (
            f"壓縮前已將未結 Task Card 的 goal/DoD 與最後 checkpoint 寫入 {SNAPSHOT_REL}；"
            "壓縮/重置後可依 system/RECOVERY_RUNBOOK.md 從該快照與 Task Card 續跑。"
        )
        print(json.dumps({"systemMessage": msg}, ensure_ascii=False))
    except Exception:
        pass  # fail-open：絕不阻斷壓縮
    return 0


if __name__ == "__main__":
    sys.exit(main())
