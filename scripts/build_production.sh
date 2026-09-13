#!/usr/bin/env bash
# TaskMate — Production Build & Packaging Script (Bash)
# Usage: ./scripts/build_production.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$WORKSPACE_ROOT/backend"
FRONTEND_DIR="$WORKSPACE_ROOT/frontend"
VENV_DIR="$BACKEND_DIR/.venv"

if [ -f "$VENV_DIR/bin/python" ]; then
    PYTHON_EXE="$VENV_DIR/bin/python"
    RUFF_EXE="$VENV_DIR/bin/ruff"
elif [ -f "$VENV_DIR/Scripts/python.exe" ]; then
    PYTHON_EXE="$VENV_DIR/Scripts/python.exe"
    RUFF_EXE="$VENV_DIR/Scripts/ruff.exe"
else
    PYTHON_EXE="python3"
    RUFF_EXE="ruff"
fi

echo "=========================================================="
echo "       TaskMate — Production Build & Validation          "
echo "=========================================================="
echo "Workspace Root : $WORKSPACE_ROOT"
echo "Timestamp      : $(date)"
echo ""

# 1. Prerequisite Checks
echo ">>> [1/5] Checking Tooling Prerequisites..."
if ! command -v node &> /dev/null; then
    echo "Error: node could not be found. Please install Node.js 18+."
    exit 1
fi
if ! command -v npm &> /dev/null; then
    echo "Error: npm could not be found. Please install npm."
    exit 1
fi
if ! command -v "$PYTHON_EXE" &> /dev/null; then
    echo "Error: python executable not found at $PYTHON_EXE."
    exit 1
fi

echo "Node version   : $(node -v)"
echo "npm version    : $(npm -v)"
echo "Python version : $("$PYTHON_EXE" --version)"
echo "Prerequisites OK."
echo ""

# 2. Backend Linting & Validation
echo ">>> [2/5] Validating Backend Code Quality..."
export PYTHONPATH="$WORKSPACE_ROOT"
if command -v "$RUFF_EXE" &> /dev/null; then
    "$RUFF_EXE" check "$BACKEND_DIR"
    echo "Backend lint clean (0 errors)."
else
    echo "Ruff not available, skipping lint check."
fi
echo ""

# 3. Backend Regression Tests
echo ">>> [3/5] Executing Backend Regression Test Suite..."
"$PYTHON_EXE" -m pytest "$BACKEND_DIR/tests" -q
echo "Backend tests passed successfully."
echo ""

# 4. Frontend Verification & Tests
echo ">>> [4/5] Testing Frontend Application..."
cd "$FRONTEND_DIR"
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm ci
fi

echo "Running frontend TypeScript validation..."
npm run lint

echo "Running frontend automated test suite..."
npm test
echo "Frontend verification passed."
echo ""

# 5. Frontend Production Bundle Build
echo ">>> [5/5] Compiling Production Frontend Bundle..."
npm run build

DIST_DIR="$FRONTEND_DIR/dist"
if [ ! -f "$DIST_DIR/index.html" ]; then
    echo "Error: Build output missing index.html in $DIST_DIR"
    exit 1
fi

echo ""
echo "=========================================================="
echo "       TaskMate Production Build Succeeded!              "
echo "=========================================================="
echo "Frontend Assets : $DIST_DIR"
echo "Backend Image   : Ready to containerize via Dockerfile"
echo "Production State: VERIFIED & READY FOR DEPLOYMENT"
echo ""
