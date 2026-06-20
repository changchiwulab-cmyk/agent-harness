#!/usr/bin/env python3
"""Skill eval structural check (L4).

Lightweight, no-LLM gate: every skill under skills/ must ship a SKILL.md and an
eval_examples.md that contains BOTH a good-output example and a bad-output
example. This keeps eval coverage from silently rotting as skills are added.
The full LLM-judge eval harness is roadmap item L5; this only checks structure.

Usage: scripts/check_skill_evals.py
Exit: 0 = all skills OK, 1 = at least one skill missing a file or eval case.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"

# Markers that denote a good / bad output example in eval_examples.md.
GOOD_MARKER = "好的輸出範例"
BAD_MARKER = "壞的輸出範例"


def check_skill(skill_dir: Path) -> list[str]:
    """Return a list of problems for one skill dir (empty = OK)."""
    problems: list[str] = []
    name = skill_dir.name

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        problems.append(f"{name}: 缺少 SKILL.md")

    evals = skill_dir / "eval_examples.md"
    if not evals.exists():
        problems.append(f"{name}: 缺少 eval_examples.md")
        return problems

    text = evals.read_text(encoding="utf-8")
    if GOOD_MARKER not in text:
        problems.append(f"{name}: eval_examples.md 缺少『{GOOD_MARKER}』")
    if BAD_MARKER not in text:
        problems.append(f"{name}: eval_examples.md 缺少『{BAD_MARKER}』")
    return problems


def collect_problems() -> tuple[list[str], int]:
    """Return (problems, skills_checked)."""
    if not SKILLS_DIR.exists():
        return ["skills/ 目錄不存在"], 0
    skill_dirs = sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir())
    problems: list[str] = []
    for d in skill_dirs:
        problems.extend(check_skill(d))
    return problems, len(skill_dirs)


def main() -> int:
    problems, checked = collect_problems()
    if problems:
        print("❌ Skill eval 結構檢查失敗：")
        for p in problems:
            print(f"   - {p}")
        return 1
    print(f"OK: skill eval 結構檢查通過（{checked} 個 skill 各含 good + bad 範例）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
