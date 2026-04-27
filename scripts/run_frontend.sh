#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="8000"
NO_GENERATE="false"

for arg in "$@"; do
  case "$arg" in
    --no-generate)
      NO_GENERATE="true"
      ;;
    ''|*[!0-9]*)
      echo "Unsupported argument: $arg" >&2
      echo "Usage: scripts/run_frontend.sh [--no-generate] [port]" >&2
      exit 1
      ;;
    *)
      PORT="$arg"
      ;;
  esac
done

cd "$ROOT_DIR"
if [[ "$NO_GENERATE" != "true" ]]; then
  python3 scripts/generate_frontend_manifest.py
fi

echo "Frontend available at: http://localhost:${PORT}/frontend/index.html"
exec python3 -m http.server "$PORT"
