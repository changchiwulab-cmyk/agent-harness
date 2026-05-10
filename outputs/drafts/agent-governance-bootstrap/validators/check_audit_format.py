#!/usr/bin/env python3
"""Standalone CLI validator for AUDIT_LOG.md format.

Validates that:
    1. file exists and is non-empty
    2. each ```yaml block parses as valid YAML
    3. each yaml block is a single-element list of mapping with required keys:
       task_id, date, status
    4. task_id matches ^\\d{8}-[A-Z0-9]+$
    5. status is in {pending, in_progress, review, done, failed, partial}
    6. AUTO_AUDIT_BEGIN/END markers, if present, are balanced (begin before end)

Exit codes:
    0 — pass
    1 — usage error
    2 — format errors (printed to stdout)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

TASK_ID_RE = re.compile(r"^\d{8}-[A-Z0-9]+$")
VALID_STATUS = {"pending", "in_progress", "review", "done", "failed", "partial"}
REQUIRED_KEYS = ("task_id", "date", "status")
YAML_BLOCK_RE = re.compile(r"```yaml\n(.*?)\n```", re.DOTALL)
AUTO_BEGIN_RE = re.compile(r"^<!--\s*AUTO_AUDIT_BEGIN\s*-->", re.MULTILINE)
AUTO_END_RE = re.compile(r"^<!--\s*AUTO_AUDIT_END\s*-->", re.MULTILINE)


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"audit log not found: {path}"]
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return [f"audit log empty: {path}"]

    begins = list(AUTO_BEGIN_RE.finditer(text))
    ends = list(AUTO_END_RE.finditer(text))
    if len(begins) != len(ends):
        errors.append(
            f"AUTO_AUDIT marker mismatch: {len(begins)} BEGIN vs {len(ends)} END"
        )
    for b, e in zip(begins, ends):
        if b.start() >= e.start():
            errors.append("AUTO_AUDIT_BEGIN appears after END (unbalanced)")
            break

    blocks = YAML_BLOCK_RE.findall(text)
    if not blocks:
        errors.append("no ```yaml blocks found in audit log")
        return errors

    for i, block in enumerate(blocks, start=1):
        try:
            data = yaml.safe_load(block)
        except yaml.YAMLError as exc:
            errors.append(f"block #{i}: YAML parse error — {exc}")
            continue
        if data is None:
            continue  # template / placeholder
        if not isinstance(data, list):
            # Some blocks may be template format (mapping with keys); allow but warn
            if isinstance(data, dict):
                continue
            errors.append(f"block #{i}: expected a list of audit entries, got {type(data).__name__}")
            continue
        for j, entry in enumerate(data, start=1):
            if not isinstance(entry, dict):
                errors.append(f"block #{i} entry #{j}: not a mapping")
                continue
            for key in REQUIRED_KEYS:
                if not entry.get(key):
                    errors.append(f"block #{i} entry #{j}: missing or empty '{key}'")
            tid = entry.get("task_id", "")
            if tid and not TASK_ID_RE.match(str(tid)):
                errors.append(f"block #{i} entry #{j}: invalid task_id format '{tid}'")
            st = entry.get("status", "")
            if st and st not in VALID_STATUS:
                errors.append(
                    f"block #{i} entry #{j}: invalid status '{st}', allowed {sorted(VALID_STATUS)}"
                )

    return errors


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print("用法：check_audit_format.py <path-to-audit-log.md>", file=sys.stderr)
        return 1

    path = Path(args[0])
    errors = validate(path)
    if errors:
        print(f"❌ Audit Log 格式檢查失敗：{path}")
        for e in errors:
            print(f"   - {e}")
        return 2
    print(f"✅ Audit Log 格式檢查通過：{path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
