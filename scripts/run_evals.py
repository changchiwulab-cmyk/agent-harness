#!/usr/bin/env python3
"""Evaluation Plane runner — rubric 自評＋schema 守護.

機制（見 system/EVAL_POLICY.yaml）：
    評分由 Claude 依 rubric 維度填 evals/results/*.yaml（judge: rubric_self）。
    本腳本是 deterministic 守門：重算 score_pct/verdict、比對 golden 回歸。

用法：
    run_evals.py --check                     驗證所有 results（schema＋verdict 重算＋golden 回歸）。CI 用。
    run_evals.py --scaffold <target> <skill> 依 skill rubric 產空白評分卡（含 auto_signal 命中提示）。
    run_evals.py --judge <target> <skill>    LLM-as-judge（v2 保留，尚未實作）。

Exit code:
    0 = OK
    1 = 驗證/回歸失敗
    2 = 採集錯誤（缺檔、解析失敗、未知 skill）
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
RUBRICS_DIR = ROOT / "evals" / "rubrics"
RESULTS_DIR = ROOT / "evals" / "results"
GOLDEN_FILE = ROOT / "evals" / "golden" / "cases.yaml"

VALID_SKILLS = ("research", "analysis", "writing", "ops", "review")
VALID_JUDGES = ("rubric_self", "llm_judge")
VALID_SCORES = (0, 1, 2)
VALID_VERDICTS = ("fail", "partial", "pass")
VERDICT_RANK = {"fail": 0, "partial": 1, "pass": 2}
DEFAULT_PASS_THRESHOLD = 80

REQUIRED_RECORD_FIELDS = (
    "eval_id", "task_id", "skill_type", "target",
    "judge", "scored_at", "dimensions", "score_pct", "verdict",
)


# --- Loaders ---------------------------------------------------------------


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_rubric(skill: str, rubrics_dir: Path = RUBRICS_DIR) -> dict:
    path = rubrics_dir / f"{skill}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"rubric not found for skill '{skill}': {path}")
    data = load_yaml(path)
    if not isinstance(data, dict) or not isinstance(data.get("dimensions"), list):
        raise ValueError(f"{path}: rubric must be a mapping with a 'dimensions' list")
    return data


def unwrap_record(doc: Any) -> dict:
    """Accept either {eval_record: {...}} wrapper or a bare record mapping."""
    if isinstance(doc, dict) and isinstance(doc.get("eval_record"), dict):
        return doc["eval_record"]
    return doc if isinstance(doc, dict) else {}


def load_results(results_dir: Path = RESULTS_DIR) -> list[tuple[str, dict]]:
    out: list[tuple[str, dict]] = []
    if not results_dir.exists():
        return out
    for p in sorted(results_dir.glob("*.yaml")):
        out.append((p.name, unwrap_record(load_yaml(p))))
    return out


def load_golden(golden_file: Path = GOLDEN_FILE) -> list[dict]:
    if not golden_file.exists():
        return []
    data = load_yaml(golden_file)
    cases = data.get("golden_cases") if isinstance(data, dict) else None
    return [c for c in cases if isinstance(c, dict)] if isinstance(cases, list) else []


# --- Pure scoring core (deterministic guard) -------------------------------


def compute_score_pct(scores: list[int]) -> float:
    if not scores:
        return 0.0
    return round(100 * sum(scores) / (2 * len(scores)), 1)


def compute_verdict(dim_scores: dict[str, int], rubric: dict) -> tuple[float, str]:
    """Recompute (score_pct, verdict) from scores + rubric blocker/threshold.

    Mirrors system/EVAL_POLICY.yaml verdict_rules so --check can guard the
    recorded verdict against drift.
    """
    threshold = rubric.get("pass_threshold", DEFAULT_PASS_THRESHOLD)
    blockers = {d["id"] for d in rubric["dimensions"] if d.get("blocker")}
    scores = list(dim_scores.values())
    pct = compute_score_pct(scores)
    blocker_failed = any(dim_scores.get(b, 2) == 0 for b in blockers)
    if pct < 60 or blocker_failed:
        verdict = "fail"
    elif pct < threshold:
        verdict = "partial"
    else:
        verdict = "pass"
    return pct, verdict


# --- Validation ------------------------------------------------------------


def validate_rubric(skill: str, rubric: dict) -> list[str]:
    errs: list[str] = []
    ids = [d.get("id") for d in rubric["dimensions"]]
    if any(not i for i in ids):
        errs.append(f"rubric {skill}: every dimension needs a non-empty id")
    if len(ids) != len(set(ids)):
        errs.append(f"rubric {skill}: duplicate dimension ids {ids}")
    return errs


def validate_result(name: str, rec: dict, rubrics: dict[str, dict]) -> list[str]:
    errs: list[str] = []

    for field in REQUIRED_RECORD_FIELDS:
        val = rec.get(field)
        empty = val is None or (isinstance(val, str) and not val.strip()) or (
            isinstance(val, (list, dict)) and not val
        )
        if empty:
            errs.append(f"{name}: missing required field '{field}'")
    if errs:
        return errs  # without core fields, deeper checks are noise

    skill = rec["skill_type"]
    if skill not in VALID_SKILLS:
        errs.append(f"{name}: invalid skill_type '{skill}'")
        return errs
    if rec["judge"] not in VALID_JUDGES:
        errs.append(f"{name}: invalid judge '{rec['judge']}' (allowed: {'/'.join(VALID_JUDGES)})")
    if skill not in rubrics:
        errs.append(f"{name}: no rubric loaded for skill '{skill}'")
        return errs

    rubric = rubrics[skill]
    rubric_ids = [d["id"] for d in rubric["dimensions"]]

    dims = rec["dimensions"]
    if not isinstance(dims, list):
        errs.append(f"{name}: dimensions must be a list")
        return errs

    dim_scores: dict[str, int] = {}
    for i, d in enumerate(dims):
        if not isinstance(d, dict):
            errs.append(f"{name}: dimensions[{i}] must be a mapping")
            continue
        did, score = d.get("id"), d.get("score")
        if score not in VALID_SCORES:
            errs.append(f"{name}: dimension '{did}' score {score!r} not in {VALID_SCORES}")
        if did in dim_scores:
            errs.append(f"{name}: duplicate dimension '{did}'")
        dim_scores[did] = score if score in VALID_SCORES else 0

    missing = [i for i in rubric_ids if i not in dim_scores]
    extra = [i for i in dim_scores if i not in rubric_ids]
    if missing:
        errs.append(f"{name}: missing rubric dimensions {missing}")
    if extra:
        errs.append(f"{name}: unknown dimensions not in rubric {extra}")
    if missing or extra:
        return errs  # verdict recompute meaningless without full coverage

    exp_pct, exp_verdict = compute_verdict(dim_scores, rubric)
    if abs(float(rec["score_pct"]) - exp_pct) > 0.05:
        errs.append(f"{name}: score_pct {rec['score_pct']} != recomputed {exp_pct}")
    if rec["verdict"] not in VALID_VERDICTS:
        errs.append(f"{name}: invalid verdict '{rec['verdict']}'")
    elif rec["verdict"] != exp_verdict:
        errs.append(f"{name}: verdict '{rec['verdict']}' != recomputed '{exp_verdict}'")
    return errs


def check_golden_regression(results: list[tuple[str, dict]], golden: list[dict]) -> list[str]:
    errs: list[str] = []
    by_target: dict[str, list[tuple[str, dict]]] = {}
    for name, rec in results:
        tgt = rec.get("target")
        if tgt:
            by_target.setdefault(tgt, []).append((name, rec))
    for case in golden:
        tgt = case.get("target")
        exp = case.get("expected_verdict")
        if exp not in VERDICT_RANK:
            errs.append(f"golden {case.get('case_id')}: invalid expected_verdict '{exp}'")
            continue
        for name, rec in by_target.get(tgt, []):
            got = rec.get("verdict")
            if VERDICT_RANK.get(got, -1) < VERDICT_RANK[exp]:
                errs.append(
                    f"golden regression: {name} verdict '{got}' below expected "
                    f"'{exp}' for {tgt} (case {case.get('case_id')})"
                )
    return errs


# --- Commands --------------------------------------------------------------


def cmd_check(root: Path = ROOT) -> int:
    rubrics_dir = root / "evals" / "rubrics"
    results_dir = root / "evals" / "results"
    golden_file = root / "evals" / "golden" / "cases.yaml"

    errors: list[str] = []
    rubrics: dict[str, dict] = {}
    for skill in VALID_SKILLS:
        try:
            rubrics[skill] = load_rubric(skill, rubrics_dir)
            errors.extend(validate_rubric(skill, rubrics[skill]))
        except (FileNotFoundError, ValueError, yaml.YAMLError) as exc:
            errors.append(str(exc))

    try:
        results = load_results(results_dir)
    except yaml.YAMLError as exc:
        print(f"ERROR: results parse failure: {exc}", file=sys.stderr)
        return 2

    for name, rec in results:
        errors.extend(validate_result(name, rec, rubrics))
    errors.extend(check_golden_regression(results, load_golden(golden_file)))

    if errors:
        print("FAILED: eval checks found issues:")
        for e in errors:
            print(f"- {e}")
        return 1
    print(f"OK: eval checks passed ({len(results)} result(s), {len(rubrics)} rubric(s))")
    return 0


def cmd_scaffold(target: str, skill: str, root: Path = ROOT) -> int:
    if skill not in VALID_SKILLS:
        print(f"ERROR: unknown skill '{skill}' (allowed: {'/'.join(VALID_SKILLS)})", file=sys.stderr)
        return 2
    try:
        rubric = load_rubric(skill, root / "evals" / "rubrics")
    except (FileNotFoundError, ValueError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    target_path = root / target if not Path(target).is_absolute() else Path(target)
    text = target_path.read_text(encoding="utf-8") if target_path.exists() else ""

    print(f"# Eval scaffold — 填入每維度 score (0/1/2) 與 note，存到 evals/results/EVAL-YYYYMMDD-###_*.yaml")
    print(f"# 機制：rubric 自評（見 system/EVAL_POLICY.yaml）。填完跑 run_evals.py --check 守門。")
    print("eval_record:")
    print('  eval_id: "EVAL-YYYYMMDD-001"')
    print('  task_id: ""')
    print(f'  skill_type: "{skill}"')
    print(f'  target: "{target}"')
    print(f'  rubric: "evals/rubrics/{skill}.yaml"')
    print('  judge: "rubric_self"')
    print('  scored_at: "YYYY-MM-DD"')
    print("  dimensions:")
    for d in rubric["dimensions"]:
        signals = d.get("auto_signal") or []
        hits = [s for s in signals if s in text] if text else []
        blocker = " [blocker]" if d.get("blocker") else ""
        print(f'    - id: {d["id"]}            # {d.get("name", "")}{blocker}')
        print(f"      score:                  # 2=通過 / 1=部分 / 0=不通過 ｜ 通過標準：{d.get('pass', '')}")
        print('      note: ""')
        if signals:
            status = f"命中 {hits}" if hits else "未命中（可能扣分訊號）"
            print(f"      # auto_signal {signals} → {status}")
    print("  score_pct: 0.0            # run_evals.py --check 會重算守門")
    print('  verdict: ""              # pass/partial/fail，--check 會重算守門')
    print('  notes: ""')
    return 0


def cmd_judge(target: str, skill: str) -> int:
    print(
        "llm_judge 為 v2 保留介面，尚未實作（見 system/EVAL_POLICY.yaml judges.llm_judge）。\n"
        "v1 請用 --scaffold 產評分卡、人工/Claude 依 rubric 自評後 --check 守門。",
        file=sys.stderr,
    )
    return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluation Plane runner (rubric 自評＋schema 守護).")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="驗證所有 results（CI 用）。")
    group.add_argument("--scaffold", nargs=2, metavar=("TARGET", "SKILL"), help="產空白評分卡。")
    group.add_argument("--judge", nargs=2, metavar=("TARGET", "SKILL"), help="LLM-as-judge（v2 保留）。")
    args = parser.parse_args(argv)

    try:
        if args.check:
            return cmd_check()
        if args.scaffold:
            return cmd_scaffold(args.scaffold[0], args.scaffold[1])
        if args.judge:
            return cmd_judge(args.judge[0], args.judge[1])
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
