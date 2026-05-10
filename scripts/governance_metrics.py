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
    text = AUDIT_LOG.read_text(encoding="utf-8")
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
    parser.add_argument("--json", action="store_true", help="Output JSON instead of markdown.")
    parser.add_argument("--today", type=str, help="Override today's date (YYYY-MM-DD), for testing.")
    args = parser.parse_args(argv)

    today = date.fromisoformat(args.today) if args.today else date.today()

    try:
        metrics = collect_metrics(today)
    except (OSError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(render_json(metrics))
    else:
        print(render_markdown(metrics, today))

    has_issue = any(m.status in {"warn", "alert"} for m in metrics)
    return 1 if has_issue else 0


if __name__ == "__main__":
    sys.exit(main())
