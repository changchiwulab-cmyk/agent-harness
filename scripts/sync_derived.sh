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

if [[ "${1:-}" == "--check" ]]; then
  python3 scripts/generate_frontend_manifest.py --check
  python3 scripts/generate_audit_log.py --check
else
  python3 scripts/generate_frontend_manifest.py
  python3 scripts/generate_audit_log.py
fi
