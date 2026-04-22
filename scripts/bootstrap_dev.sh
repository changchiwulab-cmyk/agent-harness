#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REQ_FILE="$ROOT_DIR/requirements-dev.txt"

if [[ ! -f "$REQ_FILE" ]]; then
  echo "ERROR: 找不到 requirements-dev.txt：$REQ_FILE" >&2
  exit 1
fi

python3 -m pip install -r "$REQ_FILE"
echo "OK: 開發依賴安裝完成"
