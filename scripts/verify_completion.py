#!/usr/bin/env python3
"""Independent completion verifier (AGI-1: 20260606-B01).

The harness's executor grades its own homework: it authors `status`,
`gate_results`, `result_summary`, and the audit entry for the very task it just
ran. METR (o3 hacking its own timer) and Apollo (frontier scheming /
self-report falsification) show self-reports cannot be trusted as oversight.

This script is the *independent* check: decoupled from the executor, read-only,
it RECOMPUTES whether a Task Card that claims `done`/`partial` actually produced
what it claims, instead of believing the card.

Verdict tiers (per task):
  OK    — declared artifact exists on disk (and risk placement is correct).
  WARN  — cannot verify, but not a violation: the output location is not a
          single checkable path (e.g. multi-target / "見 DoD"), OR the artifact
          is gone but ``checkpoint: [task_id]`` commits prove work happened
          (artifact later moved/cleaned/promoted).
  FAIL  — genuine reward-hacking signal:
          (a) status done/partial, a single concrete artifact is declared, it
              is MISSING, and there is NO checkpoint commit for the task — i.e.
              the card claims completion with zero on-disk or in-git evidence; or
          (b) a high/critical-risk card routes its output into outputs/reports/
              instead of outputs/drafts/ (risk gate breach).

``--check`` exits non-zero iff any FAIL exists. Reuses generate_audit_log's
find_checkpoints/load_yaml so the git-evidence definition stays single-sourced.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

# Reuse the audit generator's git-evidence + yaml helpers (single source of truth).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_audit_log import find_checkpoints, load_yaml  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TASKS_GLOB = "tasks/20*.yaml"
VERIFIED_STATUSES = {"done", "partial"}

OK, WARN, FAIL = "OK", "WARN", "FAIL"


def artifact_path(task: dict[str, Any]) -> str:
    eo = task.get("expected_output") or {}
    if not isinstance(eo, dict):
        return ""
    loc = str(eo.get("location", "")).rstrip("/")
    fn = str(eo.get("filename", ""))
    return f"{loc}/{fn}" if loc and fn else ""


def is_shallow_repo(root: Path) -> bool:
    """True if `root` is a shallow git clone (history truncated).

    On a shallow clone, `git log --grep="checkpoint: ..."` cannot see older
    checkpoint commits, so "artifact missing + no checkpoints" is *unverifiable*
    rather than a falsification. A reward-hacking detector must not itself emit
    false positives when it can't see the evidence. Non-git dirs → False.
    """
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--is-shallow-repository"],
            cwd=root, check=True, capture_output=True, text=True,
        )
        return out.stdout.strip() == "true"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def is_checkable_path(path: str) -> bool:
    """A single, concrete, on-disk path we can assert existence of.

    Excludes multi-target/free-text locations the corpus sometimes used
    (commas, or non-ASCII like the literal "見 DoD" placeholder).
    """
    if not path:
        return False
    if "," in path:
        return False
    if any(ord(ch) > 127 for ch in path):
        return False
    return path.endswith(tuple(".md .yaml .yml .py .rb .json .html .csv .sh .js .txt".split()))


def evaluate_task(
    task: dict[str, Any],
    root: Path,
    checkpoint_finder: Callable[[str, Path], list] = find_checkpoints,
    shallow: bool = False,
) -> dict[str, Any]:
    """Pure verdict function — returns {task_id, level, reason}. Unit-testable."""
    task_id = str(task.get("task_id", ""))
    status = str(task.get("status", ""))
    risk = str(task.get("risk_level", ""))
    eo = task.get("expected_output") or {}
    loc = str(eo.get("location", "")) if isinstance(eo, dict) else ""
    path = artifact_path(task)

    # Risk gate breach is a hard FAIL regardless of artifact state.
    if risk in ("high", "critical") and "outputs/reports" in loc:
        return {"task_id": task_id, "level": FAIL,
                "reason": f"{risk}-risk output declared under outputs/reports/ (must be outputs/drafts/)"}

    if status not in VERIFIED_STATUSES:
        return {"task_id": task_id, "level": OK, "reason": f"status={status} (not a completion claim)"}

    if not is_checkable_path(path):
        return {"task_id": task_id, "level": WARN,
                "reason": f"output location not a single checkable path ({path or '∅'}) — unverifiable"}

    if (root / path).exists():
        return {"task_id": task_id, "level": OK, "reason": f"artifact present: {path}"}

    # Artifact missing — is there git evidence the work happened?
    checkpoints = checkpoint_finder(task_id, root)
    if checkpoints:
        return {"task_id": task_id, "level": WARN,
                "reason": f"declared artifact missing ({path}) but {len(checkpoints)} checkpoint(s) exist — likely moved/cleaned"}

    if shallow:
        return {"task_id": task_id, "level": WARN,
                "reason": f"declared artifact missing ({path}); shallow clone — checkpoint history unavailable, unverifiable"}

    return {"task_id": task_id, "level": FAIL,
            "reason": f"status={status} but declared artifact missing ({path}) and NO checkpoint evidence "
                      f"— possible self-report falsification"}


def evaluate_all(root: Path) -> list[dict[str, Any]]:
    shallow = is_shallow_repo(root)
    results = []
    for p in sorted(root.glob(TASKS_GLOB)):
        if not p.is_file() or "TEMPLATE" in p.name:
            continue
        doc = load_yaml(p)
        if not doc.get("task_id"):
            continue
        results.append(evaluate_task(doc, root, shallow=shallow))
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="exit non-zero if any task FAILs verification")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--json", action="store_true", help="emit results as JSON")
    parser.add_argument("--task", type=str, default=None, help="verify a single task_id")
    args = parser.parse_args(argv)

    results = evaluate_all(args.root)
    if args.task:
        results = [r for r in results if r["task_id"] == args.task]

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for r in results:
            if r["level"] != OK:
                print(f"[{r['level']}] {r['task_id']}: {r['reason']}")
        counts = {lvl: sum(1 for r in results if r["level"] == lvl) for lvl in (OK, WARN, FAIL)}
        print(f"verify_completion: {len(results)} tasks — OK={counts[OK]} WARN={counts[WARN]} FAIL={counts[FAIL]}")

    fails = [r for r in results if r["level"] == FAIL]
    if args.check and fails:
        print(f"FAILED: {len(fails)} task(s) failed independent completion verification.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
