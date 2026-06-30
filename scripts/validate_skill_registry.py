#!/usr/bin/env python3
"""Validate skills/REGISTRY.yaml against the skills/ directory (bidirectional).

REGISTRY.yaml is the single source of truth for skill metadata (trigger
keywords, token budgets, default tools). This check keeps it honest:
    * every registered skill has a real skills/<name>/SKILL.md
    * every skills/<name>/SKILL.md is registered
    * skill_type values are the canonical five
    * required per-skill fields are present

Usage:
    validate_skill_registry.py            # print result
    validate_skill_registry.py --check    # exit non-zero on any drift (CI)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "skills" / "REGISTRY.yaml"
CANONICAL_SKILLS = {"research", "analysis", "writing", "ops", "review"}
REQUIRED_FIELDS = ("description", "path", "trigger_keywords", "token_budget", "default_allowed_tools")


def load_registry(root: Path = ROOT) -> dict[str, Any]:
    path = root / "skills" / "REGISTRY.yaml"
    with path.open("r", encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    return doc if isinstance(doc, dict) else {}


def discover_skill_dirs(root: Path = ROOT) -> set[str]:
    base = root / "skills"
    found = set()
    for p in sorted(base.iterdir()) if base.exists() else []:
        if p.is_dir() and (p / "SKILL.md").is_file():
            found.add(p.name)
    return found


def validate(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    doc = load_registry(root)
    skills = doc.get("skills")
    if not isinstance(skills, dict) or not skills:
        return ["REGISTRY.yaml: 'skills' mapping missing or empty"]

    registered = set(skills.keys())
    on_disk = discover_skill_dirs(root)

    for name in sorted(registered - on_disk):
        errors.append(f"registered skill '{name}' has no skills/{name}/SKILL.md")
    for name in sorted(on_disk - registered):
        errors.append(f"skills/{name}/ exists but is not registered in REGISTRY.yaml")

    for name, meta in skills.items():
        if name not in CANONICAL_SKILLS:
            errors.append(f"skill '{name}' is not one of the canonical skills {sorted(CANONICAL_SKILLS)}")
        if not isinstance(meta, dict):
            errors.append(f"skill '{name}': entry must be a mapping")
            continue
        for field in REQUIRED_FIELDS:
            value = meta.get(field)
            empty = value is None or (hasattr(value, "__len__") and len(value) == 0)
            if empty:
                errors.append(f"skill '{name}': missing/empty field '{field}'")
        path = meta.get("path")
        if isinstance(path, str) and path and not (root / path).is_dir():
            errors.append(f"skill '{name}': path '{path}' is not a directory")

    return errors


def main(argv: list[str] | None = None) -> int:
    # --check is accepted for CI symmetry; this validator always fails on drift.
    errors = validate(ROOT)
    if errors:
        print("FAILED: skill registry inconsistencies:", file=sys.stderr)
        for e in errors:
            print(f"- {e}", file=sys.stderr)
        return 1
    print(f"OK: skill registry consistent ({len(load_registry().get('skills', {}))} skills).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
