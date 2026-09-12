# TaskMate — Frontend Development Runner (PowerShell)
# Usage: .\scripts\dev_frontend.ps1

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$WorkspaceRoot = (Resolve-Path "$ScriptDir\..").Path
$FrontendDir = Join-Path $WorkspaceRoot "frontend"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " Starting TaskMate React Frontend (Dev)   " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

Set-Location $FrontendDir

if (-not (Test-Path "node_modules")) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    npm install
}

Write-Host "Launching Vite dev server at http://localhost:5173..." -ForegroundColor Green
npm run dev
