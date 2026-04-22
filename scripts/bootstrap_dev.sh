#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REQ_FILE="$ROOT_DIR/requirements-dev.txt"
MODE="${1:-install}"

if [[ ! -f "$REQ_FILE" ]]; then
  echo "ERROR: 找不到 requirements-dev.txt：$REQ_FILE" >&2
  exit 1
fi

if [[ "$MODE" == "--check" ]]; then
  missing=()
  while IFS= read -r raw_line; do
    line="$(echo "$raw_line" | sed 's/#.*$//' | xargs)"
    [[ -z "$line" ]] && continue

    pkg="$(echo "$line" | sed -E 's/[<>=!~].*$//' | sed -E 's/\[.*\]$//')"
    if ! python3 -m pip show "$pkg" >/dev/null 2>&1; then
      missing+=("$pkg")
    fi
  done < "$REQ_FILE"

  if [[ ${#missing[@]} -eq 0 ]]; then
    echo "OK: requirements-dev 依賴皆已安裝"
    exit 0
  fi

  echo "ERROR: 缺少依賴: ${missing[*]}，請執行 ./scripts/bootstrap_dev.sh" >&2
  exit 1
fi

if [[ "$MODE" != "install" ]]; then
  echo "用法: ./scripts/bootstrap_dev.sh [--check]" >&2
  exit 1
fi

python3 -m pip install -r "$REQ_FILE"
echo "OK: 開發依賴安裝完成"
