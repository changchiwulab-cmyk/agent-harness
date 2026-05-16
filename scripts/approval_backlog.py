#!/usr/bin/env python3
"""Approval backlog: visibility + batch recording of human sign-off.

Two modes:

  scan (default)
      Show what is waiting for a human:
        - Pending sign-off: tasks/20*.yaml with approval_needed==true and
          status=='review' and NO logs/approvals/ record for that task_id,
          with how many days each has waited.
        - outputs/drafts/ volume + oldest file age.
        - logs/approvals/ count + latest record.
      Read-only. Backlog being non-empty is normal, not an error.

  --approve TASKID[,TASKID...] --by NAME [--note TEXT]
      The OPERATOR's tool to record a batch of human decisions. It does NOT
      decide anything: it writes a logs/approvals/ record (same schema as
      APR-20260515-001/002, consumed by system/RETRO_FLOW.md) for each
      task_id, with a sequential APR-YYYYMMDD-NNN id. A task_id that already
      has an approval is refused (no double sign-off). Task Card status is
      deliberately NOT changed here — that stays a separate explicit step.

The agent must only invoke --approve to transcribe an explicit human batch
decision (identical to the Phase 0/1 flow: human approves in chat -> record
is written). It never self-approves.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
TASKS_GLOB = "tasks/20*.yaml"
APPROVALS_DIR = "logs/approvals"
DRAFTS_DIR = "outputs/drafts"
_FENCE_RE = re.compile(r"```yaml\s*\n(.*?)\n```", re.DOTALL)


def _load(path: Path) -> dict[str, Any]:
    try:
        d = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, OSError):
        return {}
    return d if isinstance(d, dict) else {}


def approval_records(root: Path) -> list[dict[str, Any]]:
    recs = []
    for p in sorted((root / APPROVALS_DIR).glob("*.md")):
        m = _FENCE_RE.search(p.read_text(encoding="utf-8"))
        if not m:
            continue
        try:
            doc = yaml.safe_load(m.group(1))
        except yaml.YAMLError:
            continue
        if isinstance(doc, dict) and doc.get("task_id"):
            recs.append(doc)
    return recs


def approved_task_ids(root: Path) -> set[str]:
    return {str(r["task_id"]).strip() for r in approval_records(root)}


def _parse_date(s: str) -> _dt.date | None:
    try:
        return _dt.date.fromisoformat(str(s).strip())
    except (ValueError, TypeError):
        return None


def scan(root: Path, today: _dt.date) -> dict[str, Any]:
    approved = approved_task_ids(root)
    pending = []
    for p in sorted(root.glob(TASKS_GLOB)):
        card = _load(p)
        tid = str(card.get("task_id", "")).strip()
        if not tid:
            continue
        if not card.get("approval_needed"):
            continue
        if str(card.get("status", "")).strip() != "review":
            continue
        if tid in approved:
            continue
        d = _parse_date(card.get("date", ""))
        age = (today - d).days if d else None
        pending.append(
            {
                "task_id": tid,
                "goal": str(card.get("goal", "")).strip()[:70],
                "risk": str(card.get("risk_level", "")).strip(),
                "waiting_days": age,
            }
        )

    drafts = sorted((root / DRAFTS_DIR).glob("*.md"))
    oldest_age = None
    if drafts:
        oldest_mtime = min(f.stat().st_mtime for f in drafts)
        oldest_age = (
            today - _dt.date.fromtimestamp(oldest_mtime)
        ).days

    recs = approval_records(root)
    latest = ""
    if recs:
        latest = sorted(
            str(r.get("approval_id", "")) for r in recs
        )[-1]

    return {
        "pending": sorted(pending, key=lambda x: (x["waiting_days"] is None, -(x["waiting_days"] or 0))),
        "drafts_count": len(drafts),
        "drafts_oldest_days": oldest_age,
        "approved_count": len(recs),
        "latest_approval_id": latest,
    }


def render_scan(s: dict[str, Any]) -> str:
    out = ["=== Approval Backlog ===", ""]
    if not s["pending"]:
        out.append("Pending 簽核：無（backlog clear）")
    else:
        out.append(f"Pending 簽核：{len(s['pending'])} 筆")
        for x in s["pending"]:
            d = x["waiting_days"]
            d = f"{d}d" if d is not None else "?"
            out.append(f"  - {x['task_id']} [{x['risk']}] 等待 {d}：{x['goal']}")
    out += [
        "",
        f"草稿 outputs/drafts/：{s['drafts_count']} 個"
        + (f"（最舊 {s['drafts_oldest_days']}d）" if s["drafts_oldest_days"] is not None else ""),
        f"已核准 logs/approvals/：{s['approved_count']} 筆"
        + (f"（最新 {s['latest_approval_id']}）" if s["latest_approval_id"] else ""),
    ]
    return "\n".join(out)


def _next_seq(root: Path, today: _dt.date) -> int:
    prefix = f"APR-{today:%Y%m%d}-"
    mx = 0
    for r in approval_records(root):
        aid = str(r.get("approval_id", ""))
        if aid.startswith(prefix):
            try:
                mx = max(mx, int(aid[len(prefix):]))
            except ValueError:
                pass
    return mx + 1


def _approval_doc(approval_id: str, task_id: str, today: _dt.date, by: str, note: str) -> str:
    return (
        f"# Approval Log — {task_id}（批次記錄）\n\n"
        "依 system/APPROVAL_POLICY.yaml human_confirm；由 scripts/approval_backlog.py "
        "--approve 記錄人工批次決策，供 system/RETRO_FLOW.md 消費。\n\n"
        "```yaml\n"
        f'approval_id: "{approval_id}"\n'
        f'task_id: "{task_id}"\n'
        f'date: "{today.isoformat()}"\n'
        'method: "human_confirm"\n'
        'decision: "approved"\n'
        f'approved_by: "{by}"\n'
        'requested_by: "agent (batch via approval_backlog.py)"\n'
        'decision_channel: "operator batch approval"\n'
        f'note: "{note}"\n'
        "```\n"
    )


def approve(root: Path, task_ids: list[str], by: str, note: str, today: _dt.date) -> int:
    existing = approved_task_ids(root)
    rc = 0
    seq = _next_seq(root, today)
    for tid in task_ids:
        tid = tid.strip()
        if not tid:
            continue
        if tid in existing:
            print(f"REFUSED {tid}: 已有 approval 紀錄，不重複簽核", file=sys.stderr)
            rc = 1
            continue
        approval_id = f"APR-{today:%Y%m%d}-{seq:03d}"
        dest = root / APPROVALS_DIR / f"{today.isoformat()}_{tid}_approval.md"
        dest.write_text(_approval_doc(approval_id, tid, today, by, note), encoding="utf-8")
        print(f"RECORDED {tid} -> {dest.relative_to(root)} ({approval_id})")
        existing.add(tid)
        seq += 1
    return rc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--approve", help="comma-separated task_ids to record approval for")
    parser.add_argument("--by", default="", help="operator name (required with --approve)")
    parser.add_argument("--note", default="batch approval", help="optional note")
    parser.add_argument("--today", help="YYYY-MM-DD override (testing/determinism)")
    args = parser.parse_args(argv)

    today = _parse_date(args.today) if args.today else _dt.date.today()
    if today is None:
        print("ERROR: --today must be YYYY-MM-DD", file=sys.stderr)
        return 2

    if args.approve:
        if not args.by.strip():
            print("ERROR: --approve 需要 --by <operator>（人工簽核歸屬）", file=sys.stderr)
            return 2
        return approve(
            args.root, args.approve.split(","), args.by.strip(), args.note, today
        )

    print(render_scan(scan(args.root, today)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
