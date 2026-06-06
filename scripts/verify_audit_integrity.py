#!/usr/bin/env python3
"""Memory & audit integrity verifier (AGI-3: 20260606-B01).

Defends against OWASP ASI06 (memory & context poisoning) and the "agent edits
its own audit trail" hole. Long-term memory (decision logs, plans, project
context) is human-confirmed on write (GLOBAL_RULES 記憶規則) but has, until now,
had NO tamper-evidence: a later silent edit — by a future more-capable model,
a prompt-injected tool, or an attacker — would go undetected and poison all
downstream reasoning.

Two checks:

  HARD (── `--check` exits non-zero ──) Memory tamper-evidence:
    Every tracked memory file's sha256 must match memory/INTEGRITY_MANIFEST.yaml.
    Mismatch (tampered), missing manifest entry for an existing file (untracked
    poison injection), or a manifest file gone missing (deletion) all FAIL.
    The manifest is updated ONLY via `--update`, which is meant to be run after
    a human approves a memory write — making every memory change explicit and
    git-anchored.

  SOFT (── reported as WARN, never fails ──) Audit trail health:
    - Coverage: every done/failed Task Card should appear in logs/AUDIT_LOG.md
      (catches a task silently omitted from the audit trail).
    - Drift: whether scripts/generate_audit_log.py would rewrite the auto-section
      (informational — the live log is hand-maintained and not yet migrated to
      the generated format; migration is tracked as a separate recommendation).

Read-only except for `--update`.
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_REL = "memory/INTEGRITY_MANIFEST.yaml"
AUDIT_REL = "logs/AUDIT_LOG.md"

# Long-term memory artifacts whose integrity matters (decisions, plans, context).
TRACKED_GLOBS = [
    "memory/active_projects/*/context.md",
    "memory/active_projects/*/decisions/*.yaml",
    "memory/active_projects/*/plans/*.md",
]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tracked_files(root: Path) -> list[str]:
    found: set[str] = set()
    for pattern in TRACKED_GLOBS:
        for p in glob.glob(str(root / pattern)):
            rp = Path(p)
            if rp.is_file():
                found.add(rp.relative_to(root).as_posix())
    return sorted(found)


def load_manifest(root: Path) -> dict[str, str]:
    mpath = root / MANIFEST_REL
    if not mpath.exists():
        return {}
    doc = yaml.safe_load(mpath.read_text(encoding="utf-8")) or {}
    files = doc.get("files") if isinstance(doc, dict) else None
    return files if isinstance(files, dict) else {}


def build_manifest(root: Path) -> str:
    files = {rel: sha256_file(root / rel) for rel in tracked_files(root)}
    header = (
        "# Memory Integrity Manifest — 長期記憶防竄改（AGI-3, OWASP ASI06）\n"
        "# 由 scripts/verify_audit_integrity.py --update 產生（僅在人工核可記憶寫入後執行）。\n"
        "# --check 重算 sha256 比對，偵測未經核可的竄改/投毒/刪除。\n\n"
    )
    body = yaml.safe_dump({"files": files}, sort_keys=True, allow_unicode=True, default_flow_style=False)
    return header + body


def check_memory(root: Path) -> list[str]:
    """Return list of HARD failures (empty == integrity intact)."""
    fails: list[str] = []
    manifest = load_manifest(root)
    on_disk = {rel: sha256_file(root / rel) for rel in tracked_files(root)}

    for rel, digest in on_disk.items():
        if rel not in manifest:
            fails.append(f"UNTRACKED memory file (not in manifest — possible injection): {rel}")
        elif manifest[rel] != digest:
            fails.append(f"TAMPERED memory file (sha256 mismatch): {rel}")
    for rel in manifest:
        if rel not in on_disk:
            fails.append(f"MISSING memory file (in manifest but gone from disk): {rel}")
    return fails


def check_audit_soft(root: Path) -> list[str]:
    """Return list of SOFT warnings (audit coverage + generator drift)."""
    warns: list[str] = []
    audit_path = root / AUDIT_REL
    audit_text = audit_path.read_text(encoding="utf-8") if audit_path.exists() else ""
    for p in sorted(glob.glob(str(root / "tasks/20*.yaml"))):
        try:
            d = yaml.safe_load(Path(p).read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(d, dict) or d.get("status") not in ("done", "failed"):
            continue
        tid = str(d.get("task_id", ""))
        if tid and tid not in audit_text:
            warns.append(f"audit coverage gap: done/failed task {tid} not found in {AUDIT_REL}")

    # Drift is informational only (live log is hand-maintained, not yet migrated).
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from generate_audit_log import build_document, collect_tasks, derive_record  # noqa: E402

        records = [derive_record(t, root) for t in collect_tasks(root)]
        rendered = build_document(records, audit_text)
        if rendered != audit_text:
            warns.append(
                "audit generator would rewrite the auto-section "
                "(AUDIT_LOG.md not yet migrated to generated format — recommend a migration task)"
            )
    except Exception as e:  # pragma: no cover - defensive
        warns.append(f"audit drift check skipped: {e}")
    return warns


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="exit non-zero on any HARD memory-integrity failure")
    parser.add_argument("--update", action="store_true", help="(re)write INTEGRITY_MANIFEST.yaml from current memory files")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    root = args.root

    if args.update:
        out = root / MANIFEST_REL
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(build_manifest(root), encoding="utf-8")
        print(f"Updated {MANIFEST_REL} ({len(tracked_files(root))} tracked memory files)")
        return 0

    fails = check_memory(root)
    warns = check_audit_soft(root)

    for w in warns:
        print(f"[WARN] {w}")
    for f in fails:
        print(f"[FAIL] {f}")
    print(f"verify_audit_integrity: memory FAIL={len(fails)} | audit WARN={len(warns)}")

    if args.check and fails:
        print(f"FAILED: {len(fails)} memory-integrity violation(s).", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
