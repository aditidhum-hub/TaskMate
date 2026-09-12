# TaskMate — AI-Powered Task Management Assistant

TaskMate is an intelligent task management system and agentic AI application designed as a **Modular Monolith**.

## Architecture Overview

- **Frontend (`frontend/`):** React 19, TypeScript, Vite, Tailwind CSS v4.
- **Backend (`backend/`):** Python 3.11+, FastAPI, Pydantic BaseSettings, Uvicorn.
- **Documentation (`docs/`):** Authoritative PRD, Architecture, Phases, and Progress.
- **Experimentation (`notebooks/`):** Google Colab validation suite.
- **Authentication & Database:** Firebase Authentication and Cloud Firestore (Phases 2 & 3).
- **Runtime Agent Model:** Nemotron via provider-agnostic `LLMService` (Phase 6–8).

## Repository Layout

```text
TaskMate/
├── frontend/             # React SPA client
├── backend/              # Python FastAPI backend
├── docs/                 # Authoritative documentation (PRD, Phases, Progress)
├── notebooks/            # Google Colab experimentation notebooks
├── firebase/             # Firebase configuration & rules
├── scripts/              # Dev launcher scripts (PowerShell & Bash)
├── tests/                # Workspace test suites
├── decisions.md          # Architectural Decision Records (ADRs)
├── rules.md              # Mandatory developer & agent rules
├── memory.md             # Persistent long-term project memory
├── changelog.md          # Chronological release log
├── README.md             # Project readme
└── .gitignore
```

## Running the Application

### 1. Backend (FastAPI)
```powershell
.\scripts\dev_backend.ps1
```
Available at: `http://localhost:8000` (Docs: `http://localhost:8000/docs`)

### 2. Frontend (React)
```powershell
.\scripts\dev_frontend.ps1
```
Available at: `http://localhost:5173`
