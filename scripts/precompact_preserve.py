#!/usr/bin/env python3
"""PreCompact hook：壓縮前保全治理狀態（**fail-open**）。

context 壓縮前，把未結 Task Card 的 goal / definition_of_done 與最後 checkpoint
印到 stdout，讓壓縮後的 context 仍保留關鍵治理狀態，緩解 FAILURE_TAXONOMY
SPEC-03（對話歷史遺失）。此機制取代手動「20 輪摘要」規則 —— 改由原生
auto-compaction 觸發、本 hook 負責保全不可遺失的治理錨點。
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
OPEN_STATUSES = ("in_progress", "checkpoint", "review")


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args, _ = parser.parse_known_args(argv)
    try:
        print(build_state(args.root))
    except Exception:
        pass  # fail-open
    return 0


if __name__ == "__main__":
    sys.exit(main())
