#!/usr/bin/env python3
"""Output-quality eval harness for skill outputs.

Operationalises GATE_POLICY completion_check: instead of grading skill output
purely by hand, score it against a per-skill rubric derived from each skill's
output format + eval_examples.md (see evals/README.md).

Two layers (Decision D008):
  * Heuristic scoring (this script): deterministic structural checks — runs in
    CI, zero LLM cost, catches skill-prompt regressions via golden cases.
  * LLM-as-judge: documented on-demand step (evals/README.md), NOT in CI, for
    qualitative depth the heuristics can't reach.

Usage:
    run_evals.py --check                  # run all golden cases, fail on mismatch (CI gate)
    run_evals.py --skill research         # run one skill's golden cases
    run_evals.py --score draft.md --skill research   # score an arbitrary output
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
RUBRICS_DIR = ROOT / "evals" / "rubrics"
GOLDEN_DIR = ROOT / "evals" / "golden"
DEFAULT_THRESHOLD = 0.7


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def load_rubric(skill: str, root: Path = ROOT) -> dict[str, Any]:
    path = root / "evals" / "rubrics" / f"{skill}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"no rubric for skill '{skill}': {path}")
    return load_yaml(path)


# --- heuristic checks (deterministic) ---------------------------------------

def _first_heading_line(lines: list[str], sub: str) -> int:
    for i, line in enumerate(lines):
        if line.lstrip().startswith("#") and sub in line:
            return i
    return -1


def _heading_nonempty(lines: list[str], sub: str) -> bool:
    idx = _first_heading_line(lines, sub)
    if idx < 0:
        return False
    for line in lines[idx + 1:]:
        if line.lstrip().startswith("#"):
            break
        if line.strip():
            return True
    return False


def run_check(check: dict[str, Any], text: str) -> bool:
    lines = text.splitlines()
    t = check.get("type")
    if t == "headings_present":
        return all(_first_heading_line(lines, s) >= 0 for s in check["sections"])
    if t == "heading_nonempty":
        return _heading_nonempty(lines, check["section"])
    if t == "heading_order":
        b = _first_heading_line(lines, check["before"])
        a = _first_heading_line(lines, check["after"])
        return b >= 0 and a >= 0 and b < a
    if t == "absent":
        return not any(p in text for p in check["patterns"])
    if t == "present_any":
        return any(p in text for p in check["patterns"])
    if t == "present_all":
        return all(p in text for p in check["patterns"])
    raise ValueError(f"unknown check type: {t}")


def score_output(text: str, rubric: dict[str, Any]) -> dict[str, Any]:
    results = []
    total = 0
    passed_w = 0
    required_fail = False
    for c in rubric.get("criteria", []):
        ok = run_check(c["check"], text)
        w = int(c.get("weight", 1))
        total += w
        if ok:
            passed_w += w
        elif c.get("required"):
            required_fail = True
        results.append({
            "id": c["id"],
            "passed": ok,
            "weight": w,
            "required": bool(c.get("required", False)),
        })
    pct = (passed_w / total) if total else 0.0
    threshold = float(rubric.get("pass_threshold", DEFAULT_THRESHOLD))
    passed = (not required_fail) and pct >= threshold
    return {
        "score": passed_w,
        "max": total,
        "pct": round(pct, 3),
        "passed": passed,
        "required_fail": required_fail,
        "criteria": results,
    }


# --- golden case runner ------------------------------------------------------

def _golden_files(root: Path, skill: str | None) -> list[Path]:
    base = root / "evals" / "golden"
    pattern = f"{skill}/*.yaml" if skill else "*/*.yaml"
    return sorted(base.glob(pattern))


def run_golden(root: Path = ROOT, skill: str | None = None) -> list[dict[str, Any]]:
    out = []
    for path in _golden_files(root, skill):
        case = load_yaml(path)
        case_skill = case.get("skill", "")
        rubric = load_rubric(case_skill, root)
        result = score_output(str(case.get("output", "")), rubric)
        expect_pass = str(case.get("expect", "pass")) == "pass"
        out.append({
            "case_id": case.get("case_id", path.stem),
            "skill": case_skill,
            "path": path.relative_to(root).as_posix(),
            "expect_pass": expect_pass,
            "actual_pass": result["passed"],
            "match": result["passed"] == expect_pass,
            "result": result,
        })
    return out


def _format_scorecard(result: dict[str, Any]) -> str:
    lines = [f"score {result['score']}/{result['max']} ({result['pct']:.0%}) → "
             f"{'PASS' if result['passed'] else 'FAIL'}"]
    for c in result["criteria"]:
        mark = "✓" if c["passed"] else "✗"
        req = " (required)" if c["required"] else ""
        lines.append(f"  {mark} {c['id']}{req}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="run all golden cases; exit non-zero on any expect/actual mismatch")
    parser.add_argument("--skill", default=None, help="limit to one skill")
    parser.add_argument("--score", default=None, metavar="FILE",
                        help="score an arbitrary output file against --skill's rubric")
    args = parser.parse_args(argv)

    if args.score:
        if not args.skill:
            print("--score requires --skill", file=sys.stderr)
            return 2
        text = Path(args.score).read_text(encoding="utf-8")
        result = score_output(text, load_rubric(args.skill))
        print(f"{args.score} [{args.skill}]")
        print(_format_scorecard(result))
        return 0 if result["passed"] else 1

    cases = run_golden(ROOT, args.skill)
    mismatches = [c for c in cases if not c["match"]]
    for c in cases:
        status = "OK " if c["match"] else "BAD"
        exp = "pass" if c["expect_pass"] else "fail"
        act = "pass" if c["actual_pass"] else "fail"
        print(f"[{status}] {c['case_id']} ({c['skill']}): expect={exp} actual={act} "
              f"({c['result']['pct']:.0%})")
    print(f"\n{len(cases)} cases, {len(mismatches)} mismatch(es).")
    if args.check and mismatches:
        print("FAILED: rubric/golden drift — a golden case no longer scores as expected.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
