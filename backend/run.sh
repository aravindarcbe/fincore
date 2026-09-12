#!/usr/bin/env bash
# Runs the FinCore backend on macOS/Linux: creates the venv if missing,
# installs dependencies, then starts the API. Always operates on this
# script's own folder, so it doesn't matter which directory you launched it
# from.
#
# Usage:
#   ./run.sh          # port 8000
#   ./run.sh 8001      # custom port

set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

PORT="${1:-8000}"

if [ ! -f "./venv/bin/python" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Installing dependencies..."
./venv/bin/pip install --upgrade pip --quiet
./venv/bin/pip install -r requirements.txt

echo ""
echo "Starting FinCore backend on http://localhost:${PORT} ..."
echo "If you change this port, update frontend/vite.config.js's proxy target to match."
echo ""
./venv/bin/uvicorn app.main:app --reload --port "$PORT"
