#!/usr/bin/env python3
"""Self-evolution loop — observe → analyze → propose (human-gated).

The harness's self-improvement loop, formalized as an engine. It closes the
feedback loop that RETRO_FLOW describes manually:

    observe (audit/runs/errors + verifiers + cost + overlap)
      → analyze (detect evolution triggers across 4 facets)
      → PROPOSE (write outputs/drafts/evolution-<date>.md)
      → [HUMAN GATE]  ← the loop STOPS here, by design
      → apply (human edits system/, records a decision log)
      → re-observe (next cycle)

Design stance (chosen 2026-06-06, 提案制 / propose-only): this script is
READ-ONLY with respect to system/, skills/, and memory/. It only ever writes a
proposal draft into outputs/drafts/. It NEVER edits a rule, policy, skill, or
long-term memory — that requires human approval (CLAUDE.md hard rules; harness
constitution 可控 > 能力). This is also the AGI-oversight-safe design: a
self-modifying loop is exactly where reward-hacking/scheming would bite, so the
loop proposes and humans dispose; independent verifiers (verify_completion,
verify_audit_integrity) feed it rather than the executor's self-report.

Facets observed (all four, per 2026-06-06 selection):
  cost      — logs/runs token_estimate vs COST_POLICY calibration (factor ≥ 1.5)
  failure   — logs/errors recurring types + verify_completion WARN/FAIL +
              verify_audit_integrity audit coverage WARN
  gate      — per-gate fail rate from logs/runs gate_results
  decision  — decision revisit + NATIVE_OVERLAP aggregate vs 40%/50% thresholds

Usage:
  python3 scripts/evolution_loop.py            # write proposal draft + summary
  python3 scripts/evolution_loop.py --check     # dry-run (no write), exit 0 (advisory)
  python3 scripts/evolution_loop.py --json       # proposals as JSON
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify_audit_integrity as vai  # noqa: E402
import verify_completion as vc  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

# --- thresholds (single place to tune; mirror COST_POLICY / NATIVE_OVERLAP) ---
COST_FACTOR_THRESHOLD = 1.5          # actual_avg / initial_estimate (COST_POLICY rule)
COST_MIN_SAMPLES = 2                 # need ≥N dashboard-measured runs to recalibrate
RECURRING_ERROR_THRESHOLD = 2        # same error_type count that warrants a rule review
GATE_FAIL_RATE_THRESHOLD = 0.34      # per-gate fail rate that warrants a GATE_POLICY look
OVERLAP_WARN_PCT = 40                # NATIVE_OVERLAP aggregate warn
OVERLAP_V3_PCT = 50                  # NATIVE_OVERLAP aggregate → v3 evaluation

# COST_POLICY initial per-skill estimates (single source: system/COST_POLICY.md tables).
COST_INITIAL_ESTIMATE = {
    "research": 15000, "analysis": 12000, "writing": 10000, "ops": 8000, "review": 12000,
}


@dataclass
class Proposal:
    facet: str          # cost | failure | gate | decision
    severity: str       # info | warn | action
    finding: str        # what was observed
    suggestion: str     # concrete change: file:location + direction
    needs_human: bool = True   # always True under propose-only (the loop never auto-applies)


# ───────────────────────── observation (read-only IO) ─────────────────────────

def _load_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def collect_signals(root: Path) -> dict[str, Any]:
    """Gather raw observations from the harness's own records (read-only)."""
    signals: dict[str, Any] = {"cost": {}, "failure": {}, "gate": {}, "decision": {}}

    # --- runs: cost + gate ---
    cost_by_skill: dict[str, list[int]] = {}
    measured = rule_estimated = 0
    gate_fail: dict[str, int] = {}
    gate_total: dict[str, int] = {}
    for p in sorted((root / "logs" / "runs").glob("*.yaml")):
        doc = _load_yaml(p)
        log = doc.get("execution_log") if isinstance(doc, dict) and isinstance(doc.get("execution_log"), dict) else doc
        if not isinstance(log, dict):
            continue
        te = log.get("token_estimate") or {}
        if isinstance(te, dict) and te.get("total"):
            if te.get("source") == "dashboard_measured":
                measured += 1
                cost_by_skill.setdefault(str(log.get("skill_type", "")), []).append(int(te["total"]))
            elif te.get("source") == "rule_estimated":
                rule_estimated += 1
        gr = log.get("gate_results") or {}
        if isinstance(gr, dict):
            for gate, verdict in gr.items():
                if verdict in ("pass", "fail"):
                    gate_total[gate] = gate_total.get(gate, 0) + 1
                    if verdict == "fail":
                        gate_fail[gate] = gate_fail.get(gate, 0) + 1
    signals["cost"] = {"measured": measured, "rule_estimated": rule_estimated,
                       "by_skill": {k: v for k, v in cost_by_skill.items() if k}}
    signals["gate"] = {"fail": gate_fail, "total": gate_total}

    # --- errors: recurring error_type ---
    error_types: dict[str, int] = {}
    for p in sorted((root / "logs" / "errors").glob("*.md")):
        if "TEMPLATE" in p.name:
            continue
        m = re.search(r"```yaml\n(.*?)```", p.read_text(encoding="utf-8"), re.S)
        if not m:
            continue
        block = yaml.safe_load(m.group(1)) if m else None
        et = block.get("error_type") if isinstance(block, dict) else None
        if et:
            error_types[str(et)] = error_types.get(str(et), 0) + 1

    # --- verifiers (import, not subprocess — single source of truth) ---
    try:
        vcounts = {"OK": 0, "WARN": 0, "FAIL": 0}
        for r in vc.evaluate_all(root):
            vcounts[r["level"]] = vcounts.get(r["level"], 0) + 1
    except Exception:
        vcounts = {"OK": 0, "WARN": 0, "FAIL": 0}
    try:
        audit_warn = len(vai.check_audit_soft(root))
        mem_fail = len(vai.check_memory(root))
    except Exception:
        audit_warn = mem_fail = 0
    signals["failure"] = {"error_types": error_types, "verify_completion": vcounts,
                          "audit_warn": audit_warn, "memory_fail": mem_fail}

    # --- decision: NATIVE_OVERLAP + revisit-due (best-effort subprocess) ---
    overlap_pct = None
    nov = _load_yaml(root / "system" / "NATIVE_OVERLAP.yaml")
    if isinstance(nov, dict):
        overlap_pct = nov.get("aggregate_estimate_pct") or nov.get("aggregate_overlap_pct")
        if overlap_pct is None:  # fall back to any field that looks like an aggregate %
            for k, v in nov.items():
                if "aggregate" in str(k).lower() and isinstance(v, (int, float)):
                    overlap_pct = v
                    break
    due = []
    try:
        out = subprocess.run(["ruby", str(root / "scripts" / "check_decision_revisit.rb"), "--json"],
                             cwd=root, capture_output=True, text=True, timeout=30)
        if out.returncode == 0:
            data = json.loads(out.stdout)
            rows = data.get("decisions", data) if isinstance(data, dict) else data
            for d in rows if isinstance(rows, list) else []:
                if str(d.get("verdict", "")).upper() in ("DUE", "REVISIT", "TRIGGERED"):
                    due.append(d.get("decision_id", "?"))
    except Exception:
        pass
    signals["decision"] = {"overlap_pct": overlap_pct, "due": due}
    return signals


