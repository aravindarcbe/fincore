#!/usr/bin/env bash
# Runs the FinCore frontend on macOS/Linux: installs dependencies if
# missing, then starts the dev server. Always operates on this script's own
# folder, so it doesn't matter which directory you launched it from.
#
# Usage:
#   ./run.sh          # port 5173
#   ./run.sh 5174      # custom port

set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

PORT="${1:-5173}"

if [ ! -d "./node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

echo ""
echo "Starting FinCore frontend on http://localhost:${PORT} ..."
echo "Make sure the backend (backend/run.sh) is running too - this proxies /api to it."
echo ""
npm run dev -- --port "$PORT"
