#!/usr/bin/env bash
# Smoke: wheel limpio → lablog --help + health (si serve no se lanza aquí).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

cd "$ROOT"
uv build -q
WHEEL="$(ls -1 dist/jose_labarca_lablog-*.whl | tail -1)"
python -m venv "$TMP/venv"
# shellcheck disable=SC1091
source "$TMP/venv/bin/activate"
pip install -q "$WHEEL"
lablog --help >/dev/null
python -c "from lablog.templates import list_templates; assert list_templates()"
echo "smoke_install: OK ($WHEEL)"
