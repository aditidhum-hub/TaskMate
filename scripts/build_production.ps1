# TaskMate - Production Build and Packaging Script (PowerShell)
# Usage: .\scripts\build_production.ps1

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$WorkspaceRoot = (Resolve-Path "$ScriptDir\..").Path
$BackendDir = Join-Path $WorkspaceRoot "backend"
$FrontendDir = Join-Path $WorkspaceRoot "frontend"
$VenvDir = Join-Path $BackendDir ".venv"

if (Test-Path "$VenvDir\Scripts\python.exe") {
    $PythonExe = "$VenvDir\Scripts\python.exe"
} else {
    $PythonExe = "python"
}

Write-Host '==========================================================' -ForegroundColor Cyan
Write-Host '       TaskMate - Production Build and Validation         ' -ForegroundColor Cyan
Write-Host '==========================================================' -ForegroundColor Cyan
Write-Host "Workspace Root : $WorkspaceRoot"
Write-Host "Timestamp      : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ''

# 1. Prerequisite Checks
Write-Host '[1/5] Checking Tooling Prerequisites...' -ForegroundColor Yellow
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Error 'Node.js is not found in PATH. Please install Node.js 18+.'
    exit 1
}
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Error 'npm is not found in PATH. Please install npm.'
    exit 1
}
if (-not (Get-Command $PythonExe -ErrorAction SilentlyContinue)) {
    Write-Error "Python executable not found at $PythonExe."
    exit 1
}

$NodeVersion = & node -v
$NpmVersion = & npm -v
$PyVersion = & $PythonExe --version
Write-Host "Node version   : $NodeVersion"
Write-Host "npm version    : $NpmVersion"
Write-Host "Python version : $PyVersion"
Write-Host 'Prerequisites OK.' -ForegroundColor Green
Write-Host ''

# 2. Backend Linting & Validation
Write-Host '[2/5] Validating Backend Code Quality...' -ForegroundColor Yellow
$env:PYTHONPATH = $WorkspaceRoot
if (Test-Path "$VenvDir\Scripts\ruff.exe") {
    & "$VenvDir\Scripts\ruff.exe" check "$BackendDir"
    if ($LASTEXITCODE -ne 0) {
        Write-Error 'Backend linting failed.'
        exit 1
    }
    Write-Host 'Backend lint clean (0 errors).' -ForegroundColor Green
} else {
    Write-Host 'Ruff not found in venv, skipping linter check.' -ForegroundColor Gray
}
Write-Host ''

# 3. Backend Regression Tests
Write-Host '[3/5] Executing Backend Regression Test Suite...' -ForegroundColor Yellow
& $PythonExe -m pytest "$BackendDir/tests" -q
if ($LASTEXITCODE -ne 0) {
    Write-Error 'Backend regression tests failed.'
    exit 1
}
Write-Host 'Backend tests passed successfully.' -ForegroundColor Green
Write-Host ''

# 4. Frontend Verification & Tests
Write-Host '[4/5] Testing Frontend Application...' -ForegroundColor Yellow
Push-Location $FrontendDir
try {
    if (-not (Test-Path "node_modules")) {
        Write-Host 'Installing frontend dependencies...' -ForegroundColor Yellow
        npm ci
    }

    Write-Host 'Running frontend TypeScript validation...' -ForegroundColor Yellow
    npm run lint
    if ($LASTEXITCODE -ne 0) {
        Write-Error 'Frontend TypeScript validation failed.'
        exit 1
    }

    Write-Host 'Running frontend automated test suite...' -ForegroundColor Yellow
    npm test
    if ($LASTEXITCODE -ne 0) {
        Write-Error 'Frontend automated test suite failed.'
        exit 1
    }
}
finally {
    Pop-Location
}
Write-Host 'Frontend verification passed.' -ForegroundColor Green
Write-Host ''

# 5. Frontend Production Bundle Build
Write-Host '[5/5] Compiling Production Frontend Bundle...' -ForegroundColor Yellow
Push-Location $FrontendDir
try {
    npm run build
    if ($LASTEXITCODE -ne 0) {
        Write-Error 'Frontend production build failed.'
        exit 1
    }
}
finally {
    Pop-Location
}

$DistDir = Join-Path $FrontendDir "dist"
if (-not (Test-Path "$DistDir\index.html")) {
    Write-Error "Build output missing index.html in $DistDir"
    exit 1
}

$DistFiles = Get-ChildItem -Path $DistDir -Recurse -File
$TotalSizeBytes = ($DistFiles | Measure-Object -Property Length -Sum).Sum
$TotalSizeKB = [math]::Round($TotalSizeBytes / 1024, 2)

Write-Host ''
Write-Host '==========================================================' -ForegroundColor Green
Write-Host '       TaskMate Production Build Succeeded!              ' -ForegroundColor Green
Write-Host '==========================================================' -ForegroundColor Green
Write-Host "Frontend Assets : $DistDir"
Write-Host "Files Generated : $($DistFiles.Count)"
Write-Host "Total Size      : $TotalSizeKB KB"
Write-Host 'Backend Image   : Ready to containerize via Dockerfile'
Write-Host 'Production State: VERIFIED AND READY FOR DEPLOYMENT' -ForegroundColor Green
Write-Host ''
