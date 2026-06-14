#!/usr/bin/env python3
"""Structural eval loop over each skill's golden examples (gap A2/C4, structural tier).

Each skills/<skill>/eval_examples.md documents a GOOD output and a BAD output. This
runs a *model-free* structural eval: it derives a rubric from the GOOD example's
section structure, then scores both examples against it. A skill "passes" when the
GOOD example fully conforms and the rubric discriminates (GOOD scores strictly
higher than BAD).

This is the structural tier deliberately chosen over an LLM-judge (no model calls,
fully CI-testable, zero marginal cost). It pins the golden sets' structure and lays
the foundation a future LLM-judge tier scores *content* on top of.

Usage:
    python3 scripts/run_evals.py [--json]

Exit code: 0 = all skills pass, 1 = at least one skill fails the eval, 2 = load error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"

GOOD_HEADER = "好的輸出範例"
BAD_HEADER = "壞的輸出範例"
# A GOOD example must conform fully; BAD must fall at/under this to count as discriminating.
GOOD_PASS_THRESHOLD = 1.0
BAD_CEILING = 0.5


def _extract_block_after(text: str, section_title: str) -> str | None:
    """Return the first fenced code block appearing after a `## <section_title>` heading."""
    lines = text.splitlines()
    in_section = False
    in_fence = False
    captured: list[str] = []
    for line in lines:
        if re.match(r"^#{1,6}\s+", line):
            if section_title in line:
                in_section = True
                continue
            if in_section and not in_fence:
                break  # next heading ends the section before any fence
        if not in_section:
            continue
        if line.lstrip().startswith("```"):
            if not in_fence:
                in_fence = True
                continue
            return "\n".join(captured)  # closing fence
        if in_fence:
            captured.append(line)
    return None


def section_titles(block: str) -> list[str]:
    """Normalised ## / ### header titles inside a block (drops the top-level # title)."""
    titles = []
    for line in block.splitlines():
        m = re.match(r"^(#{2,3})\s+(.*\S)\s*$", line)
        if m:
            titles.append(m.group(2).strip())
    return titles


def conformance(candidate: str, rubric: list[str]) -> float:
    """Fraction of rubric section titles present as headers in the candidate."""
    if not rubric:
        return 0.0
    present = set(section_titles(candidate))
    hit = sum(1 for t in rubric if t in present)
    return hit / len(rubric)


def eval_skill(eval_md: Path) -> dict:
    text = eval_md.read_text(encoding="utf-8")
    good = _extract_block_after(text, GOOD_HEADER)
    bad = _extract_block_after(text, BAD_HEADER)
    skill = eval_md.parent.name
    if good is None or bad is None:
        return {"skill": skill, "ok": False,
                "reason": f"missing good/bad block (good={good is not None}, bad={bad is not None})"}
    rubric = section_titles(good)
    good_score = conformance(good, rubric)
    bad_score = conformance(bad, rubric)
    ok = (
        len(rubric) > 0
        and good_score >= GOOD_PASS_THRESHOLD
        and good_score > bad_score
        and bad_score <= BAD_CEILING
    )
    return {
        "skill": skill,
        "ok": ok,
        "rubric_size": len(rubric),
        "good_score": round(good_score, 3),
        "bad_score": round(bad_score, 3),
        "reason": "" if ok else "rubric did not discriminate good vs bad",
    }


def run_all(skills_dir: Path = SKILLS_DIR) -> list[dict]:
    results = []
    for eval_md in sorted(skills_dir.glob("*/eval_examples.md")):
        results.append(eval_skill(eval_md))
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Structural eval over skill golden examples.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    results = run_all()
    if not results:
        print("ERROR: no skills/*/eval_examples.md found", file=sys.stderr)
        return 2

    failed = [r for r in results if not r["ok"]]
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print("Structural eval (skill golden examples)")
        for r in results:
            badge = "✅" if r["ok"] else "❌"
            extra = (f"rubric={r.get('rubric_size')} good={r.get('good_score')} bad={r.get('bad_score')}"
                     if "good_score" in r else r.get("reason", ""))
            print(f"  {badge} {r['skill']}: {extra}")
        print(f"Result: {'FAIL' if failed else 'PASS'}" +
              (f" ({', '.join(r['skill'] for r in failed)})" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
