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

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"

# Markers that denote a good / bad output example in eval_examples.md.
GOOD_MARKER = "好的輸出範例"
BAD_MARKER = "壞的輸出範例"
RUBRIC_MARKER = "判斷標準"

# Section headings (with the ## prefix) used by the shared parser below.
GOOD_HEADING = f"## {GOOD_MARKER}"
BAD_HEADING = f"## {BAD_MARKER}"
RUBRIC_HEADING = f"## {RUBRIC_MARKER}"


# --- Shared parser (reused by scripts/run_skill_evals.py L5) ----------------


def _section(text: str, start_heading: str, end_headings: list[str]) -> str:
    """Return the slice of `text` after `start_heading` up to the first end heading."""
    start = text.find(start_heading)
    if start == -1:
        return ""
    start += len(start_heading)
    end = len(text)
    for h in end_headings:
        i = text.find(h, start)
        if i != -1:
            end = min(end, i)
    return text[start:end]


def _first_fence(section: str) -> str:
    """Return the contents of the first ```fenced``` block in `section` (stripped)."""
    m = re.search(r"```[^\n]*\n(.*?)\n```", section, re.DOTALL)
    return m.group(1).strip() if m else ""


def parse_rubric(section: str) -> list[dict]:
    """Parse the 判斷標準 markdown table into [{item, pass, fail}] criteria rows."""
    criteria: list[dict] = []
    for raw in section.splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 3:
            continue
        item, pass_desc, fail_desc = cells[0], cells[1], cells[2]
        if not item or item == "項目":
            continue
        if set(item) <= set("-: "):  # separator row like |---|---|---|
            continue
        criteria.append({"item": item, "pass": pass_desc, "fail": fail_desc})
    return criteria


def parse_eval_examples(text: str) -> dict:
    """Extract good output, bad output, and rubric criteria from an eval_examples.md.

    Returns {"good": str, "bad": str, "criteria": [{item, pass, fail}, ...]}.
    Shared by the L4 structural check and the L5 LLM-judge harness so there is
    one parser for the eval-examples format.
    """
    good_sec = _section(text, GOOD_HEADING, [BAD_HEADING, RUBRIC_HEADING])
    bad_sec = _section(text, BAD_HEADING, [RUBRIC_HEADING])
    rubric_sec = _section(text, RUBRIC_HEADING, [])
    return {
        "good": _first_fence(good_sec),
        "bad": _first_fence(bad_sec),
        "criteria": parse_rubric(rubric_sec),
    }


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
