#!/usr/bin/env python3
"""Governance metrics collector — plan §5.3 4 條關鍵指標.

Outputs a markdown report (default) or JSON (--json). Exit code:
    0 = all metrics OK
    1 = at least one metric in warn/alert state
    2 = collection error (missing files, parse errors)

Designed to be run monthly by the user (no auto-schedule). Not part of CI.

Metrics:
    M1 — 月 Task Card 建立數
    M2 — outputs/drafts:reports 比例
    M3 — audit log 覆蓋率
    M4 — Claude Code 原生功能重疊度（人工 input from system/NATIVE_OVERLAP.yaml）
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = ROOT / "tasks"
AUDIT_LOG = ROOT / "logs" / "AUDIT_LOG.md"
DRAFTS_DIR = ROOT / "outputs" / "drafts"
REPORTS_DIR = ROOT / "outputs" / "reports"
NATIVE_OVERLAP = ROOT / "system" / "NATIVE_OVERLAP.yaml"

# generate_audit_log.py 的 AUTO 區標記；「人工備註」區封存的舊紀錄仍是 yaml fence，
# 不隔離會讓同一 task 被重複計數。
AUTO_AUDIT_BEGIN = "<!-- AUTO_AUDIT_BEGIN -->"
AUTO_AUDIT_END = "<!-- AUTO_AUDIT_END -->"


def machine_readable_audit_section(text: str) -> str:
    """有 AUTO 標記時只回傳標記內的機器可讀區段，否則回傳全文（舊格式相容）。"""
    if AUTO_AUDIT_BEGIN in text and AUTO_AUDIT_END in text:
        return text.split(AUTO_AUDIT_BEGIN, 1)[1].split(AUTO_AUDIT_END, 1)[0]
    return text

# Status values that should have a corresponding audit entry.
COMPLETED_STATUSES = {"review", "done", "failed", "partial"}

# task_id pattern: YYYYMMDD-XXX (allows letter prefixes like A01, R01, N03)
TASK_ID_RE = re.compile(r"^(\d{8})-")


@dataclass
class MetricResult:
    id: str                    # M1 / M2 / M3 / M4
    name: str
    current: str               # human-readable value
    threshold: str             # human-readable threshold
    status: str                # ok / warn / alert
    details: dict              # raw values for JSON consumers


# --- Loaders ---------------------------------------------------------------


def load_task_cards() -> list[dict]:
    """Return list of {task_id, status, year_month} for every task card under tasks/.

    Raises yaml.YAMLError on malformed task YAML — main() converts that to exit
    code 2 (collection error). Silently skipping would let broken cards
    undercount metrics and report ok/warn for actually broken data.
    """
    cards = []
    for path in sorted(TASKS_DIR.glob("*.yaml")):
        if path.name in {"TASK_CARD_TEMPLATE.yaml", "DECISION_LOG_TEMPLATE.yaml"}:
            continue
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise yaml.YAMLError(f"{path.relative_to(ROOT)}: {exc}") from exc
        if not isinstance(data, dict):
            continue
        task_id = data.get("task_id", "") or ""
        m = TASK_ID_RE.match(task_id)
        if not m:
            continue
        ymd = m.group(1)
        cards.append({
            "task_id": task_id,
            "status": data.get("status", "pending"),
            "year_month": f"{ymd[:4]}-{ymd[4:6]}",
            "path": str(path.relative_to(ROOT)),
        })
    return cards


def load_audit_task_ids() -> set[str]:
    """Return set of task_ids that have an entry in AUDIT_LOG.md (excluding empty format example).

    Parses ```yaml fenced blocks the same way validators/check_audit_format.py does,
    so any valid YAML quoting style is recognised (double, single, unquoted).
    """
    if not AUDIT_LOG.exists():
        return set()
    text = machine_readable_audit_section(AUDIT_LOG.read_text(encoding="utf-8"))
    ids: set[str] = set()
    for block in re.findall(r"```yaml\n(.*?)\n```", text, re.DOTALL):
        try:
            data = yaml.safe_load(block)
        except yaml.YAMLError:
            continue
        if data is None:
            continue
        entries = data if isinstance(data, list) else [data] if isinstance(data, dict) else []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            tid = entry.get("task_id")
            if isinstance(tid, str) and tid:
                ids.add(tid)
    return ids


def count_dir_md_files(d: Path) -> int:
    if not d.exists():
        return 0
    return sum(1 for p in d.glob("*.md") if p.is_file())


def load_native_overlap() -> dict:
    if not NATIVE_OVERLAP.exists():
        return {}
    return yaml.safe_load(NATIVE_OVERLAP.read_text(encoding="utf-8")) or {}


# --- Metric calculators ----------------------------------------------------


def _ym_minus(ym: str, months_back: int) -> str:
    """Subtract `months_back` calendar months from "YYYY-MM" string."""
    y, m = int(ym[:4]), int(ym[5:7])
    total = y * 12 + (m - 1) - months_back
    return f"{total // 12:04d}-{total % 12 + 1:02d}"


def metric_m1(cards: list[dict], today: date) -> MetricResult:
    """M1 — 月 Task Card 建立數.

    Window: 3 calendar months anchored on `today` — `[today-2m, today-1m, today]`.
    Months with no cards are evaluated as 0 against the threshold so that going
    dark in the current/recent month surfaces as warn/alert.

    Boot-phase carve-out: months strictly before the earliest observed month are
    excluded from the window. Otherwise a brand-new project would always alert
    on its first cycle.
    """
    counts: dict[str, int] = {}
    for c in cards:
        counts[c["year_month"]] = counts.get(c["year_month"], 0) + 1
    today_ym = f"{today.year:04d}-{today.month:02d}"
    window_months = [_ym_minus(today_ym, i) for i in (2, 1, 0)]
    earliest_observed = min(counts.keys()) if counts else today_ym
    in_scope = [m for m in window_months if m >= earliest_observed]
    recent = [(m, counts.get(m, 0)) for m in in_scope]
    below = [m for m, c in recent if c < 3]
    if any(
        recent[i][1] < 3 and recent[i + 1][1] < 3
        for i in range(len(recent) - 1)
    ):
        status = "alert"
    elif below:
        status = "warn"
    else:
        status = "ok"
    return MetricResult(
        id="M1",
        name="月 Task Card 建立數",
        current=", ".join(f"{m}={c}" for m, c in recent) or "(no data)",
        threshold="連續 2 個月 < 3 張 → alert；單月 < 3 張 → warn",
        status=status,
        details={
            "counts_by_month": dict(counts),
            "recent": recent,
            "below_threshold_months": below,
            "window": window_months,
            "earliest_observed": earliest_observed if counts else None,
        },
    )


def metric_m2(drafts_count: int, reports_count: int) -> MetricResult:
    """M2 — outputs/drafts:reports 比例.

    plan §5.3：drafts/reports 比 < 1:1 → alert（草稿流程沒在跑）
    解讀：drafts 應該至少跟 reports 一樣多（每份 report 通常有對應 draft），
    若 drafts < reports，代表使用者在繞過草稿流程直接寫 reports。
    """
    if reports_count == 0:
        ratio = float("inf") if drafts_count > 0 else 0.0
        ratio_str = "∞ (no reports)" if drafts_count > 0 else "0/0"
    else:
        ratio = drafts_count / reports_count
        ratio_str = f"{drafts_count}/{reports_count} = {ratio:.2f}"
    if ratio < 1 and reports_count > 0:
        status = "alert"
    elif 1 <= ratio < 1.5 and reports_count > 0:
        status = "warn"
    else:
        status = "ok"
    return MetricResult(
        id="M2",
        name="outputs/drafts:reports 比例",
        current=ratio_str,
        threshold="< 1:1 → alert（草稿流程被繞過）",
        status=status,
        details={"drafts": drafts_count, "reports": reports_count, "ratio": ratio if ratio != float("inf") else None},
    )


def metric_m3(cards: list[dict], audit_ids: set[str]) -> MetricResult:
    """M3 — audit log 覆蓋率（窄定義）."""
    completed = [c for c in cards if c["status"] in COMPLETED_STATUSES]
    total = len(completed)
    covered = [c for c in completed if c["task_id"] in audit_ids]
    if total == 0:
        coverage = 1.0
        ratio_str = "(no completed tasks)"
    else:
        coverage = len(covered) / total
        ratio_str = f"{len(covered)}/{total} = {coverage * 100:.1f}%"
    if coverage < 0.8:
        status = "alert"
    elif coverage < 0.9:
        status = "warn"
    else:
        status = "ok"
    missing = sorted(c["task_id"] for c in completed if c["task_id"] not in audit_ids)
    return MetricResult(
        id="M3",
        name="audit log 覆蓋率（status ∈ {review, done, failed, partial}）",
        current=ratio_str,
        threshold="< 80% → alert；< 90% → warn",
        status=status,
        details={
            "completed_total": total,
            "with_audit": len(covered),
            "missing_task_ids": missing,
            "coverage_pct": round(coverage * 100, 1),
        },
    )


def metric_m4(overlap_data: dict) -> MetricResult:
    """M4 — Claude Code 原生功能重疊度 (manual input)."""
    pct = overlap_data.get("aggregate_estimate_pct")
    reviewed_on = overlap_data.get("reviewed_on", "(unknown)")
    if pct is None:
        return MetricResult(
            id="M4",
            name="Claude Code 原生功能重疊度",
            current="(NATIVE_OVERLAP.yaml not found or aggregate_estimate_pct missing)",
            threshold="> 50% → alert；40-50% → warn",
            status="alert",
            details={"error": "missing input"},
        )
    if pct > 50:
        status = "alert"
    elif pct >= 40:
        status = "warn"
    else:
        status = "ok"
    return MetricResult(
        id="M4",
        name="Claude Code 原生功能重疊度（人工評估）",
        current=f"{pct}% (reviewed {reviewed_on})",
        threshold="> 50% → alert；40-50% → warn",
        status=status,
        details={"aggregate_pct": pct, "reviewed_on": reviewed_on, "modules": overlap_data.get("modules", [])},
    )


# --- Observability metrics (R7: workflow / business / failure layers) ------


def parse_token_estimate(value) -> int | None:
    """Parse audit-log estimated_tokens strings like '~16K', '~120K（含…）', '1500'."""
    if value is None:
        return None
    m = re.search(r"(\d+(?:\.\d+)?)\s*([KkMm])?", str(value))
    if not m:
        return None
    num = float(m.group(1))
    unit = (m.group(2) or "").upper()
    if unit == "K":
        num *= 1_000
    elif unit == "M":
        num *= 1_000_000
    return int(num)


def load_run_logs() -> list[dict]:
    """Return execution_log dicts from logs/runs/*.yaml (handles wrapper or bare)."""
    runs: list[dict] = []
    runs_dir = ROOT / "logs" / "runs"
    if not runs_dir.exists():
        return runs
    for p in sorted(runs_dir.glob("*.yaml")):
        try:
            doc = yaml.safe_load(p.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            continue
        if not isinstance(doc, dict):
            continue
        log = doc.get("execution_log") if isinstance(doc.get("execution_log"), dict) else doc
        if isinstance(log, dict):
            runs.append(log)
    return runs


def load_audit_entries() -> list[dict]:
    """Return full audit entries (skill_type, status, estimated_tokens, tools_called)."""
    if not AUDIT_LOG.exists():
        return []
    text = machine_readable_audit_section(AUDIT_LOG.read_text(encoding="utf-8"))
    entries: list[dict] = []
    for block in re.findall(r"```yaml\n(.*?)\n```", text, re.DOTALL):
        try:
            data = yaml.safe_load(block)
        except yaml.YAMLError:
            continue
        items = data if isinstance(data, list) else [data] if isinstance(data, dict) else []
        for e in items:
            if isinstance(e, dict) and e.get("task_id"):
                entries.append(e)
    return entries


def load_error_types() -> list[str]:
    """Return error_type values from logs/errors/*.md (skips TEMPLATE)."""
    types: list[str] = []
    errors_dir = ROOT / "logs" / "errors"
    if not errors_dir.exists():
        return types
    for p in sorted(errors_dir.glob("*.md")):
        if "TEMPLATE" in p.name:
            continue
        m = re.search(r"```yaml\n(.*?)\n```", p.read_text(encoding="utf-8"), re.DOTALL)
        if not m:
            continue
        try:
            data = yaml.safe_load(m.group(1))
        except yaml.YAMLError:
            continue
        if isinstance(data, dict) and data.get("error_type"):
            types.append(str(data["error_type"]))
    return types


GATE_NAMES = ("schema_check", "rule_check", "completion_check", "risk_check")


def observability_workflow(runs: list[dict]) -> dict:
    """Workflow layer: gate pass/fail tally, status distribution, avg checkpoints."""
    gate_tally: dict = {g: {} for g in GATE_NAMES}
    status_dist: dict = {}
    checkpoint_counts: list[int] = []
    for r in runs:
        st = r.get("status", "unknown")
        status_dist[st] = status_dist.get(st, 0) + 1
        gr = r.get("gate_results") or {}
        if isinstance(gr, dict):
            for g in GATE_NAMES:
                v = gr.get(g)
                if v is not None:
                    gate_tally[g][v] = gate_tally[g].get(v, 0) + 1
        cps = r.get("checkpoints")
        if isinstance(cps, list):
            checkpoint_counts.append(len(cps))
    avg_cp = round(sum(checkpoint_counts) / len(checkpoint_counts), 2) if checkpoint_counts else 0
    return {
        "runs_total": len(runs),
        "status_distribution": status_dist,
        "gate_results": gate_tally,
        "avg_checkpoints": avg_cp,
    }


def observability_business(audit: list[dict]) -> dict:
    """Business layer: per-skill task count, avg estimated tokens, avg tool calls."""
    by_skill: dict = {}
    for e in audit:
        sk = e.get("skill_type") or "unknown"
        d = by_skill.setdefault(sk, {"count": 0, "tokens": [], "tool_calls": []})
        d["count"] += 1
        tok = parse_token_estimate(e.get("estimated_tokens"))
        if tok is not None:
            d["tokens"].append(tok)
        tc = e.get("tools_called")
        if isinstance(tc, list):
            d["tool_calls"].append(sum(int(x.get("call_count", 0)) for x in tc if isinstance(x, dict)))
    out: dict = {}
    for sk in sorted(by_skill):
        d = by_skill[sk]
        out[sk] = {
            "count": d["count"],
            "avg_tokens": int(sum(d["tokens"]) / len(d["tokens"])) if d["tokens"] else None,
            "avg_tool_calls": round(sum(d["tool_calls"]) / len(d["tool_calls"]), 1) if d["tool_calls"] else None,
        }
    return out


def observability_failures(error_types: list[str]) -> dict:
    """Failure layer: error_type distribution from logs/errors/."""
    dist: dict = {}
    for et in error_types:
        dist[et] = dist.get(et, 0) + 1
    return {"errors_total": len(error_types), "by_type": dist}


def collect_observability() -> dict:
    """Assemble the three observability layers (workflow / business / failures)."""
    return {
        "workflow": observability_workflow(load_run_logs()),
        "business": observability_business(load_audit_entries()),
        "failures": observability_failures(load_error_types()),
    }


def render_observability_markdown(obs: dict) -> str:
    """Render the observability section appended after the M1–M4 report."""
    lines = ["## 可觀測性指標（R7：工作流層 / 業務層 / 失敗分佈）", ""]
    wf = obs["workflow"]
    lines.append(f"### 工作流層（{wf['runs_total']} 筆 run log）")
    lines.append(f"- status 分佈：{wf['status_distribution'] or '(無)'}")
    lines.append(f"- 平均 checkpoints/run：{wf['avg_checkpoints']}")
    lines.append("- 四層 gate 結果統計：")
    for g in GATE_NAMES:
        tally = wf["gate_results"].get(g) or {}
        lines.append(f"  - {g}: {tally or '(尚無資料)'}")
    lines.append("")
    lines.append("### 業務層（每 skill，來源：AUDIT_LOG）")
    lines.append("| skill | 任務數 | 平均 token | 平均工具呼叫 |")
    lines.append("|-------|:-----:|:---------:|:-----------:|")
    for sk, d in obs["business"].items():
        at = d["avg_tokens"] if d["avg_tokens"] is not None else "—"
        ac = d["avg_tool_calls"] if d["avg_tool_calls"] is not None else "—"
        lines.append(f"| {sk} | {d['count']} | {at} | {ac} |")
    lines.append("")
    fa = obs["failures"]
    lines.append(f"### 失敗分佈（{fa['errors_total']} 筆 error log）")
    lines.append(f"- error_type：{fa['by_type'] or '(無)'}")
    lines.append("")
    return "\n".join(lines) + "\n"


# --- Reporters -------------------------------------------------------------


STATUS_BADGE = {"ok": "✅ ok", "warn": "⚠️ warn", "alert": "🚨 alert"}


def render_markdown(metrics: list[MetricResult], today: date) -> str:
    lines = []
    lines.append(f"# Governance Metrics — {today.strftime('%Y-%m')}")
    lines.append("")
    lines.append(f"- 採集時間：{today.isoformat()}")
    lines.append("- 來源：plan §5.3")
    lines.append("- 警訊處理：alert → 開 retro task；warn → 下次 retro 帶討論")
    lines.append("")
    lines.append("## 摘要")
    by_status = {"ok": 0, "warn": 0, "alert": 0}
    for m in metrics:
        by_status[m.status] += 1
    overall = "🚨 ALERT" if by_status["alert"] else ("⚠️ WARN" if by_status["warn"] else "✅ OK")
    lines.append(f"- 整體狀態：**{overall}**（ok={by_status['ok']} / warn={by_status['warn']} / alert={by_status['alert']}）")
    if by_status["alert"]:
        lines.append("- 觸發 alert 的指標：" + ", ".join(m.id for m in metrics if m.status == "alert"))
    if by_status["warn"]:
        lines.append("- 觸發 warn 的指標：" + ", ".join(m.id for m in metrics if m.status == "warn"))
    lines.append("")
    lines.append("## 指標明細")
    lines.append("")
    lines.append("| ID | 名稱 | current | threshold | status |")
    lines.append("|----|------|---------|-----------|:------:|")
    for m in metrics:
        lines.append(f"| {m.id} | {m.name} | {m.current} | {m.threshold} | {STATUS_BADGE[m.status]} |")
    lines.append("")
    lines.append("## 詳細資料（debug）")
    lines.append("```json")
    lines.append(json.dumps([asdict(m) for m in metrics], ensure_ascii=False, indent=2))
    lines.append("```")
    lines.append("")
    lines.append("## 建議動作")
    if by_status["alert"]:
        lines.append("- 至少一條 alert：請開 retro task 檢視觸發原因（plan §5.3 規定）")
    elif by_status["warn"]:
        lines.append("- 有 warn：下一次 retro 把這些指標納入討論清單")
    else:
        lines.append("- 全部 ok：保持現狀，下個月再採集")
    return "\n".join(lines) + "\n"


