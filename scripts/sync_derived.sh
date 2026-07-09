#!/usr/bin/env bash
# Regenerate every backend-derived frontend artifact in one place.
#
# Single source of truth for "the set of derived artifacts" — reused by the
# git pre-commit hook (.githooks/pre-commit), the CI workflow
# (.github/workflows/spec-consistency.yml) and the Claude harness Stop hook
# (.claude/settings.json), so the front-end view never drifts from the
# back-end YAML.
#
# Derived artifacts kept aligned with their YAML / git sources:
#   - frontend/data.json   (scripts/generate_frontend_manifest.py)
#   - logs/AUDIT_LOG.md     (scripts/generate_audit_log.py)
#
# Usage:
#   scripts/sync_derived.sh           Regenerate (write) the artifacts.
#   scripts/sync_derived.sh --check   Verify only; exit non-zero on drift.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Neither derived file may carry committed merge-conflict garbage. The audit
# generator preserves the manual-notes section verbatim, so markers there
# survive regeneration and pass the drift check silently (seen in PR #129).
check_conflict_markers() {
  if grep -nE '^(<{7}|={7}|>{7})' logs/AUDIT_LOG.md frontend/data.json; then
    echo "ERROR: merge-conflict markers found in derived artifacts." >&2
    exit 1
  fi
}

# Audit log first: frontend/data.json's governance alerts (M3) read
# logs/AUDIT_LOG.md via load_audit_task_ids, so the manifest must be
# generated from the fresh audit log or it lags one run behind.
if [[ "${1:-}" == "--check" ]]; then
  check_conflict_markers
  python3 scripts/generate_audit_log.py --check
  python3 scripts/generate_frontend_manifest.py --check
else
  python3 scripts/generate_audit_log.py
  python3 scripts/generate_frontend_manifest.py
  check_conflict_markers
fi
