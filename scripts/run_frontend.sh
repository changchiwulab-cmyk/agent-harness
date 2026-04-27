#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${1:-8000}"

cd "$ROOT_DIR"
python3 scripts/generate_frontend_manifest.py

echo "Frontend available at: http://localhost:${PORT}/frontend/index.html"
exec python3 -m http.server "$PORT"
