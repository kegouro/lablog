#!/usr/bin/env bash
# Build the portable, offline lablog desktop bundle.
#
#   ./scripts/package_desktop.sh
#
# Output: dist/lablog/  (a self-contained folder; zip and ship it).
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> Building the UI (offline bundle: KaTeX + fonts included)"
( cd ui && npm install && npm run build )

echo "==> Installing desktop + packaging dependencies"
uv sync --extra desktop
uv pip install pyinstaller

echo "==> Packaging with PyInstaller"
uv run pyinstaller --noconfirm lablog.spec

echo "==> Done. Bundle at: dist/lablog/"
echo "    Run it with: dist/lablog/lablog"
