#!/usr/bin/env python3
"""Eval runner — executable evals for skill outputs (G-B).

Turns skills/*/eval_examples.md (prose good/bad examples) into *executable*
regression evals, closing the "可量化" gap: GATE_POLICY is a manual checklist
and governance_metrics.py measures operations, not output quality. This scores
output *quality* against each skill's definition-of-done rubric.

Two judges:
  * rule  (default) — deterministic structural checks derived from the rubric.
            Reproducible, no network, CI-safe. This is the CI baseline.
  * llm   (--judge llm) — semantic LLM-as-judge, wired to the Anthropic Messages
            API via the stdlib (no third-party dependency). Runs ONLY when
            ANTHROPIC_API_KEY is set; with no key (CI / offline) it prints a
            notice and falls back to `rule`, so CI never touches the network and
            behaves bit-identically to the rule judge. Any provider/parse error
            during scoring also falls back to `rule` per case. The LLM judge is
            calibrated against the same gold/bad examples each case carries.

Modes:
  * default (calibration): for every case, score its gold_example (must PASS)
            and bad_example (must FAIL). This proves the rubric discriminates —
            the "calibrate judge against a gold set" practice. Exit 1 if any
            case fails calibration.
  * --candidate FILE --case CASE_ID: score a real output file against one case.

Usage:
  python scripts/run_evals.py                 # calibrate all cases (rule judge)
  python scripts/run_evals.py --json
  python scripts/run_evals.py --candidate outputs/drafts/x.md --case research-taiwan-sme
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
EVALS_DIR = ROOT / "evals"

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")


# --- Markdown structural helpers ------------------------------------------


@dataclass
class Section:
    level: int
    heading: str
    body: str


def parse_sections(text: str) -> list[Section]:
    sections: list[Section] = []
    cur: Section | None = None
    buf: list[str] = []
    for line in (text or "").splitlines():
        m = HEADING_RE.match(line)
        if m:
            if cur is not None:
                cur.body = "\n".join(buf).strip()
                sections.append(cur)
            cur = Section(level=len(m.group(1)), heading=m.group(2).strip(), body="")
            buf = []
        else:
            buf.append(line)
    if cur is not None:
        cur.body = "\n".join(buf).strip()
        sections.append(cur)
    return sections


def first_h2(sections: list[Section]) -> Section | None:
    for s in sections:
        if s.level == 2:
            return s
    return None


# --- Rubric checks ---------------------------------------------------------
# Each returns True if the candidate satisfies the rubric item.


def _check_section_first(text, sections, args) -> bool:
    h2 = first_h2(sections)
    return bool(h2 and args["heading"] in h2.heading)


def _check_section_nonempty(text, sections, args) -> bool:
    want = args["heading"]
    return any(want in s.heading and s.body.strip() for s in sections)


def _check_all_headings(text, sections, args) -> bool:
    headings = [s.heading for s in sections]
    return all(any(want in h for h in headings) for want in args["headings"])


def _check_contains_any(text, sections, args) -> bool:
    return any(n in text for n in args["needles"])


def _check_regex(text, sections, args) -> bool:
    return re.search(args["pattern"], text) is not None


CHECKS = {
    "section_first": _check_section_first,
    "section_nonempty": _check_section_nonempty,
    "all_headings": _check_all_headings,
    "contains_any": _check_contains_any,
    "regex": _check_regex,
}


@dataclass
class ScoreResult:
    case_id: str
    score: float
    passed: bool
    items: dict = field(default_factory=dict)  # rubric_id -> bool


def score_text(case: dict, text: str, threshold: float = 1.0) -> ScoreResult:
    sections = parse_sections(text)
    items: dict[str, bool] = {}
    for item in case.get("rubric", []):
        fn = CHECKS.get(item["kind"])
        if fn is None:
            raise ValueError(f"unknown rubric kind: {item['kind']}")
        items[item["id"]] = bool(fn(text, sections, item.get("args", {})))
    total = len(items) or 1
    score = sum(1 for v in items.values() if v) / total
    return ScoreResult(case["case_id"], round(score, 3), score >= threshold, items)


# --- LLM judge (semantic layer) -------------------------------------------
# Wired to the Anthropic Messages API via the stdlib. Reached ONLY when a key
# is present; the seam functions (`_llm_available`, `_call_anthropic`) are the
# monkeypatch points for the offline tests.

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
# Judge model is configurable so the harness can pin/upgrade without code edits.
JUDGE_MODEL = os.environ.get("EVAL_JUDGE_MODEL", "claude-sonnet-5")


def _llm_available() -> bool:
    """True when a provider call is possible (API key present)."""
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def _call_anthropic(prompt: str) -> str:
    """POST `prompt` to the Messages API and return the assistant text.

    Uses only the stdlib (urllib) — no third-party SDK, so CI needs no extra
    dependency and never installs one. Only invoked when ANTHROPIC_API_KEY is
    set, so the network is never touched in CI. Raises on transport/HTTP errors;
    the caller (`_judge_score`) turns any exception into a per-case rule fallback.
    """
    body = json.dumps(
        {
            "model": JUDGE_MODEL,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=body,
        headers={
            "content-type": "application/json",
            "x-api-key": os.environ["ANTHROPIC_API_KEY"],
            "anthropic-version": ANTHROPIC_VERSION,
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310 (fixed host)
        payload = json.loads(resp.read().decode("utf-8"))
    parts = [b.get("text", "") for b in payload.get("content", []) if b.get("type") == "text"]
    return "".join(parts)


def _build_judge_prompt(case: dict, text: str) -> str:
    dod = "\n".join(f"- {d}" for d in case.get("definition_of_done", [])) or "-（未提供）"
    rubric = case.get("rubric", [])
    rubric_lines = "\n".join(f"  - {item['id']}（{item.get('kind', '')}）" for item in rubric)
    ids = [item["id"] for item in rubric]
    keys = ", ".join(f'"{i}": true|false' for i in ids)
    return (
        "你是一人公司 harness 的產出品質評審。依 definition_of_done 與 rubric，"
        "逐項判斷候選輸出是否在『語意上』滿足（不只結構符合）。\n\n"
        f"## definition_of_done\n{dod}\n\n"
        f"## rubric（逐項 pass/fail）\n{rubric_lines}\n\n"
        f"## 候選輸出\n{text}\n\n"
        f'只回傳 JSON，格式 {{"items": {{{keys}}}}}，不要任何其他文字。'
    )


def _parse_judge_json(raw: str) -> dict:
    """Extract the first JSON object from the model reply and validate shape."""
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        raise ValueError(f"judge returned no JSON object: {raw!r}")
    data = json.loads(m.group(0))
    if not isinstance(data, dict) or not isinstance(data.get("items"), dict):
        raise ValueError(f"judge JSON missing items map: {data!r}")
    return data


def llm_score_text(case: dict, text: str, threshold: float = 1.0) -> ScoreResult:
    """Score `text` with the LLM judge. Raises on provider/parse failure."""
    data = _parse_judge_json(_call_anthropic(_build_judge_prompt(case, text)))
    items = {item["id"]: bool(data["items"].get(item["id"], False)) for item in case.get("rubric", [])}
    total = len(items) or 1
    score = sum(1 for v in items.values() if v) / total
    return ScoreResult(case["case_id"], round(score, 3), score >= threshold, items)


def _judge_score(case: dict, text: str, judge: str, threshold: float = 1.0) -> ScoreResult:
    """Dispatch to the requested judge; fall back to rule on any llm failure."""
    if judge == "llm":
        try:
            return llm_score_text(case, text, threshold)
        except Exception as exc:  # provider/parse/transport → offline-safe fallback
            print(
                f"warning: llm judge failed for {case.get('case_id')} ({exc}); "
                "falling back to rule judge for this case",
                file=sys.stderr,
            )
    return score_text(case, text, threshold)


# --- Loading ---------------------------------------------------------------


def load_cases() -> list[dict]:
    cases = []
    for path in sorted(EVALS_DIR.glob("**/*.yaml")):
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(doc, dict) and doc.get("case_id"):
            doc["_path"] = str(path.relative_to(ROOT))
            cases.append(doc)
    return cases


# --- Runner ----------------------------------------------------------------


def calibrate(cases: list[dict], judge: str) -> tuple[list[dict], bool]:
    rows = []
    ok = True
    for case in cases:
        gold = _judge_score(case, case.get("gold_example", ""), judge)
        bad = _judge_score(case, case.get("bad_example", ""), judge)
        case_ok = gold.passed and not bad.passed
        ok = ok and case_ok
        rows.append(
            {
                "case_id": case["case_id"],
                "skill": case.get("skill"),
                "judge": judge,
                "gold_score": gold.score,
                "gold_passed": gold.passed,
                "bad_score": bad.score,
                "bad_passed": bad.passed,
                "calibration_ok": case_ok,
            }
        )
    return rows, ok


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Run executable skill-output evals (G-B).")
    ap.add_argument("--judge", choices=["rule", "llm"], default="rule")
    ap.add_argument("--candidate", help="score this output file against --case")
    ap.add_argument("--case", help="case_id to score the candidate against")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv[1:])

    if args.judge == "llm" and not _llm_available():
        print("note: --judge llm requested but ANTHROPIC_API_KEY not set; falling back to rule judge", file=sys.stderr)
        args.judge = "rule"

    cases = load_cases()
    if not cases:
        print(f"no eval cases found under {EVALS_DIR}", file=sys.stderr)
        return 2

    if args.candidate:
        if not args.case:
            print("--candidate requires --case CASE_ID", file=sys.stderr)
            return 2
        case = next((c for c in cases if c["case_id"] == args.case), None)
        if case is None:
            print(f"unknown case: {args.case}", file=sys.stderr)
            return 2
        res = _judge_score(case, Path(args.candidate).read_text(encoding="utf-8"), args.judge)
        payload = {"case_id": res.case_id, "score": res.score, "passed": res.passed, "items": res.items}
        print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else
              f"{res.case_id}: score={res.score} passed={res.passed} items={res.items}")
        return 0 if res.passed else 1

    rows, ok = calibrate(cases, args.judge)
    if args.json:
        print(json.dumps({"cases": rows, "ok": ok}, ensure_ascii=False, indent=2))
    else:
        print(f"Eval calibration ({len(rows)} cases, judge={args.judge}):")
        for r in rows:
            mark = "OK " if r["calibration_ok"] else "BAD"
            print(f"  [{mark}] {r['case_id']:<24} gold={r['gold_score']}/pass={r['gold_passed']} "
                  f"bad={r['bad_score']}/pass={r['bad_passed']}")
        print("OK: all cases discriminate gold from bad" if ok else
              "FAILED: some cases do not discriminate gold from bad")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
