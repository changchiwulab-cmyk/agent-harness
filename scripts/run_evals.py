#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Eval harness — 用 deterministic 規則對 skill 輸出評分。

讓既有 skills/<type>/eval_examples.md 的 golden set 真的能「跑」（regression）。
policy 見 system/EVAL_POLICY.md；rubric schema 見 skills/<type>/rubric.yaml。

依賴：PyYAML（CI 已安裝）。預設無外呼；LLM-as-judge 為可選層、本檔不實作外呼。

用法：
  python3 scripts/run_evals.py                      # regression：每個 skill 的 good 必過、bad 必不過
  python3 scripts/run_evals.py --skill research      # 只跑單一 skill 的 golden 不變式
  python3 scripts/run_evals.py --skill research --file outputs/drafts/foo.md   # 評一份實際輸出

exit 0 = 全部通過；exit 1 = 有 regression / 評分未達門檻。
"""
import argparse
import os
import re
import sys

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.stderr.write("需要 PyYAML：pip install pyyaml\n")
    sys.exit(2)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_DIR = os.path.join(ROOT, "skills")

HEADING_RE = re.compile(r'^#{1,6}\s+(.*)$', re.MULTILINE)
FENCE_RE = re.compile(r'```[a-zA-Z]*\n(.*?)```', re.DOTALL)


def discover_skills():
    """回傳所有含 rubric.yaml 的 skill 名稱（排序）。"""
    out = []
    if not os.path.isdir(SKILLS_DIR):
        return out
    for name in sorted(os.listdir(SKILLS_DIR)):
        if os.path.exists(os.path.join(SKILLS_DIR, name, "rubric.yaml")):
            out.append(name)
    return out


def load_rubric(skill):
    path = os.path.join(SKILLS_DIR, skill, "rubric.yaml")
    if not os.path.exists(path):
        raise FileNotFoundError("missing rubric: %s" % path)
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def heading_index(text, token):
    """第一個包含 token 的標題在文中的字元位置；找不到回 -1。"""
    for m in HEADING_RE.finditer(text):
        if token in m.group(1):
            return m.start()
    return -1


def section_body(text, token):
    """含 token 的標題到下一個標題之間的內文。"""
    headings = list(HEADING_RE.finditer(text))
    for i, m in enumerate(headings):
        if token in m.group(1):
            start = m.end()
            end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
            return text[start:end]
    return ""


def run_check(text, check):
    t = check.get("type")
    if t == "required_heading":
        return heading_index(text, check["token"]) >= 0
    if t == "forbidden_regex":
        return re.search(check["pattern"], text, re.MULTILINE) is None
    if t == "required_regex":
        return re.search(check["pattern"], text, re.MULTILINE) is not None
    if t == "heading_order":
        a = heading_index(text, check["before"])
        b = heading_index(text, check["after"])
        return a >= 0 and b >= 0 and a < b
    if t == "heading_nonempty":
        return section_body(text, check["token"]).strip() != ""
    raise ValueError("unknown check type: %s" % t)


def evaluate(rubric, text):
    """回傳 dict：score / passed / threshold / results / n_pass / total。"""
    text = text or ""
    checks = rubric.get("checks", []) or []
    results = []
    for c in checks:
        try:
            passed = run_check(text, c)
        except Exception:
            passed = False
        results.append((c.get("id", c.get("type")), bool(passed), c.get("desc", "")))
    total = len(results)
    n_pass = sum(1 for _, p, _ in results if p)
    score = (n_pass / total) if total else 0.0
    threshold = float(rubric.get("pass_threshold", 0.8))
    return {
        "score": score,
        "passed": score >= threshold,
        "threshold": threshold,
        "results": results,
        "n_pass": n_pass,
        "total": total,
    }


def _first_block_after(md, heading_token):
    """eval_examples.md 中，指定標題後第一個 ``` 圍欄碼塊的內文。"""
    hidx = -1
    for m in HEADING_RE.finditer(md):
        if heading_token in m.group(1):
            hidx = m.end()
            break
    if hidx < 0:
        return None
    fence = FENCE_RE.search(md[hidx:])
    return fence.group(1) if fence else None


def extract_examples(skill):
    """從 skills/<skill>/eval_examples.md 取出 good / bad 範例文字。"""
    path = os.path.join(SKILLS_DIR, skill, "eval_examples.md")
    with open(path, encoding="utf-8") as f:
        md = f.read()
    return {
        "good": _first_block_after(md, "好的輸出範例"),
        "bad": _first_block_after(md, "壞的輸出範例"),
    }


def check_golden_invariant(skill):
    """同一 skill：good 必過、bad 必不過。回傳 (ok, good_result, bad_result)。"""
    rubric = load_rubric(skill)
    ex = extract_examples(skill)
    good = evaluate(rubric, ex["good"])
    bad = evaluate(rubric, ex["bad"])
    ok = good["passed"] and not bad["passed"]
    return ok, good, bad


def regression(skills, quiet=False):
    failures = []
    for skill in skills:
        ok, good, bad = check_golden_invariant(skill)
        if not ok:
            failures.append(skill)
        if not quiet:
            status = "OK  " if ok else "FAIL"
            print("[%s] %-9s good=%d/%d(pass=%s) bad=%d/%d(pass=%s)" % (
                status, skill,
                good["n_pass"], good["total"], good["passed"],
                bad["n_pass"], bad["total"], bad["passed"],
            ))
    return failures


def score_file(skill, path):
    rubric = load_rubric(skill)
    with open(path, encoding="utf-8") as f:
        text = f.read()
    res = evaluate(rubric, text)
    print("eval: %s  vs  skill=%s" % (path, skill))
    for cid, passed, desc in res["results"]:
        print("  [%s] %s — %s" % ("PASS" if passed else "fail", cid, desc))
    print("score: %d/%d = %.2f (threshold %.2f) → %s" % (
        res["n_pass"], res["total"], res["score"], res["threshold"],
        "PASS" if res["passed"] else "FAIL",
    ))
    return res["passed"]


def main(argv=None):
    ap = argparse.ArgumentParser(description="Deterministic eval runner for skill outputs.")
    ap.add_argument("--skill", help="skill 名稱（research/analysis/writing/ops/review）")
    ap.add_argument("--file", help="要評的輸出檔（需搭配 --skill）")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    if args.file:
        if not args.skill:
            ap.error("--file 需搭配 --skill")
        return 0 if score_file(args.skill, args.file) else 1

    skills = [args.skill] if args.skill else discover_skills()
    if not skills:
        sys.stderr.write("找不到任何 skills/*/rubric.yaml\n")
        return 1
    failures = regression(skills, quiet=args.quiet)
    if failures:
        print("FAILED eval regression: %s" % ", ".join(failures))
        return 1
    print("OK: eval regression passed (%d skills)" % len(skills))
    return 0


if __name__ == "__main__":
    sys.exit(main())
