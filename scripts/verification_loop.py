#!/usr/bin/env python3
"""Verification-loop driver — system/VERIFICATION_LOOP.yaml 的可執行驅動器.

把 GATE_POLICY 的四層驗證（schema → rule → completion → risk）跑成一個有界、會終止、
可稽核的閉環。本腳本是「驗證驅動器」：它跑 gate、分類失敗、判 disposition、守迭代預算、
產出帳本。真正的「修正」由 agent 在兩輪之間執行，然後以遞增的 --iteration 重新呼叫本腳本。

用法：
    verification_loop.py <task_card.yaml> [--run-log RUN-*.yaml] \\
        [--completion pass,fail,...] [--iteration N] [--max-iterations M] [--json]

退出碼：
    0 = 本輪 outcome 為 pass（四層全綠）
    1 = 非 pass（continue / hard_stop / escalated / exhausted）—迴圈尚未成功或已終止於失敗
    2 = collection error（Task Card 不存在、PERMISSIONS 無法讀取等）

設計重用（不重造輪子）：
    - schema_check 直接呼叫 system/validate_task_card.py 的 validate()
    - rule_check 讀 system/PERMISSIONS.yaml 的 deny 清單
    - 帳本欄位對齊 system/EXECUTION_LOG_SCHEMA.yaml 的 verification_loop 區塊
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PERMISSIONS_PATH = ROOT / "system" / "PERMISSIONS.yaml"
SYSTEM_DIR = ROOT / "system"

# 讓 system/validate_task_card.py 可被 import（system/ 非套件）
if str(SYSTEM_DIR) not in sys.path:
    sys.path.insert(0, str(SYSTEM_DIR))
from validate_task_card import validate as validate_schema  # noqa: E402

GATES = ("schema_check", "rule_check", "completion_check", "risk_check")
GLOBAL_HARD_CAP = 3  # CLAUDE.md：連續失敗 3 次就停下來

# 各 gate 的處置與重試上限（沿用 GATE_POLICY.yaml on_fail 語意；見 VERIFICATION_LOOP.yaml）
DISPOSITION = {
    "schema_check": "retry_fixable",
    "rule_check": "hard_stop",
    "completion_check": "human_gated",
    "risk_check": "escalate",
}
# 額外重試次數（None = 受全域上限約束）。schema 僅 1 次；rule/risk 不重試。
RETRY_CAP = {
    "schema_check": 1,
    "rule_check": 0,
    "completion_check": None,
    "risk_check": 0,
}


class CollectionError(Exception):
    """無法蒐集驗證所需輸入（檔案缺失/讀取失敗）→ 退出碼 2。"""


@dataclass
class GateOutcome:
    results: dict = field(default_factory=lambda: {g: "not_run" for g in GATES})
    first_fail: str | None = None
    messages: list[str] = field(default_factory=list)


# --- 載入器 ---------------------------------------------------------------


def load_yaml(path: Path) -> dict:
    try:
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except FileNotFoundError as e:
        raise CollectionError(f"找不到檔案：{path}") from e
    except yaml.YAMLError as e:
        raise CollectionError(f"YAML 解析失敗：{path}：{e}") from e
    return data if isinstance(data, dict) else {}


def load_deny_list() -> set[str]:
    perms = load_yaml(PERMISSIONS_PATH)
    deny = (perms.get("permissions") or {}).get("deny") or []
    return {str(x).strip() for x in deny}


def run_log_tools(run_log: dict) -> list[dict]:
    log = run_log.get("execution_log", run_log)
    return [t for t in (log.get("tools_used") or []) if isinstance(t, dict)]


# --- 四層 gate -------------------------------------------------------------


def check_schema(card_path: Path) -> tuple[bool, list[str]]:
    """重用 validate_task_card.validate；回傳 (passed, messages)。"""
    errors = validate_schema(str(card_path))
    return (not errors), errors


def check_rule(card: dict, run_log: dict | None) -> tuple[bool, list[str]]:
    msgs: list[str] = []
    deny = load_deny_list()
    allowed = [str(t).strip() for t in (card.get("allowed_tools") or [])]

    for tool in allowed:
        if tool in deny:
            msgs.append(f"allowed_tools 含 deny 工具：{tool}")

    if run_log is not None:
        used = run_log_tools(run_log)
        allowed_set = set(allowed)
        for entry in used:
            name = str(entry.get("tool", "")).strip()
            if name and name not in allowed_set:
                msgs.append(f"使用了白名單外的工具：{name}")
            if name in deny:
                msgs.append(f"使用了 deny 工具：{name}")
            if name == "web_search" and int(entry.get("call_count", 0) or 0) > 3:
                msgs.append(f"外部查詢超過 3 輪：web_search={entry.get('call_count')}")

    return (not msgs), msgs


def check_completion(card: dict, completion: list[str] | None) -> tuple[bool, list[str] | None]:
    """逐條比對 definition_of_done。

    completion 是與 DoD 同序的 pass/fail 標記。未提供標記 → 回傳 None（not_run，
    交人工/agent 提供逐條結果），非視為失敗。
    """
    dod = card.get("definition_of_done") or []
    if completion is None:
        return False, None  # not_run sentinel（呼叫端據此標 not_run）
    if len(completion) != len(dod):
        return False, [f"completion checklist 長度({len(completion)}) 與 DoD({len(dod)}) 不符"]
    gaps = [
        f"definition_of_done[{i}] 未通過：{str(dod[i])[:60]}"
        for i, mark in enumerate(completion)
        if str(mark).strip().lower() != "pass"
    ]
    return (not gaps), gaps


def check_risk(card: dict) -> tuple[bool, list[str]]:
    risk = str(card.get("risk_level", "")).strip()
    loc = str((card.get("expected_output") or {}).get("location", "")).strip()
    if risk in ("high", "critical") and not loc.startswith("outputs/drafts"):
        return False, [f"risk_level={risk} 的輸出須在 outputs/drafts/，目前：{loc or '(未指定)'}"]
    return True, []


def run_gates(
    card_path: Path,
    card: dict | None,
    run_log: dict | None,
    completion: list[str] | None,
) -> GateOutcome:
    """依序跑四層，遇首個 fail 即短路（其餘標 not_run）。not_run 不算 fail。"""
    outcome = GateOutcome()

    ok, msgs = check_schema(card_path)
    outcome.results["schema_check"] = "pass" if ok else "fail"
    outcome.messages += msgs
    if not ok:
        outcome.first_fail = "schema_check"
        return outcome

    # schema 通過後 card 必為可解析的 dict
    card = card or {}

    ok, msgs = check_rule(card, run_log)
    outcome.results["rule_check"] = "pass" if ok else "fail"
    outcome.messages += msgs
    if not ok:
        outcome.first_fail = "rule_check"
        return outcome

    ok, comp_msgs = check_completion(card, completion)
    if comp_msgs is None:
        outcome.results["completion_check"] = "not_run"
        outcome.messages.append("completion_check 未評估：請以 --completion 提供 DoD 逐條結果")
    else:
        outcome.results["completion_check"] = "pass" if ok else "fail"
        outcome.messages += comp_msgs
        if not ok:
            outcome.first_fail = "completion_check"
            return outcome

    ok, msgs = check_risk(card)
    outcome.results["risk_check"] = "pass" if ok else "fail"
    outcome.messages += msgs
    if not ok:
        outcome.first_fail = "risk_check"
        return outcome

    return outcome


# --- 決策：disposition + 終態 + 預算 ---------------------------------------


def attempts_allowed(gate: str, max_iterations: int) -> int:
    cap = RETRY_CAP[gate]
    if cap is None:
        return max_iterations
    return min(1 + cap, max_iterations)


def decide(
    outcome: GateOutcome, iteration: int, max_iterations: int
) -> tuple[str, str | None, str | None]:
    """回傳 (loop_outcome, disposition, next_action)。

    loop_outcome ∈ pass | continue | hard_stop | escalated | exhausted
    """
    first = outcome.first_fail
    # 四層全 pass，且 completion 不是 not_run → pass
    if first is None:
        if outcome.results["completion_check"] == "not_run":
            return (
                "continue",
                "human_gated",
                "提供 DoD 逐條結果（--completion）以完成 completion_check",
            )
        return "pass", None, None

    disp = DISPOSITION[first]
    if disp == "hard_stop":
        return "hard_stop", disp, "rule 違規：停止、寫 logs/errors/、通知使用者"
    if disp == "escalate":
        return "escalated", disp, "輸出鎖進 outputs/drafts/，等待人工審閱"

    # retry_fixable / human_gated
    if iteration >= attempts_allowed(first, max_iterations):
        return "exhausted", disp, "達迭代上限仍未通過：停止、寫 logs/errors/、通知使用者"
    return "continue", disp, f"修正後以 --iteration {iteration + 1} 重新驗證"


def build_ledger_entry(
    outcome: GateOutcome, iteration: int, disposition: str | None, action: str | None
) -> dict:
    return {
        "iteration": iteration,
        "gate_results": dict(outcome.results),
        "first_fail": outcome.first_fail,
        "disposition": disposition,
        "action": action,
    }


# --- CLI ------------------------------------------------------------------


def parse_completion(raw: str | None) -> list[str] | None:
    if raw is None:
        return None
    return [p.strip() for p in raw.split(",") if p.strip() != ""]


def run(
    card_path: Path,
    run_log_path: Path | None,
    completion: list[str] | None,
    iteration: int,
    max_iterations: int | None,
) -> dict:
    if not card_path.exists():
        raise CollectionError(f"找不到 Task Card：{card_path}")
    card = load_yaml(card_path)  # schema fail 時仍可能為 {}，由 check_schema 把關
    run_log = load_yaml(run_log_path) if run_log_path else None

    if max_iterations is None:
        max_iterations = int(card.get("max_retries") or GLOBAL_HARD_CAP)
    max_iterations = max(1, min(max_iterations, GLOBAL_HARD_CAP))

    outcome = run_gates(card_path, card, run_log, completion)
    loop_outcome, disposition, next_action = decide(outcome, iteration, max_iterations)
    entry = build_ledger_entry(outcome, iteration, disposition, next_action)

    return {
        "task_id": card.get("task_id", ""),
        "iteration": iteration,
        "max_iterations": max_iterations,
        "outcome": loop_outcome,
        "gate_results": dict(outcome.results),
        "first_fail": outcome.first_fail,
        "disposition": disposition,
        "next_action": next_action,
        "messages": outcome.messages,
        "ledger_entry": entry,
    }


def format_human(result: dict) -> str:
    lines = [
        f"Task Card : {result['task_id'] or '(未知)'}",
        f"迭代       : {result['iteration']}/{result['max_iterations']}",
        f"outcome    : {result['outcome']}",
        "gate_results:",
    ]
    for g in GATES:
        mark = {"pass": "✅", "fail": "❌", "not_run": "·"}.get(result["gate_results"][g], "?")
        lines.append(f"  {mark} {g}: {result['gate_results'][g]}")
    if result["first_fail"]:
        lines.append(f"first_fail : {result['first_fail']} → disposition: {result['disposition']}")
    if result["next_action"]:
        lines.append(f"next_action: {result['next_action']}")
    for m in result["messages"]:
        lines.append(f"  - {m}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="驗證閉環驅動器（VERIFICATION_LOOP.yaml）")
    parser.add_argument("task_card", help="Task Card YAML 路徑")
    parser.add_argument("--run-log", help="logs/runs/RUN-*.yaml（檢查實際工具使用）")
    parser.add_argument("--completion", help="DoD 逐條結果，逗號分隔，如 pass,fail,pass")
    parser.add_argument("--iteration", type=int, default=1, help="目前輪次（從 1 起）")
    parser.add_argument("--max-iterations", type=int, default=None, help="迭代上限（預設 min(max_retries,3)）")
    parser.add_argument("--json", action="store_true", help="輸出 JSON")
    args = parser.parse_args(argv)

    try:
        result = run(
            Path(args.task_card),
            Path(args.run_log) if args.run_log else None,
            parse_completion(args.completion),
            args.iteration,
            args.max_iterations,
        )
    except CollectionError as e:
        msg = {"error": str(e)}
        print(json.dumps(msg, ensure_ascii=False) if args.json else f"⚠️  collection error：{e}")
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_human(result))

    return 0 if result["outcome"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
