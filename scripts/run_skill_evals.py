#!/usr/bin/env python3
"""LLM-judge skill eval harness (L5).

Upgrades the L4 structural check (scripts/check_skill_evals.py) into a real
evaluation: an LLM judge scores a candidate output against a skill's 判斷標準
rubric, criterion by criterion. The bundled good/bad examples act as a golden
regression set for the judge itself.

Design constraints (see plan §L5):
  - This is OPT-IN and must NOT gate the required `validate-spec` CI job. It runs
    on demand / via the separate .github/workflows/skill-evals.yml workflow.
  - No API key → print "skipped" and exit 0 (no network, no cost).
  - --mock runs the full parse → judge → aggregate → render plumbing offline
    with a deterministic stub judge (no anthropic SDK, no network).
  - The `anthropic` SDK is imported lazily inside the live judge only, so this
    module imports and unit-tests without the package installed.

Usage:
  python scripts/run_skill_evals.py                 # live golden run (needs ANTHROPIC_API_KEY)
  python scripts/run_skill_evals.py --skill research # one skill
  python scripts/run_skill_evals.py --mock           # offline plumbing smoke
  python scripts/run_skill_evals.py --model claude-sonnet-4-6

Exit: 0 = ok / skipped / mock; 1 = a golden assertion failed (live mode).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_skill_evals as cse  # shared parser + SKILLS_DIR

ROOT = cse.ROOT
DRAFTS_DIR = ROOT / "outputs" / "drafts"

# Per COST_POLICY.md 模型路由規則: rubric scoring is classification-shaped →
# cheapest capable model that supports structured outputs.
DEFAULT_MODEL = "claude-haiku-4-5"

# Golden thresholds — tolerant of LLM non-determinism.
GOOD_MAX_FAIL = 1   # the good exemplar may fail at most this many criteria
BAD_MIN_FAIL = 2    # the bad exemplar must fail at least this many criteria

VERDICT_SCHEMA = {
    "type": "object",
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "item": {"type": "string"},
                    "verdict": {"type": "string", "enum": ["pass", "fail"]},
                    "reason": {"type": "string"},
                },
                "required": ["item", "verdict", "reason"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["results"],
    "additionalProperties": False,
}


# --- Skill discovery + parsing ---------------------------------------------


def load_skill(skill_dir: Path) -> dict | None:
    """Return {name, good, bad, criteria} for a skill, or None if no eval file."""
    evals = skill_dir / "eval_examples.md"
    if not evals.exists():
        return None
    parsed = cse.parse_eval_examples(evals.read_text(encoding="utf-8"))
    if not parsed["good"] or not parsed["bad"] or not parsed["criteria"]:
        return None
    return {"name": skill_dir.name, **parsed}


def discover_skills(only: str | None = None) -> list[dict]:
    skills = []
    for d in sorted(p for p in cse.SKILLS_DIR.iterdir() if p.is_dir()):
        if only and d.name != only:
            continue
        s = load_skill(d)
        if s:
            skills.append(s)
    return skills


# --- Judges -----------------------------------------------------------------


def _build_prompt(skill: str, criteria: list[dict], candidate: str) -> str:
    rubric_lines = [
        f"- {c['item']}：通過＝{c['pass']}｜不通過＝{c['fail']}" for c in criteria
    ]
    return (
        f"你是嚴格的品質評審。針對 `{skill}` skill 的候選輸出，依下列『判斷標準』"
        "逐條判定通過（pass）或不通過（fail）。只依標準評，不加標準以外的要求；"
        "對每條給一句具體理由。\n\n"
        "判斷標準：\n" + "\n".join(rubric_lines) + "\n\n"
        "候選輸出：\n```\n" + candidate + "\n```\n\n"
        "回傳每條標準的 item / verdict / reason。"
    )


def anthropic_judge(skill: str, candidate: str, criteria: list[dict],
                    model: str = DEFAULT_MODEL) -> list[dict]:
    """Live judge: call the Anthropic API with structured outputs. Lazy import."""
    import anthropic  # lazy — keeps module importable without the SDK

    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=model,
        max_tokens=1500,
        output_config={"format": {"type": "json_schema", "schema": VERDICT_SCHEMA}},
        messages=[{"role": "user", "content": _build_prompt(skill, criteria, candidate)}],
    )
    text = next((b.text for b in resp.content if getattr(b, "type", "") == "text"), "")
    data = json.loads(text)
    return data.get("results", [])


def mock_judge(skill: str, candidate: str, criteria: list[dict],
               model: str = DEFAULT_MODEL) -> list[dict]:
    """Offline stub: marks every criterion 'pass'. Exercises plumbing only —
    NOT a quality signal, so --mock never runs the golden assertions."""
    return [{"item": c["item"], "verdict": "pass", "reason": "mock"} for c in criteria]


# --- Aggregation + golden verdict ------------------------------------------


def aggregate(criteria: list[dict], verdicts: list[dict]) -> dict:
    """Combine judge verdicts against the criteria. Missing/unknown items = fail."""
    by_item = {v.get("item"): v for v in verdicts if isinstance(v, dict)}
    details, failed = [], 0
    for c in criteria:
        v = by_item.get(c["item"])
        verdict = (v or {}).get("verdict")
        ok = verdict == "pass"
        if not ok:
            failed += 1
        details.append({
            "item": c["item"],
            "verdict": "pass" if ok else "fail",
            "reason": (v or {}).get("reason", "judge omitted this criterion"),
        })
    total = len(criteria)
    return {"total": total, "passed": total - failed, "failed": failed, "details": details}


def golden_verdict(good_agg: dict, bad_agg: dict) -> tuple[bool, list[str]]:
    """A judge passes the golden set if good fails ≤GOOD_MAX_FAIL and bad fails ≥BAD_MIN_FAIL."""
    reasons = []
    if good_agg["failed"] > GOOD_MAX_FAIL:
        reasons.append(
            f"good 範例不該被判失敗 {good_agg['failed']} 條（容忍 ≤{GOOD_MAX_FAIL}）"
        )
    if bad_agg["failed"] < BAD_MIN_FAIL:
        reasons.append(
            f"bad 範例只被抓出 {bad_agg['failed']} 條問題（需 ≥{BAD_MIN_FAIL}）"
        )
    return (not reasons), reasons


def run_golden(skills: list[dict], judge) -> list[dict]:
    """Run the golden regression for each skill; return per-skill result dicts."""
    out = []
    for s in skills:
        good_agg = aggregate(s["criteria"], judge(s["name"], s["good"], s["criteria"]))
        bad_agg = aggregate(s["criteria"], judge(s["name"], s["bad"], s["criteria"]))
        ok, reasons = golden_verdict(good_agg, bad_agg)
        out.append({"skill": s["name"], "ok": ok, "reasons": reasons,
                    "good": good_agg, "bad": bad_agg})
    return out


# --- Reporting --------------------------------------------------------------


def render_markdown(results: list[dict], model: str, today: date) -> str:
    lines = [
        f"# Skill Evals — LLM-judge 回歸（{today.isoformat()}）",
        "",
        f"- judge 模型：`{model}`（依 COST_POLICY 模型路由，評分用 Haiku 等級）",
        f"- golden 閾值：good 失敗 ≤{GOOD_MAX_FAIL}、bad 失敗 ≥{BAD_MIN_FAIL}",
        "",
        "| skill | golden | good 通過 | bad 抓出問題 | 備註 |",
        "|-------|:------:|:---------:|:-----------:|------|",
    ]
    for r in results:
        badge = "✅" if r["ok"] else "🚨"
        note = "；".join(r["reasons"]) if r["reasons"] else "—"
        lines.append(
            f"| {r['skill']} | {badge} | {r['good']['passed']}/{r['good']['total']} "
            f"| {r['bad']['failed']}/{r['bad']['total']} | {note} |"
        )
    lines.append("")
    return "\n".join(lines) + "\n"


# --- Main -------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="LLM-judge skill eval harness (L5).")
    parser.add_argument("--skill", help="只評單一 skill（預設全部）")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="judge 模型 id")
    parser.add_argument("--mock", action="store_true", help="離線 plumbing smoke（不觸網、不評質量）")
    parser.add_argument("--today", help="覆寫日期 YYYY-MM-DD（測試用）")
    parser.add_argument("--no-write", action="store_true", help="不寫 scorecard 草稿")
    args = parser.parse_args(argv)

    today = date.fromisoformat(args.today) if args.today else date.today()
    skills = discover_skills(args.skill)
    if not skills:
        print("沒有可評的 skill（缺 eval_examples / 判斷標準）")
        return 0

    if args.mock:
        results = run_golden(skills, mock_judge)
        print(render_markdown(results, f"{args.model} (mock)", today))
        print("（--mock：僅驗 plumbing，未做質量斷言）")
        return 0

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("skipped：未設定 ANTHROPIC_API_KEY，跳過 LLM-judge（live 評估走 skill-evals.yml）")
        return 0

    def judge(skill, candidate, criteria):
        return anthropic_judge(skill, candidate, criteria, model=args.model)

    results = run_golden(skills, judge)
    report = render_markdown(results, args.model, today)
    print(report)

    if not args.no_write:
        DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
        out = DRAFTS_DIR / f"{today.isoformat()}_skill-evals-run.md"
        out.write_text(report, encoding="utf-8")
        print(f"scorecard → {out.relative_to(ROOT)}")

    failed = [r["skill"] for r in results if not r["ok"]]
    if failed:
        print(f"❌ golden 回歸失敗：{failed}", file=sys.stderr)
        return 1
    print("OK: 所有 skill 通過 golden 回歸")
    return 0


if __name__ == "__main__":
    sys.exit(main())
