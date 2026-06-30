#!/usr/bin/env python3
"""Retrieve relevant episodes + playbook entries for an incoming task.

Used at INTAKE time (see system/INTAKE_FLOW.md): given a skill_type and a few
goal keywords, surface past episodes (how similar tasks went, what tripped them
up) and playbook entries (reusable heuristics) to inject into context.

Reading memory is allow-tier (see MEMORY_POLICY.md) — this is pure retrieval,
no writes. Matching is keyword/tag based over the indexes built by
scripts/build_memory_index.py; no vector store (Decision D008).

Usage:
    memory_retrieve.py --skill research --keywords "web search,rate limit"
    memory_retrieve.py --skill review --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
EPISODES_INDEX = ROOT / "memory" / "episodes" / "INDEX.yaml"
PLAYBOOK_INDEX = ROOT / "memory" / "playbook" / "INDEX.yaml"

SKILL_MATCH = 2
TAG_MATCH = 3
TEXT_MATCH = 1


def _load_index(path: Path, key: str) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        doc = yaml.safe_load(f) or {}
    items = doc.get(key)
    return items if isinstance(items, list) else []


def _norm_keywords(keywords: list[str] | None) -> list[str]:
    out: list[str] = []
    for kw in keywords or []:
        for part in str(kw).replace(",", " ").split():
            part = part.strip().lower()
            if part:
                out.append(part)
    return out


def score_item(item: dict[str, Any], skill: str | None, keywords: list[str]) -> int:
    score = 0
    if skill and item.get("skill_type") == skill:
        score += SKILL_MATCH
    tags = [str(t).lower() for t in item.get("tags", [])]
    text = " ".join(
        str(item.get(f, "")) for f in ("title", "goal", "outcome")
    ).lower()
    for kw in keywords:
        if any(kw in tag or tag in kw for tag in tags):
            score += TAG_MATCH
        elif kw in text:
            score += TEXT_MATCH
    return score


def retrieve(
    skill: str | None = None,
    keywords: list[str] | None = None,
    *,
    root: Path = ROOT,
    top: int = 5,
) -> dict[str, list[dict[str, Any]]]:
    kws = _norm_keywords(keywords)
    episodes = _load_index(root / "memory" / "episodes" / "INDEX.yaml", "episodes")
    playbook = _load_index(root / "memory" / "playbook" / "INDEX.yaml", "entries")

    def rank(items: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
        scored = []
        for it in items:
            s = score_item(it, skill, kws)
            # With no keywords, a skill filter alone still surfaces that skill's
            # entries; otherwise require a positive signal.
            if s > 0 or (not kws and skill and it.get("skill_type") == skill):
                scored.append({**it, "kind": kind, "score": s})
        scored.sort(key=lambda d: (-d["score"], d["id"]))
        return scored[:top]

    return {
        "episodes": rank(episodes, "episode"),
        "playbook": rank(playbook, "playbook"),
    }


def format_human(results: dict[str, list[dict[str, Any]]]) -> str:
    lines: list[str] = []
    for section, label in (("playbook", "Playbook 啟發"), ("episodes", "相關 Episodes")):
        items = results.get(section, [])
        lines.append(f"## {label}（{len(items)}）")
        if not items:
            lines.append("（無相關條目）")
        for it in items:
            head = it.get("title") or it.get("goal") or it.get("id")
            lines.append(f"- [{it['id']}] {head}  (score={it['score']}, {it['path']})")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", default=None, help="skill_type filter")
    parser.add_argument("--keywords", default="", help="comma/space separated keywords")
    parser.add_argument("--top", type=int, default=5)
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args(argv)

    results = retrieve(args.skill, [args.keywords], top=args.top)
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        sys.stdout.write(format_human(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
