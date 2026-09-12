#!/usr/bin/env bash
# TaskMate — Frontend Development Runner (Bash)
# Usage: ./scripts/dev_frontend.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FRONTEND_DIR="$WORKSPACE_ROOT/frontend"

echo "=========================================="
echo " Starting TaskMate React Frontend (Dev)   "
echo "=========================================="

cd "$FRONTEND_DIR"

if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

echo "Launching Vite dev server at http://localhost:5173..."
npm run dev