def render_json(metrics: list[MetricResult]) -> str:
    return json.dumps([asdict(m) for m in metrics], ensure_ascii=False, indent=2)


# --- Main ------------------------------------------------------------------


def collect_metrics(today: date) -> list[MetricResult]:
    cards = load_task_cards()
    audit_ids = load_audit_task_ids()
    drafts = count_dir_md_files(DRAFTS_DIR)
    reports = count_dir_md_files(REPORTS_DIR)
    overlap = load_native_overlap()
    return [
        metric_m1(cards, today),
        metric_m2(drafts, reports),
        metric_m3(cards, audit_ids),
        metric_m4(overlap),
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Collect governance metrics (plan §5.3).")
    parser.add_argument("--json", action="store_true", help="Output M1–M4 JSON instead of markdown.")
    parser.add_argument("--observability", action="store_true",
                        help="Output R7 observability metrics (workflow/business/failure) as JSON.")
    parser.add_argument("--today", type=str, help="Override today's date (YYYY-MM-DD), for testing.")
    args = parser.parse_args(argv)

    today = date.fromisoformat(args.today) if args.today else date.today()

    try:
        metrics = collect_metrics(today)
        obs = collect_observability()
    except (OSError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.observability:
        print(json.dumps(obs, ensure_ascii=False, indent=2))
        return 0
    if args.json:
        print(render_json(metrics))
    else:
        print(render_markdown(metrics, today))
        print(render_observability_markdown(obs))

    has_issue = any(m.status in {"warn", "alert"} for m in metrics)
    return 1 if has_issue else 0


if __name__ == "__main__":
    sys.exit(main())
