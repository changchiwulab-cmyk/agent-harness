#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BOOTSTRAP="$ROOT_DIR/scripts/bootstrap_dev.sh"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

REQ_FILE_PATH="$TMP_DIR/requirements-dev.txt"
MOCK_PIP_SHOW="$TMP_DIR/mock_pip_show.sh"

cat > "$MOCK_PIP_SHOW" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
pkg="${1:-}"
case "$pkg" in
  pyyaml|requests) exit 0 ;;
  *) exit 1 ;;
esac
EOF
chmod +x "$MOCK_PIP_SHOW"

# Case 1: comments / blank lines / version / extras should parse and pass
cat > "$REQ_FILE_PATH" <<'EOF'
# comment line

pyyaml>=6.0
requests[security]==2.0
EOF

REQ_FILE="$REQ_FILE_PATH" PIP_SHOW_BIN="$MOCK_PIP_SHOW" "$BOOTSTRAP" --check

# Case 2: missing package should fail and print package name
cat > "$REQ_FILE_PATH" <<'EOF'
pyyaml>=6.0
missing_pkg==1.0
EOF

set +e
OUTPUT="$(REQ_FILE="$REQ_FILE_PATH" PIP_SHOW_BIN="$MOCK_PIP_SHOW" "$BOOTSTRAP" --check 2>&1)"
CODE=$?
set -e

if [[ $CODE -eq 0 ]]; then
  echo "expected non-zero exit code when package is missing" >&2
  exit 1
fi

echo "$OUTPUT" | grep -q "missing_pkg"
echo "OK: bootstrap_dev --check tests passed"
