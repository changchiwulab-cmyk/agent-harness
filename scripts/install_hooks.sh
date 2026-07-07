#!/usr/bin/env bash
# Activate the versioned git hooks in .githooks/ for this clone.
#
# Points core.hooksPath at the repo's .githooks/ directory so the pre-commit
# hook auto-aligns frontend/data.json + logs/AUDIT_LOG.md on every commit.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

git config core.hooksPath .githooks
echo "Enabled git hooks from .githooks/ (core.hooksPath=.githooks)."
