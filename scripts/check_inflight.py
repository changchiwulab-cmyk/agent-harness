#!/usr/bin/env python3
"""In-flight dedup check — 開卡前查重（INTAKE_FLOW 前置步驟）.

整合平面對策（2026-07-06 架構診斷）：跨 session 同題重做的實證包括 eval harness
五做（#113–#118）、R9/R10 兩做、R11–R14 編號撞車。根因是開卡前沒有任何機制
看見 in-flight 的分支與 open PR。本工具在草擬 Task Card 前掃三個來源：

    1. tasks/*.yaml 的 goal 欄位 + 檔名 slug（既有卡，含未結案）
    2. `git ls-remote --heads origin` 的分支名（in-flight 分支）
    3. open PR 標題（--pr-json 提供，與 governance_metrics --pr-json 同一份
       GitHub REST /pulls?state=open 輸出；本地通常省略）

定位是 advisory：關鍵字比對抓不到語意重複（「eval harness」vs「評測框架」），
所以輸出疑似清單交人裁決，不做 hook 硬擋（誤判率高的硬擋只會被繞過）。

用法：
    python3 scripts/check_inflight.py 評估 evaluation [--pr-json open_prs.json] [--no-remote]

建議中英文關鍵字各給 1–2 個：goal 多為中文、分支名為英文 slug。

Exit code：0 = 無命中；1 = 有疑似重複（advisory）；2 = 執行錯誤。
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = ROOT / "tasks"
SKIP_FILES = {"TASK_CARD_TEMPLATE.yaml", "DECISION_LOG_TEMPLATE.yaml"}
REMOTE_TIMEOUT_SECONDS = 15


# --- Loaders ----------------------------------------------------------------


def load_task_cards(tasks_dir: Path | None = None) -> list[dict]:
    """Return [{task_id, status, goal, slug, path}] for every card under tasks/.

    壞 YAML 跳過並附警語（查重是 advisory，不 fail-hard——與 governance_metrics
    的 fail-hard 相反，那邊算的是指標、錯數據會誤導）。
    """
    d = tasks_dir if tasks_dir is not None else TASKS_DIR
    cards: list[dict] = []
    for path in sorted(d.glob("*.yaml")):
        if path.name in SKIP_FILES:
            continue
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            print(f"[warn] 跳過壞 YAML：{path.name}", file=sys.stderr)
            continue
        if not isinstance(data, dict):
            continue
        cards.append({
            "task_id": str(data.get("task_id", "") or ""),
            "status": str(data.get("status", "") or ""),
            "goal": str(data.get("goal", "") or ""),
            "slug": path.stem,
            "path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
        })
    return cards


def fetch_remote_branches() -> list[str]:
    """`git ls-remote --heads origin` → 分支名清單。失敗拋例外（caller 降級）。"""
    out = subprocess.run(
        ["git", "ls-remote", "--heads", "origin"],
        capture_output=True, text=True, timeout=REMOTE_TIMEOUT_SECONDS,
        cwd=ROOT, check=True,
    )
    names = []
    for line in out.stdout.splitlines():
        parts = line.split("refs/heads/", 1)
        if len(parts) == 2 and parts[1]:
            names.append(parts[1])
    return names


def load_open_prs(path: str | None) -> list[dict]:
    """讀 GitHub REST /pulls?state=open JSON；無路徑回空清單（PR 來源為選配）。"""
    if not path:
        return []
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{path}: 預期 GitHub pulls list JSON，實得 {type(data).__name__}")
    return data


# --- Matchers（純函式，離線可測）--------------------------------------------


def _norm(s: str) -> str:
    return s.lower().replace(" ", "-")


def match_task_cards(cards: list[dict], keywords: list[str]) -> list[dict]:
    """goal 或檔名 slug 含任一關鍵字（大小寫不敏感）即命中。"""
    hits = []
    for c in cards:
        haystack = (c["goal"] + " " + c["slug"]).lower()
        if any(k.lower() in haystack for k in keywords):
            hits.append(c)
    return hits


def match_branches(names: list[str], keywords: list[str]) -> list[str]:
    """分支名比對：關鍵字正規化（lower、空格→'-'）後做子字串比對。"""
    norm_keys = [_norm(k) for k in keywords]
    return [n for n in names if any(k in n.lower() for k in norm_keys)]


def match_prs(prs: list[dict], keywords: list[str]) -> list[dict]:
    """open PR 標題含任一關鍵字即命中；回傳 [{number, title}]。"""
    hits = []
    for pr in prs:
        if not isinstance(pr, dict):
            continue
        title = str(pr.get("title", "") or "")
        if any(k.lower() in title.lower() for k in keywords):
            hits.append({"number": pr.get("number"), "title": title})
    return hits


# --- Main -------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="開卡前 in-flight 查重（advisory）。")
    parser.add_argument("keywords", nargs="+", help="候選題目關鍵字（建議中英文各 1–2 個）")
    parser.add_argument("--pr-json", type=str, default=None,
                        help="GitHub REST /pulls?state=open JSON（選配，與 governance_metrics 同格式）")
    parser.add_argument("--no-remote", action="store_true",
                        help="跳過 git ls-remote（離線或想省時間時）")
    args = parser.parse_args(argv)

    keywords = [k for k in args.keywords if k.strip()]
    if not keywords:
        print("ERROR: 關鍵字不可為空", file=sys.stderr)
        return 2

    try:
        cards = load_task_cards()
        prs = load_open_prs(args.pr_json)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    branches: list[str] = []
    remote_ok = False
    if not args.no_remote:
        try:
            branches = fetch_remote_branches()
            remote_ok = True
        except Exception as exc:  # noqa: BLE001 — 降級不炸：查重是 advisory
            print(f"[remote unavailable] 略過分支查重：{exc}", file=sys.stderr)

    card_hits = match_task_cards(cards, keywords)
    branch_hits = match_branches(branches, keywords)
    pr_hits = match_prs(prs, keywords)

    print(f"# In-flight 查重：{' / '.join(keywords)}")
    print(f"- 既有 Task Card 命中：{len(card_hits)}")
    for c in card_hits:
        print(f"  - [{c['status'] or '?'}] {c['task_id'] or '(no id)'} {c['goal'][:60]}（{c['path']}）")
    if remote_ok:
        print(f"- in-flight 分支命中：{len(branch_hits)}")
        for b in branch_hits:
            print(f"  - {b}")
    else:
        print("- in-flight 分支：（未查——remote 不可用或 --no-remote）")
    if args.pr_json:
        print(f"- open PR 標題命中：{len(pr_hits)}")
        for p in pr_hits:
            print(f"  - #{p['number']} {p['title'][:70]}")
    else:
        print("- open PR：（未查——未提供 --pr-json）")

    hit = bool(card_hits or branch_hits or pr_hits)
    if hit:
        print("\n⚠ 有疑似重複：停止開卡，呈報使用者裁決（續作既有卡 / 接手 in-flight 分支 / 確認新題）")
    else:
        print("\n✅ 無命中：可續行開卡流程")
    return 1 if hit else 0


if __name__ == "__main__":
    sys.exit(main())
