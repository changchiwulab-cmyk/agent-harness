#!/usr/bin/env python3
"""Eval runner — 把靜態 eval_examples 升級為可執行的確定性評分。

設計（嚴守 harness 哲學）:
- auto_checks  = 確定性結構檢查（conclusion-first / 結構 / 來源），本腳本跑、可入 CI gate。
- judge_checks = 內容語意判斷（來源真實性、量化、誠實…），屬 LLM-as-judge / 人工，
  本腳本只把它們列為 `judge_pending`，不自動評分（成本與 draft-first 哲學）。

用法:
    python scripts/run_evals.py                 # 跑 regression manifest，印摘要 + 寫 scorecard
    python scripts/run_evals.py --no-write       # 只印摘要不寫檔
    python scripts/run_evals.py --out PATH        # 自訂 scorecard 路徑

退出碼: 0 全 case 通過 / 1 有 case 未通過 / 2 設定錯誤（缺 rubric、manifest 解析失敗）。

scorecard 為確定性輸出（無 wall-clock timestamp、key 排序），可安全 commit 為證據。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
RUBRICS_DIR = ROOT / "evals" / "rubrics"
MANIFEST = ROOT / "evals" / "regression" / "manifest.yaml"
DEFAULT_OUT = ROOT / "logs" / "evals" / "scorecard-latest.yaml"

ALLOWED_SKILL = {"research", "analysis", "writing", "ops", "review"}
HEAD_LINES = 80
MIN_BYTES = 200


# ── 純函式（可單元測試）─────────────────────────────────────────────────────

def load_yaml(path: Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_rubric(rubrics_dir: Path, skill: str) -> dict[str, Any]:
    """讀取並回傳某 skill 的 rubric mapping；找不到/格式錯則 raise。"""
    path = Path(rubrics_dir) / f"{skill}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"missing rubric for skill '{skill}': {path}")
    doc = load_yaml(path)
    rubric = doc.get("rubric") if isinstance(doc, dict) else None
    if not isinstance(rubric, dict):
        raise ValueError(f"{path}: top-level 'rubric' mapping required")
    return rubric


def has_marker(text: str, markers: list[str]) -> bool:
    return any(m in text for m in markers)


def evaluate_content(content: str, rubric: dict[str, Any]) -> dict[str, Any]:
    """對單份文字內容套 rubric 的 auto_checks，回傳確定性結果（純函式）。"""
    head = "\n".join(content.splitlines()[:HEAD_LINES])
    auto_results: list[dict[str, Any]] = []
    for check in rubric.get("auto_checks", []):
        scope = check.get("scope", "full")
        haystack = head if scope == "head" else content
        passed = has_marker(haystack, check.get("any_markers", []))
        auto_results.append({"id": check.get("id"), "result": "pass" if passed else "fail"})
    total = len(auto_results)
    passed = sum(1 for r in auto_results if r["result"] == "pass")
    ratio = round(passed / total, 3) if total else 1.0
    first_nonempty = next((ln for ln in content.splitlines() if ln.strip()), "")
    return {
        "has_title": first_nonempty.startswith("#"),
        "auto_results": auto_results,
        "auto_pass_ratio": ratio,
        "judge_pending": [c.get("id") for c in rubric.get("judge_checks", [])],
    }


def evaluate_single(output_path: str | Path, skill: str, rubrics_dir: Path = RUBRICS_DIR) -> dict[str, Any]:
    """評分單一產出檔（per-output 模式；供 GATE completion 評『本任務實際產出』）。

    含檔案存在性 / 非空 / 標題 + rubric auto_checks 門檻。skill 無效則 raise ValueError。
    """
    if skill not in ALLOWED_SKILL:
        raise ValueError(f"invalid skill '{skill}' (allowed: {sorted(ALLOWED_SKILL)})")
    path = Path(output_path)
    result: dict[str, Any] = {"output_path": str(output_path), "skill": skill, "passed": False}

    if not path.exists():
        result["reason"] = "output_missing"
        return result
    content = path.read_text(encoding="utf-8")
    if len(content.encode("utf-8")) < MIN_BYTES:
        result["reason"] = "output_too_short"
        return result

    rubric = load_rubric(rubrics_dir, skill)
    ev = evaluate_content(content, rubric)
    min_ratio = float(rubric.get("min_auto_pass_ratio", 0.5))
    result.update(ev)
    result["passed"] = bool(ev["has_title"] and ev["auto_pass_ratio"] >= min_ratio)
    if not result["passed"]:
        result["reason"] = "below_auto_threshold" if ev["has_title"] else "no_title"
    return result


def evaluate_case(root: Path, case: dict[str, Any], rubrics_dir: Path) -> dict[str, Any]:
    """評估單一 regression case（委派 evaluate_single，路徑相對 root 解析）。"""
    out_rel = case.get("output_path", "")
    result = evaluate_single(Path(root) / out_rel, case.get("skill"), rubrics_dir)
    result["case_id"] = case.get("case_id")
    result["output_path"] = out_rel  # 保留相對路徑，維持 scorecard 確定性
    return result


def run(root: Path = ROOT, manifest: Path = MANIFEST, rubrics_dir: Path = RUBRICS_DIR) -> dict[str, Any]:
    """跑整個 regression set，回傳確定性 scorecard dict。"""
    doc = load_yaml(manifest)
    rs = doc.get("regression_set") if isinstance(doc, dict) else None
    if not isinstance(rs, dict) or not isinstance(rs.get("cases"), list):
        raise ValueError(f"{manifest}: 'regression_set.cases' list required")

    cases = sorted(rs["cases"], key=lambda c: str(c.get("case_id")))
    case_results = [evaluate_case(root, c, rubrics_dir) for c in cases]

    auto_total = sum(len(r.get("auto_results", [])) for r in case_results)
    auto_passed = sum(
        1 for r in case_results for a in r.get("auto_results", []) if a["result"] == "pass"
    )
    judge_pending = sum(len(r.get("judge_pending", [])) for r in case_results)
    return {
        "scorecard": {
            "summary": {
                "cases_total": len(case_results),
                "cases_passed": sum(1 for r in case_results if r["passed"]),
                "auto_checks_total": auto_total,
                "auto_checks_passed": auto_passed,
                "judge_checks_pending": judge_pending,
            },
            "cases": case_results,
        }
    }


def dump(scorecard: dict[str, Any]) -> str:
    return yaml.safe_dump(scorecard, allow_unicode=True, sort_keys=True, default_flow_style=False)


# ── CLI ─────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run eval regression set / per-output gate")
    parser.add_argument("--output", default=None, help="per-output 模式：評單一產出檔（需搭配 --skill）")
    parser.add_argument("--skill", default=None, help="per-output 模式的 skill（research/analysis/writing/ops/review）")
    parser.add_argument("--no-write", action="store_true", help="只印摘要不寫 scorecard")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="scorecard 輸出路徑")
    args = parser.parse_args(argv)

    # per-output 模式（GATE completion 用：評本任務實際產出，非 regression）
    if args.output:
        if not args.skill:
            print("ERROR: --output 需搭配 --skill", file=sys.stderr)
            return 2
        try:
            res = evaluate_single(args.output, args.skill)
        except (FileNotFoundError, ValueError) as e:
            print(f"CONFIG ERROR: {e}", file=sys.stderr)
            return 2
        mark = "PASS" if res["passed"] else "FAIL"
        extra = "" if res["passed"] else f" ({res.get('reason')})"
        print(f"eval [{mark}] {args.output} ({args.skill}) ratio={res.get('auto_pass_ratio')}{extra}")
        return 0 if res["passed"] else 1

    try:
        scorecard = run()
    except (FileNotFoundError, ValueError) as e:
        print(f"CONFIG ERROR: {e}", file=sys.stderr)
        return 2

    rendered = dump(scorecard)
    if not args.no_write:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered, encoding="utf-8")

    s = scorecard["scorecard"]["summary"]
    print(
        f"evals: {s['cases_passed']}/{s['cases_total']} cases passed | "
        f"auto {s['auto_checks_passed']}/{s['auto_checks_total']} | "
        f"judge_pending {s['judge_checks_pending']}"
    )
    for c in scorecard["scorecard"]["cases"]:
        mark = "PASS" if c["passed"] else "FAIL"
        extra = "" if c["passed"] else f" ({c.get('reason')})"
        print(f"  [{mark}] {c['case_id']} ({c['skill']}) ratio={c.get('auto_pass_ratio')}{extra}")

    return 0 if s["cases_passed"] == s["cases_total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
