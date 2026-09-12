# TaskMate — Backend Development Runner (PowerShell)
# Usage: .\scripts\dev_backend.ps1

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$WorkspaceRoot = (Resolve-Path "$ScriptDir\..").Path
$BackendDir = Join-Path $WorkspaceRoot "backend"
$VenvDir = Join-Path $BackendDir ".venv"
$PythonExe = Join-Path $VenvDir "Scripts\python.exe"
$UvicornExe = Join-Path $VenvDir "Scripts\uvicorn.exe"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " Starting TaskMate FastAPI Backend (Dev) " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Workspace Root: $WorkspaceRoot"

# Check if Python is installed
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python is not found in PATH. Please install Python 3.11+."
    exit 1
}

# Create virtual environment if missing
if (-not (Test-Path $VenvDir)) {
    Write-Host "Creating Python virtual environment in $VenvDir..." -ForegroundColor Yellow
    python -m venv $VenvDir
}

# Activate & verify dependencies
Write-Host "Checking / Installing dependencies from requirements-dev.txt..." -ForegroundColor Yellow
& $PythonExe -m pip install --upgrade pip --quiet
& $PythonExe -m pip install -r "$BackendDir\requirements-dev.txt" --quiet

# Launch FastAPI via Uvicorn with auto-reload
Write-Host "Launching Uvicorn at http://localhost:8000 (Docs: http://localhost:8000/docs)..." -ForegroundColor Green
$env:PYTHONPATH = $WorkspaceRoot
& $UvicornExe backend.app.main:app --reload --host 0.0.0.0 --port 8000
