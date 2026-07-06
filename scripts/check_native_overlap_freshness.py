#!/usr/bin/env python3
"""Check freshness of system/NATIVE_OVERLAP.yaml.

The native-overlap snapshot needs periodic re-review (per the file's own
`revisit_trigger`). This script reads `reviewed_on` and `stale_after_days`
and prints a warning if the snapshot is older than the threshold.

Exit code is always 0 — staleness is advisory, not a CI gate.
Run manually or wire into a periodic reminder.
"""

from __future__ import annotations

import sys
from datetime import date, datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
NATIVE_OVERLAP_PATH = ROOT / "system" / "NATIVE_OVERLAP.yaml"


def main() -> int:
    if not NATIVE_OVERLAP_PATH.exists():
        print(f"missing: {NATIVE_OVERLAP_PATH}", file=sys.stderr)
        return 0

    with NATIVE_OVERLAP_PATH.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    reviewed_on = data.get("reviewed_on")
    threshold = data.get("stale_after_days", 90)

    if isinstance(reviewed_on, str):
        reviewed_date = datetime.strptime(reviewed_on, "%Y-%m-%d").date()
    elif isinstance(reviewed_on, date):
        reviewed_date = reviewed_on
    else:
        print("reviewed_on missing or malformed; treat as stale")
        return 0

    age = (date.today() - reviewed_date).days
    if age > threshold:
        print(
            f"STALE: NATIVE_OVERLAP.yaml reviewed {age} days ago "
            f"(threshold {threshold}). Re-evaluate per revisit_trigger."
        )
    else:
        print(f"FRESH: NATIVE_OVERLAP.yaml reviewed {age} days ago (threshold {threshold}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
