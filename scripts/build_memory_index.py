#!/usr/bin/env python3
"""Build memory/decision_index.json from decision records (gap A4).

Decisions live as scattered YAML under memory/{active,archived}_projects/*/decisions/.
Without an index there's no cheap way to ask "have we decided this before?" at
intake time. This builds a flat, queryable, deterministic index so INTAKE_FLOW
can scan prior decisions before a new Task Card is created.

Usage:
    python3 scripts/build_memory_index.py            # write the index
    python3 scripts/build_memory_index.py --check     # CI drift check (exit 1 on drift)

Output is byte-identical for identical inputs (sorted keys, sorted records), so a
CI drift check can detect a decision added without regenerating the index.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "memory" / "decision_index.json"

GLOBS = (
    ("active", "memory/active_projects/*/decisions/*.yaml"),
    ("archived", "memory/archived_projects/*/decisions/*.yaml"),
)
FIELDS = ("decision_id", "date", "decision", "status", "related_task", "revisit_trigger")


def _project_of(path: Path, scope: str) -> str:
    anchor = f"{scope}_projects"
    parts = path.parts
    return parts[parts.index(anchor) + 1] if anchor in parts else "unknown"


def build(root: Path) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for scope, glob in GLOBS:
        for p in sorted(root.glob(glob)):
            if not p.is_file():
                continue
            try:
                doc = yaml.safe_load(p.read_text(encoding="utf-8"))
            except yaml.YAMLError:
                continue
            if not isinstance(doc, dict):
                continue
            rec = {k: doc.get(k) for k in FIELDS if k in doc}
            rec["project"] = _project_of(p, scope)
            rec["scope"] = scope
            rec["path"] = p.relative_to(root).as_posix()
            records.append(rec)
    records.sort(key=lambda r: (str(r.get("decision_id") or ""), r["path"]))
    return {"count": len(records), "decisions": records}


def dump(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    rendered = dump(build(ROOT))
    if "--check" in args:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != rendered:
            print(f"DRIFT: {OUTPUT.relative_to(ROOT)} is out of date. Re-run scripts/build_memory_index.py.",
                  file=sys.stderr)
            return 1
        print(f"OK: {OUTPUT.relative_to(ROOT)} is up to date.")
        return 0
    OUTPUT.write_text(rendered, encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)} ({json.loads(rendered)['count']} decisions)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
