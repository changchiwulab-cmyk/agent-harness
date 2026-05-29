#!/usr/bin/env python3
"""SessionStart hook：載入 recovery / 定向 context。

Claude Code 在 session 啟動時執行本腳本，stdout 會被加入 session 起始 context，
讓 agent 一開始就知道：目前未結的 Task Card、最後一個 git checkpoint、以及
recovery runbook 的位置。把 system/RECOVERY_RUNBOOK.md 的「scenario C：context
reset 後從未完成子任務續跑」與 FAILURE_TAXONOMY COORD-01 / SPEC-03 自動化。

設計原則：快速、**fail-open**（任何錯誤一律 exit 0，絕不阻斷 session）。
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
OPEN_STATUSES = ("pending", "in_progress", "checkpoint", "review")


def _git(root: Path, *args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True, timeout=5
        ).stdout.strip()
    except Exception:
        return ""


def open_task_cards(root: Path) -> list[str]:
    """回傳未結（pending/in_progress/checkpoint/review）的 Task Card 摘要行。"""
    rows = []
    for p in sorted(Path(root).glob("tasks/20*.yaml")):
        try:
            doc = yaml.safe_load(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(doc, dict) and str(doc.get("status", "")) in OPEN_STATUSES:
            rows.append(
                f"  - {doc.get('task_id', '?')} [{doc.get('status')}] {doc.get('goal', '')}".rstrip()
            )
    return rows


def build_context(root: Path) -> str:
    branch = _git(root, "rev-parse", "--abbrev-ref", "HEAD")
    last = _git(root, "log", "-1", "--pretty=%h %s")
    cards = open_task_cards(root)
    lines = ["# Harness session 定向（SessionStart hook）", ""]
    lines.append(f"分支：{branch or '?'}　最後 checkpoint：{last or '(無)'}")
    lines.append("未結 Task Card：" + ("" if cards else "無"))
    lines.extend(cards)
    lines += ["", "中斷復原見 system/RECOVERY_RUNBOOK.md；沒有 Task Card 不執行任務。"]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args, _ = parser.parse_known_args(argv)
    try:
        print(build_context(args.root))
    except Exception:
        pass  # fail-open：絕不阻斷 session
    return 0


if __name__ == "__main__":
    sys.exit(main())