# ───────────────────────── analysis (pure / testable) ─────────────────────────

def build_proposals(signals: dict[str, Any]) -> list[Proposal]:
    """Turn raw signals into human-gated proposals. Pure function — unit-tested."""
    props: list[Proposal] = []

    # cost
    cost = signals.get("cost", {})
    measured = cost.get("measured", 0)
    if measured < COST_MIN_SAMPLES:
        props.append(Proposal(
            "cost", "info",
            f"只有 {measured} 筆 dashboard_measured token 樣本（需 ≥{COST_MIN_SAMPLES} 才能可信回測）。",
            "logs/runs/*.yaml：未來 run 的 token_estimate.source 填 dashboard_measured；"
            "暫不調 COST_POLICY 數字。",
        ))
    for skill, totals in (cost.get("by_skill") or {}).items():
        if len(totals) < COST_MIN_SAMPLES:
            continue
        avg = sum(totals) / len(totals)
        est = COST_INITIAL_ESTIMATE.get(skill)
        if est and avg / est >= COST_FACTOR_THRESHOLD:
            props.append(Proposal(
                "cost", "action",
                f"{skill} 實測均 {avg:.0f} tokens，校準係數 {avg/est:.2f} ≥ {COST_FACTOR_THRESHOLD}（{len(totals)} 樣本）。",
                f"system/COST_POLICY.md：更新 {skill} 的建議上限與校準係數（依實測回測）。",
            ))

    # failure
    fail = signals.get("failure", {})
    for et, n in (fail.get("error_types") or {}).items():
        if n >= RECURRING_ERROR_THRESHOLD:
            props.append(Proposal(
                "failure", "action",
                f"error_type='{et}' 累積 {n} 次（≥{RECURRING_ERROR_THRESHOLD}）—— 反覆失敗。",
                "system/FAILURE_TAXONOMY.yaml + GLOBAL_RULES.md：評估是否需新增/強化對應緩解規則。",
            ))
    vco = fail.get("verify_completion", {})
    if vco.get("FAIL", 0) > 0:
        props.append(Proposal(
            "failure", "action",
            f"verify_completion 標記 {vco['FAIL']} 筆 FAIL（done 無產物/無 checkpoint，疑似自我謊報）。",
            "逐筆調查對應 Task Card；必要時修正狀態或補產物。屬 reward-hacking 訊號，優先處理。",
        ))
    if fail.get("audit_warn", 0) > 0:
        props.append(Proposal(
            "failure", "warn",
            f"verify_audit_integrity 報 {fail['audit_warn']} 筆稽核 WARN（覆蓋缺口/生成漂移）。",
            "logs/AUDIT_LOG.md：考慮開「遷移到生成格式」任務，之後把 generate_audit_log --check 升為硬 gate。",
        ))

    # gate
    gate = signals.get("gate", {})
    for g, total in (gate.get("total") or {}).items():
        f = gate.get("fail", {}).get(g, 0)
        if total and f / total >= GATE_FAIL_RATE_THRESHOLD:
            props.append(Proposal(
                "gate", "action",
                f"{g} 失敗率 {f}/{total}（≥{GATE_FAIL_RATE_THRESHOLD:.0%}）—— 該層最常卡。",
                f"system/GATE_POLICY.yaml（{g}）/ tasks/TASK_CARD_TEMPLATE.yaml：檢視該 gate 條件或 DoD 顆粒度。",
            ))

    # decision
    dec = signals.get("decision", {})
    for did in dec.get("due", []):
        props.append(Proposal(
            "decision", "action",
            f"決策 {did} 的 revisit_trigger 已達成 —— 該回看。",
            f"memory/active_projects/*/decisions/：重評 {did}，必要時開新 decision 取代/更新。",
        ))
    op = dec.get("overlap_pct")
    if isinstance(op, (int, float)):
        if op >= OVERLAP_V3_PCT:
            props.append(Proposal(
                "decision", "action",
                f"NATIVE_OVERLAP aggregate {op}% ≥ {OVERLAP_V3_PCT}% —— 觸發 v3 評估。",
                "system/NATIVE_OVERLAP.yaml + 開 v3-readiness 評估任務（保留/下放原生）。",
            ))
        elif op >= OVERLAP_WARN_PCT:
            props.append(Proposal(
                "decision", "warn",
                f"NATIVE_OVERLAP aggregate {op}% ≥ {OVERLAP_WARN_PCT}%（預警，未達 v3 閾值）。",
                "下次季度 RETRO 逐模組重評原生重疊；持續上升才動 v3。",
            ))
    return props


