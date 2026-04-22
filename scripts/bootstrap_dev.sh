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
  if python3 -c "import yaml" >/dev/null 2>&1; then
    echo "OK: PyYAML 已安裝"
    exit 0
  fi
  echo "ERROR: PyYAML 未安裝，請執行 ./scripts/bootstrap_dev.sh" >&2
  exit 1
fi

if [[ "$MODE" != "install" ]]; then
  echo "用法: ./scripts/bootstrap_dev.sh [--check]" >&2
  exit 1
fi

python3 -m pip install -r "$REQ_FILE"
echo "OK: 開發依賴安裝完成"
