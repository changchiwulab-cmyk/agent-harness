#!/usr/bin/env python3
"""Check that every Task Card with status in {done, review} has its
expected_output file physically present in the working tree.

Scope:
- Only tasks/20*.yaml (top-level). Skips tasks/archived/ and tasks/examples/.
- Only existence is checked. Content / schema is left to other validators.

Exits non-zero on any missing expected_output.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TASKS_GLOB = "tasks/20*.yaml"
TARGET_STATUSES = {"done", "review"}


def find_missing(root: Path) -> list[tuple[str, str]]:
    """Return list of (task_card_path, missing_output_path) for failing cards."""
    missing: list[tuple[str, str]] = []
    for path in sorted(root.glob(TASKS_GLOB)):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            missing.append((str(path.relative_to(root)), f"YAML parse error: {exc}"))
            continue

        status = data.get("status")
        if status not in TARGET_STATUSES:
            continue

        output = data.get("expected_output") or {}
        if (output.get("format") or "").strip() == "multi":
            continue
        location = (output.get("location") or "").strip()
        filename = (output.get("filename") or "").strip()
        if not location or not filename:
            missing.append(
                (
                    str(path.relative_to(root)),
                    "expected_output.location/filename missing or empty",
                )
            )
            continue

        target = (root / location / filename).resolve()
        if not target.exists():
            try:
                rel = target.relative_to(root)
            except ValueError:
                rel = target
            missing.append((str(path.relative_to(root)), str(rel)))

    return missing


def main(argv: list[str]) -> int:
    root = ROOT
    missing = find_missing(root)
    if missing:
        print("FAIL: expected_output files missing for done/review Task Cards:")
        for card, target in missing:
            print(f"  - {card} -> {target}")
        print(
            "Hint: either restore the output, or move the card to "
            "tasks/archived/ if the work is being parked."
        )
        return 1
    print("OK: all done/review Task Cards have their expected_output present.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
