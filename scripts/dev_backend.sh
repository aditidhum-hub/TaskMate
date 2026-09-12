#!/usr/bin/env bash
# TaskMate — Backend Development Runner (Bash)
# Usage: ./scripts/dev_backend.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$WORKSPACE_ROOT/backend"
VENV_DIR="$BACKEND_DIR/.venv"

echo "=========================================="
echo " Starting TaskMate FastAPI Backend (Dev) "
echo "=========================================="
echo "Workspace Root: $WORKSPACE_ROOT"

if ! command -v python3 &> /dev/null; then
    echo "Error: python3 could not be found. Please install Python 3.11+."
    exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating Python virtual environment in $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
fi

echo "Activating virtual environment and verifying dependencies..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip --quiet
pip install -r "$BACKEND_DIR/requirements-dev.txt" --quiet

echo "Launching Uvicorn at http://localhost:8000 (Docs: http://localhost:8000/docs)..."
export PYTHONPATH="$WORKSPACE_ROOT"
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
