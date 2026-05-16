#!/usr/bin/env python3
"""Machine-check CLAUDE.md hard-rule 3 against the execution-log artifacts.

Rule 3: 連續失敗 3 次就停下來，寫 logs/errors/ 並通知使用者，不自行硬修。

The harness enforces this the same way it enforces every other spec — as a
checkable invariant over the artifacts on disk, not a runtime daemon:

    For every logs/runs/*.y{a,}ml whose
        execution_log.retry_policy.consecutive_failures >= 3
    it MUST have
        execution_log.retry_policy.failure_policy_action == "stopped"
    AND a logs/errors/*.md record whose task_id matches.

No logs/runs/ at all -> vacuously OK (exit 0). Any violation -> exit 1.
Files that predate the retry_policy field default to 0 failures (compatible).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
_FENCE_RE = re.compile(r"```yaml\s*\n(.*?)\n```", re.DOTALL)
THRESHOLD = 3


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def error_log_task_ids(root: Path) -> set[str]:
    ids: set[str] = set()
    for p in sorted((root / "logs" / "errors").glob("*.md")):
        if "TEMPLATE" in p.name:
            continue
        m = _FENCE_RE.search(p.read_text(encoding="utf-8"))
        if not m:
            continue
        try:
            doc = yaml.safe_load(m.group(1))
        except yaml.YAMLError:
            continue
        if isinstance(doc, dict) and doc.get("task_id"):
            ids.add(str(doc["task_id"]).strip())
    return ids


def check(root: Path) -> list[str]:
    runs_dir = root / "logs" / "runs"
    run_files = sorted(runs_dir.glob("*.yaml")) + sorted(runs_dir.glob("*.yml"))
    if not run_files:
        return []  # vacuously true

    err_ids = error_log_task_ids(root)
    violations: list[str] = []
    for rf in run_files:
        log = _load_yaml(rf).get("execution_log", {})
        if not isinstance(log, dict):
            continue
        rp = log.get("retry_policy") or {}
        try:
            cf = int(rp.get("consecutive_failures", 0) or 0)
        except (TypeError, ValueError):
            cf = 0
        if cf < THRESHOLD:
            continue
        task_id = str(log.get("task_id", "")).strip()
        action = str(rp.get("failure_policy_action", "none")).strip()
        rel = rf.relative_to(root).as_posix()
        if action != "stopped":
            violations.append(
                f"{rel}: consecutive_failures={cf} 但 failure_policy_action="
                f"'{action}'（規則3 應為 'stopped'）"
            )
        if task_id not in err_ids:
            violations.append(
                f"{rel}: consecutive_failures={cf} 但 logs/errors/ 無 task_id="
                f"'{task_id}' 的紀錄（規則3 要求寫 error log）"
            )
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)

    violations = check(args.root)
    if violations:
        print("FAIL: 規則3（連續失敗 3 次須停 + error log）違反：", file=sys.stderr)
        for v in violations:
            print(f"  - {v}", file=sys.stderr)
        return 1
    print("OK: 規則3 失敗政策檢查通過（logs/runs/ 無 >=3 連敗未停的紀錄）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
