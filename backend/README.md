# TaskMate — Backend Modular Monolith

This directory houses the production Python 3.11+ Modular Monolith backend for **TaskMate**, powered by **FastAPI** and **Pydantic**.

## Directory Structure

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py        # Centralized settings via Pydantic BaseSettings
│   └── api/
│       ├── __init__.py
│       └── routes_health.py # GET /health
├── tests/
│   ├── __init__.py
│   └── api/
│       ├── __init__.py
│       └── test_health.py   # Health endpoint pytest suite
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Testing & linting dependencies
├── .env.example             # Backend environment template
└── README.md
```

## Running the Backend

```powershell
# From workspace root using PowerShell:
.\scripts\dev_backend.ps1

# Or directly using the virtual environment:
$env:PYTHONPATH = "."
.\backend\.venv\Scripts\uvicorn.exe backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

## Running Tests

```powershell
$env:PYTHONPATH = "."
.\backend\.venv\Scripts\python.exe -m pytest backend/tests/ -v
```
