#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="8000"
NO_GENERATE="false"
SCRIPT_VERSION="1.3.0"
LAST_UPDATED="2026-04-27"

print_help() {
  cat <<'HELP'
Usage:
  scripts/run_frontend.sh [--no-generate] [port]
  scripts/run_frontend.sh --help
  scripts/run_frontend.sh --version

Options:
  --no-generate   Skip manifest generation and only start http.server.
  --help, -h      Show this help message.
  --version, -v   Show script version and last updated date.

Examples:
  scripts/run_frontend.sh
  scripts/run_frontend.sh 9000
  scripts/run_frontend.sh --no-generate
  scripts/run_frontend.sh --no-generate 9000
  scripts/run_frontend.sh --version
HELP
}

print_version() {
  echo "scripts/run_frontend.sh version ${SCRIPT_VERSION} (last updated: ${LAST_UPDATED})"
}

for arg in "$@"; do
  case "$arg" in
    --help|-h)
      print_help
      exit 0
      ;;
    --version|-v)
      print_version
      exit 0
      ;;
    --no-generate)
      NO_GENERATE="true"
      ;;
    ''|*[!0-9]*)
      echo "Unsupported argument: $arg" >&2
      print_help >&2
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