# ───────────────────────── proposal rendering ─────────────────────────

SEV_ORDER = {"action": 0, "warn": 1, "info": 2}
SEV_ICON = {"action": "🔴", "warn": "🟡", "info": "🟢"}


def render_proposal_doc(props: list[Proposal], today: str) -> str:
    props = sorted(props, key=lambda p: (SEV_ORDER.get(p.severity, 9), p.facet))
    lines = [
        f"# 自我進化提案 — {today}",
        "",
        "> **草稿（draft）** ｜ 由 `scripts/evolution_loop.py` 自動觀測+分析產出。",
        "> **提案制（人工把關）**：本檔只是提案。任何 `system/`/`skills/` 變更**須人工核可後**才套用；",
        "> 本迴圈不自行修改任何規則/政策/記憶（CLAUDE.md 硬規則、可控 > 能力）。",
        "",
        f"觀測四面向：成本 / 失敗 / Gate / 決策。共 {len(props)} 條提案"
        f"（🔴 {sum(1 for p in props if p.severity=='action')} action、"
        f"🟡 {sum(1 for p in props if p.severity=='warn')} warn、"
        f"🟢 {sum(1 for p in props if p.severity=='info')} info）。",
        "",
    ]
    if not props:
        lines.append("本週期無觸發任何進化提案（所有面向在閾值內）。")
    else:
        lines.append("| | 面向 | 發現 | 建議變更（待人工核可） |")
        lines.append("|:--:|------|------|------|")
        for p in props:
            lines.append(f"| {SEV_ICON.get(p.severity,'')} | {p.facet} | {p.finding} | {p.suggestion} |")
    lines += [
        "",
        "## 閉環下一步（人工）",
        "1. 審閱上表，勾選要採納的提案。",
        "2. 採納者：人工修改對應 `system/`/`skills/`（ask 級），並依 RETRO_FLOW 記一筆 decision log。",
        "3. 若動到 memory/，套用後跑 `verify_audit_integrity.py --update` 重建完整性 manifest。",
        "4. 下個週期再跑 `evolution_loop.py` 重新觀測，確認問題收斂。",
        "",
        "_來源工具：verify_completion / verify_audit_integrity / logs(runs,errors) / "
        "check_decision_revisit / NATIVE_OVERLAP / COST_POLICY。_",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="dry-run: detect + summarize, do not write (advisory, exit 0)")
    parser.add_argument("--json", action="store_true", help="emit proposals as JSON")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--today", type=str, default=None, help="override date (YYYY-MM-DD), for testing")
    args = parser.parse_args(argv)

    today = args.today or date.today().isoformat()
    signals = collect_signals(args.root)
    props = build_proposals(signals)

    if args.json:
        print(json.dumps([asdict(p) for p in props], ensure_ascii=False, indent=2))
        return 0

    summary = (f"evolution_loop: {len(props)} proposal(s) — "
               f"action={sum(1 for p in props if p.severity=='action')} "
               f"warn={sum(1 for p in props if p.severity=='warn')} "
               f"info={sum(1 for p in props if p.severity=='info')}")

    if args.check:
        for p in sorted(props, key=lambda p: SEV_ORDER.get(p.severity, 9)):
            print(f"[{p.severity}] {p.facet}: {p.finding}")
        print(summary + " (dry-run; no file written)")
        return 0

    out = args.root / "outputs" / "drafts" / f"evolution-{today}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_proposal_doc(props, today), encoding="utf-8")
    print(f"Wrote {out.relative_to(args.root)}")
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
