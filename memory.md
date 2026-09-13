# TaskMate — Long-Term Project Memory

This document serves as the permanent, authoritative project memory for **TaskMate**. It provides persistent context for AI coding assistants and developers across engineering sessions by recording the actual technical foundation, current repository state, approved architectural contracts, and the active phased implementation plan.

---

## 1. Project Overview

**TaskMate** is an AI-powered personal task management application. Its primary architectural purpose is to demonstrate a practical, reliable, and testable **Agentic AI workflow** using a clean modular design.

Instead of requiring users to manually fill out nested forms or navigate complex views to manage everyday items, TaskMate enables natural-language interactions:
- *"Create a task to study Python tomorrow."*
- *"Show my pending tasks."*
- *"What is today's date?"*
- *"I have 20 chapters and 5 days. How many chapters should I study each day?"*
- *"Delete my task 'Complete assignment'."*

### Core Agent Loop
The system executes a strictly bounded, single-agent tool-calling loop:
```text
User Request
    ↓
Natural-Language Understanding (Intent & Entity Parsing)
    ↓
Tool Selection Decision (Is a tool needed? Which approved tool?)
    ↓
Structured Argument Generation
    ↓
Execution of Approved Tool (Calculator / Date-Time / Task Tool)
    ↓
Observation of Real Tool Result
    ↓
Truthful Final Response Generation
    ↓
User Interface Update
```

---

## 2. Approved Technical Architecture (Version 1)

TaskMate Version 1 is explicitly designed as a **Modular Monolith**:

| Component | Technology | Role & Constraints |
| :--- | :--- | :--- |
| **Architecture Pattern** | Modular Monolith | Single backend service boundary; no distributed microservices, service meshes, or event brokers in V1. |
| **Frontend** | React (TypeScript, Vite, Tailwind CSS) | Responsive user interface providing Workspace, Kanban, Dashboard, Task filtering, and AI chat panel. |
| **Backend** | Python 3.11+ + FastAPI + Pydantic | Core API application (`backend/app/`), request validation, agent orchestration, and tool execution. |
| **Authentication** | Firebase Authentication | User registration, login, session tokens, and cryptographic Firebase ID token issuance. |
| **Database** | Cloud Firestore | Cloud NoSQL document storage scoped under `users/{user_id}/tasks/{task_id}`. |
| **Runtime Agent Model** | Nemotron | The approved runtime LLM for agent intent analysis, structured tool calling, and response synthesis. |
| **Model Configuration** | Configurable via Environment | Abstracted via `LLM_PROVIDER`, `LLM_MODEL`, and `LLM_API_KEY`. No hard-coded model dependencies. |
| **Development Tooling** | Google AI Studio | Scaffolding and UI code generation tool during early development; **NOT** the production runtime agent. |
| **Experimentation Layer**| Google Colab (`notebooks/`) | Cell-by-cell validation for setup, LLM calls, tools, and Firebase; **NOT** the production runtime. |

---

## 3. Approved Agent Tools (Version 1)

The runtime agent is restricted to three approved tools:

### 3.1 Calculator Tool
- **Purpose:** Perform safe arithmetic calculations to assist in budgeting, scheduling, and division of study/work goals.
- **Security Rule:** **Zero `eval()` Policy.** Never use unrestricted Python `eval()`, `exec()`, or JavaScript `Function()`.
- **Constraint:** Must parse or safely evaluate only explicitly supported arithmetic operators (`+`, `-`, `*`, `/`, `%`, `^`), parentheses, and safe functions (`sqrt`, `round`, `abs`, `ceil`, `floor`).

### 3.2 Date/Time Tool
- **Purpose:** Provide real-time calendar and clock awareness for temporal grounding.
- **Deterministic Resolution:** Natural language dates (*"today"*, *"tomorrow"*, *"yesterday"*, *"next Monday"*, *"in 5 days"*) must be resolved using deterministic system clock logic rather than trusting the LLM's internal clock knowledge.
- **Output:** Standardized ISO-8601 strings (`YYYY-MM-DD` or full timestamps) and human-readable dates.

### 3.3 Task Tool
- **Purpose:** Execute verified CRUD operations against Cloud Firestore.
- **Approved Operations:**
  1. `create_task(title, description?, due_date?, priority?)`
  2. `list_tasks(status?, priority?)`
  3. `get_task(task_id)`
  4. `update_task(task_id, ...)`
  5. `complete_task(task_id)`
  6. `delete_task(task_id)`
- **Context:** Every operation must be strictly scoped to the authenticated `user_id`.

---

## 4. Security, Identity & Authorization Model

### 4.1 Token Verification Pipeline
Authorization follows a strict, unidirectional validation chain:
```text
Client Login via Firebase Auth
        ↓
Frontend receives Firebase ID Token (JWT)
        ↓
HTTP Request with Authorization: Bearer <ID_Token>
        ↓
FastAPI Backend verifies token via Firebase Admin SDK
        ↓
Backend derives authenticated user_id = decoded_token["uid"]
        ↓
Tool/Service executes query strictly scoped to derived user_id
```

### 4.2 Security Rules & Boundaries
- **Never Trust Client-Supplied Identity:** The backend must **never** trust a `user_id` passed in the request body, path, or query string for authorization. Identity is derived solely from the cryptographically verified token.
- **Firestore Security Rules:** Direct client access (if configured) must enforce `request.auth != null && request.auth.uid == user_id`.
- **No Secret Leakage:** Client bundles must never contain backend API keys, service account JSON files, or administrative secrets.

### 4.3 Agent Operational Boundaries
The AI agent must:
- Select only approved tools (`Calculator`, `Date/Time`, `Task`).
- Validate structured arguments before invoking tools.
- Rely on real tool results and report errors truthfully.
- Respect the authenticated user context.

The AI agent must **never**:
- Fabricate or simulate tool results.
- Claim success after a tool execution failed.
- Execute arbitrary code, shell commands, or operating system subprocesses.
- Bypass authentication or authorization boundaries.
- Directly query or modify the database outside approved service functions.
- Expose raw internal chain-of-thought or prompt internals to users. User-facing status messages (*"Thinking..."*, *"Checking your tasks..."*, *"Creating your task..."*) are permitted.

---

## 5. Database Schema & Data Models

### 5.1 Preferred Firestore Structure
```text
users/{user_id}/tasks/{task_id}
```
Every task document is nested under the authenticated user's document path to guarantee natural isolation and clean security rules.

### 5.2 Core Task Fields (PRD Baseline)

| Field | Type | Description / Constraints |
| :--- | :--- | :--- |
| `id` | `string` | Unique task identifier (UUID or Firestore document ID). |
| `user_id` | `string` | ID of the task owner (matches Firebase Auth UID). |
| `title` | `string` | Required, non-empty title (max 200 characters). |
| `description` | `string` | Optional descriptive notes or instructions. |
| `due_date` | `string` | Optional ISO-8601 date string (e.g., `"2026-09-12"` or `"2026-09-12T00:00:00Z"`). |
| `priority` | `string` | Allowed values: `"low"`, `"medium"`, `"high"`. |
| `status` | `string` | Allowed values in V1 PRD: `"pending"`, `"completed"`. |
| `created_at` | `string` | ISO-8601 timestamp of document creation. |
| `updated_at` | `string` | ISO-8601 timestamp of last update. |

> [!NOTE]
> **Prototype / Extension Fields:** The current React frontend prototype includes additional UI fields: `category` (e.g., *"Work"*, *"Study"*) and `in_progress` status. These exist as exploratory UI enhancements and do not alter the core PRD requirements.

---

## 6. Approved Core API Endpoints

In accordance with `TaskMate_01_PRD.md` and `TaskMate_03_PHASES.md`, the core approved HTTP API endpoints exposed by the FastAPI backend are:

| Endpoint | Method | Purpose | Authorization |
| :--- | :--- | :--- | :--- |
| `/health` | `GET` | Service liveness probe and uptime status. | Public |
| `/api/chat` | `POST` | Primary agent conversational endpoint. Accepts user prompt, invokes agent loop with tools, returns truthful response. | Verified Firebase ID Token |

*Note: Internal business tools (Calculator, Date/Time, Task CRUD) are executed internally by the agent loop within the backend application. Direct REST endpoints for tools or task CRUD may be added only if explicitly defined in architecture reviews.*

---

## 7. Google Colab Validation Notebooks

The repository includes a dedicated notebook experimentation suite under `notebooks/`:

```text
notebooks/
├── 01_environment_setup.ipynb     # Verifies Python 3.11+, dependencies, and environment keys
├── 02_llm_connection.ipynb         # Tests direct connection and prompt response from Nemotron
├── 03_tool_calling.ipynb          # Tests structured function declaration and tool-calling schemas
├── 04_firebase_connection.ipynb   # Validates Firebase Admin credentials and Firestore read/writes
├── 05_agent_loop.ipynb            # Implements and verifies the step-by-step reasoning + tool execution loop
├── 06_api_testing.ipynb           # Validates FastAPI endpoints (/health, /api/chat) via test client
└── 07_end_to_end_validation.ipynb # Runs full user conversation scenarios against the live agent
```

**Operational Boundary:** Colab notebooks are strictly for learning, experimentation, and step-by-step validation. They are **NOT** the production runtime. All verified logic must reside inside `backend/app/`.

---

## 8. Current Implementation State

To ensure total transparency and avoid false assumptions, the codebase distinguishes between **Production Features**, **Frontend Prototype Features**, and **Pending Features**:

### 8.1 Completed Production Features ✅
- **Documentation & Specifications (Phase 0):** `TaskMate_01_PRD.md` (complete PRD) and `TaskMate_03_PHASES.md` (15-phase blueprint).
- **Persistent AI Context:** `decisions.md` (architectural decision log with historical superseded entries), `rules.md` (operational rules for coding and security), and `changelog.md` (chronological release log).
- **Project Environment and Skeleton (Phase 1):** Production Python 3.11+ backend initialized under `backend/app/` with FastAPI application shell, centralized configuration (`backend/app/core/config.py` using Pydantic `BaseSettings`), health check endpoint (`backend/app/api/routes_health.py`), development runner scripts (`scripts/dev_backend.ps1`, `scripts/dev_backend.sh`), Google Colab setup validation notebook (`notebooks/01_environment_setup.ipynb`), and automated pytest suite (`backend/tests/api/test_health.py`).
- **Firebase Setup and Authentication Foundation (Phase 2):** Official Firebase Web SDK (`firebase`) integrated into `frontend/` with client configuration (`frontend/src/services/firebase.ts`) and real auth methods in `frontend/src/services/authService.ts`. Firebase Admin SDK initialization in `backend/app/services/firebase.py`, cryptographically verified JWT token extraction via `backend/app/core/security.py` (zero synthetic token bypass), FastAPI `get_current_user` dependency in `backend/app/api/dependencies.py`, 10 automated auth pytest tests in `backend/tests/api/test_auth_dependency.py`, and Colab validation notebook `notebooks/04_firebase_connection.ipynb`.
- **Data Models and Task Service (Phase 3):** Python Pydantic models (`backend/app/models/task.py`: `TaskCreate`, `TaskUpdate`, `TaskResponse`, `TaskPriority`, `TaskStatus`) and Firestore task service (`backend/app/services/task_service.py`) executing full user-scoped CRUD against `users/{user_id}/tasks/{task_id}`. Security boundaries established via `firebase/firestore.rules` and `firebase/firestore.indexes.json`. 25 automated unit and tenant-isolation pytests passing in `backend/tests/unit/test_task_service.py` (38/38 total backend tests passing).
- **Calculator and Date/Time Tools (Phase 4):** Pure Python, LLM-independent utility tools. AST-based arithmetic evaluator with Zero `eval()` Policy (`backend/app/tools/calculator.py`) supporting `+`, `-`, `*`, `/`, `//`, `%`, `**`, `^`, parentheses, `sqrt`, `round`, `abs`, `ceil`, `floor`, with code injection defense. Deterministic relative/absolute temporal resolver (`backend/app/tools/datetime_tool.py`) parsing `"today"`, `"tomorrow"`, `"yesterday"`, `"next <weekday>"`, `"in N days/weeks/hours"`, and ISO dates. 35 automated unit tests in `backend/tests/unit/test_calculator.py` and `backend/tests/unit/test_datetime_tool.py` (73/73 total backend tests passing).
- **Task Tool (Phase 5):** Agent-facing tool wrapper (`backend/app/tools/task_tool.py`) connecting agent actions to `TaskService`. Injects authenticated caller `user_id` context into all 6 approved operations (`create_task`, `list_tasks`, `get_task`, `update_task`, `complete_task`, `delete_task`), dynamic dispatcher (`execute`), and returns structured JSON responses suitable for LLM reasoning. 17 unit and multi-tenant security pytests passing in `backend/tests/unit/test_task_tool.py` (90/90 total backend tests passing).
- **LLM Connection and Structured Tool Calling (Phase 6):** Provider-agnostic `LLMService` in `backend/app/services/llm_service.py` connecting to NVIDIA Nemotron via OpenAI-compatible Chat Completions endpoint. Structured tool schemas in `backend/app/agent/schemas.py`, dynamic dispatcher and argument validator in `backend/app/agent/tool_registry.py` enforcing strict tenant isolation (stripping LLM-supplied `user_id` and binding `TaskTool` to authenticated security context). Colab validation notebooks `notebooks/02_llm_connection.ipynb` and `notebooks/03_tool_calling.ipynb`. 20 automated unit/security pytests in `backend/tests/agent/test_agent_tools.py` (110/110 total backend tests passing).

### 8.2 Completed Frontend Prototype / Mock Features 🎨
*(Active in local repository, pending connection to production FastAPI backend)*
- **React 19 SPA Shell (`src/App.tsx`):** Header navigation with view routing (`workspace`, `dashboard`, `tasks`, `assistant`).
- **Workspace & Kanban Board:** Interactive 3-column task board (*Pending*, *In Progress*, *Completed*) with instant status toggles.
- **Dashboard View:** Productivity metrics tracking task counts, completion rates, and priority distribution.
- **Tasks Filter Panel:** Text search, category/status/priority filters, and multi-field sorting.
- **Local Service Mock Layer:**
  - `taskService.ts`: In-memory and browser `localStorage` CRUD mock with starter tasks.
  - `authService.ts`: Simulated authentication state and demo user session.
  - `aiService.ts`: Client-side conversational parser with status update callbacks (*"Thinking..."*, *"Checking your tasks..."*).
- **Client-side AST Math Evaluator (`src/utils/safeEvaluator.ts`):** Recursive descent arithmetic parser (zero `eval()`).
- **Client-side Date Resolver (`src/utils/safeEvaluator.ts`):** Deterministic temporal interpreter converting relative phrases to ISO dates.
- **Exploratory Dev Server (`server.ts`):** Prototype Express server running Vite in middleware mode. *(Marked as superseded; to be decommissioned upon FastAPI backend setup).*

### 8.3 Completed Frontend Features (Phase 9) ✅
- **React 19 SPA Architecture (`frontend/src/`):** Full user interface including Workspace, Kanban board, Productivity Dashboard, Tasks filtering panel, and AI Assistant panel.
- **Interactive Kanban Board (`src/components/tasks/KanbanBoard.tsx`):** 3-column workflow (*Pending*, *In Progress*, *Completed*) with column counts, color-coded badges, task action buttons to transition task states, empty states, and filter awareness.
- **Centralized State (`src/context/AppContext.tsx`):** Optimistic task mutation with automatic rollback on error, canonical derived productivity metrics, and `moveTaskStatus` handler.
- **Production API Connector (`src/services/apiClient.ts`):** Connects to FastAPI backend (`/api/chat`, `/api/health`) with automatic Firebase Bearer token attachment and error sanitization.
- **Canonical TypeScript Types (`src/types/index.ts`):** Typesafe data models matching FastAPI schemas (`ChatRequestPayload`, `ChatResponsePayload`, `Task`, `NavView`, `TaskFilters`, etc.).
- **Vite Dev Server Proxy:** Configured dev server proxy routing `/api` and `/health` requests directly to FastAPI backend (`http://127.0.0.1:8000`).

### 8.4 Completed Phase 10: Frontend + Backend Integration ✅
- **Checkpoint 10.1 (Backend E2E Integration Test Suite):** Comprehensive test suite in `backend/tests/integration/test_e2e_flow.py` covering canonical task scenarios (Creation, Querying, Calculation, Completion, Multi-turn context). 6/6 integration tests passed; 152/152 backend pytests passed.
- **Checkpoint 10.2 (Firestore Client SDK Integration):** Integrated Cloud Firestore client singleton in `frontend/src/services/firebase.ts` with user-scoped tasks (`users/{uid}/tasks/{taskId}`) in `frontend/src/services/taskService.ts` and resilient offline fallback.
- **Checkpoint 10.3 (Live Chat API & UI State Synchronization):** Connected conversational chat in `aiService.ts` to live `POST /api/chat` with Bearer auth; dynamic `applyAiToolEffects` in `AppContext.tsx` for real-time Kanban column transitions and Dashboard metrics recalculation; deduplication and duplicate Firestore write protection. 18/18 frontend tests passed.
- **Checkpoint 10.4 (Google Colab End-to-End Validation Notebook):** Authored `notebooks/07_end_to_end_validation.ipynb` verifying all 4 canonical scenarios and client-side state models with 7 passing executable code cells.
- **Checkpoint 10.5 (Full Regression Testing, Build Verification & Documentation):** 152/152 backend tests passing, 0 ruff errors, 18/18 frontend tests passing, 0 TypeScript errors, successful Vite production build.

### 8.5 Completed Phase 11: Testing and Error Handling ✅
- **Checkpoint 11.1 (Centralized Error Handling & Sanitization):** Implemented `backend/app/core/errors.py` with custom exception hierarchy (`TaskMateError`, `NotFoundError`, `UnauthorizedError`, `ValidationError`, `ServiceUnavailableError`) and global exception handlers mounted in `main.py`. Ensures 0 internal stack traces or secrets leak in 500 errors. 8/8 API error tests passing.
- **Checkpoint 11.2 (Tool & Agent Boundary Conditions):** Added 23 unit boundary tests (`test_error_boundaries.py`) covering Calculator (division by zero, syntax errors, overflow, disallowed lookups), Date/Time (unrecognized/invalid dates), and Task Tool (non-existent task operations). Added 6 agent tests (`test_agent_error_handling.py`) verifying timeout handling, provider 500s, and truthful failure reporting.
- **Checkpoint 11.3 (Frontend Defensive Error Handling & Rollback):** Added 7 frontend tests (`test_phase11_error_handling.mjs`) verifying optimistic creation/update/move/delete rollbacks, AI chat input unlocking, raw HTML 502 error sanitization, and offline network handling. 25/25 total frontend tests passing.
- **Checkpoint 11.4 (E2E Error Resilience Suite):** Implemented 6 full-stack integration tests in `test_error_resilience.py` verifying system behavior under LLM timeout, auth rejection, division by zero, non-existent task IDs, and unexpected agent crashes.
- **Checkpoint 11.5 (Full Regression & Build Verification):** 195/195 backend pytests passing, 0 ruff errors, 25/25 frontend tests passing, 0 TypeScript errors, clean Vite production build.

### 8.6 Completed Phase 12: Security and Tenant Isolation Review ✅
- **Checkpoint 12.1 (Security Audit & Hardening):** Verified Firestore security rules (`request.auth.uid == userId`), confirmed Zero eval() / exec() policy throughout codebase, verified secret hygiene with `.env*` git exclusion, verified client-supplied identity rejection, and confirmed CORS origin whitelist.
- **Checkpoint 12.2 (Automated Tenant Isolation Suite):** Implemented `backend/tests/integration/test_security_isolation.py` (9 tests passing) validating cross-user read/update/delete/list denial, parameter forgery defense (stripping LLM/client-supplied `user_id`), missing/forged token rejection (401), and unapproved CORS origin rejection.
- **Checkpoint 12.3 (Regression & Build Verification):** 204/204 backend tests passing, 0 ruff errors, 25/25 frontend tests passing, 0 TypeScript errors, clean Vite production build.

### 8.7 Completed Phase 13: Performance, Observability and Reliability ✅
- **Checkpoint 13.0 (Environment Configuration Audit):** Verified `.gitignore` excludes `.env*`, audited config settings and `.env.example`, added Phase 13 placeholders (`LOG_LEVEL`, `LOG_FORMAT`, `RATE_LIMIT_REQUESTS`, `RATE_LIMIT_WINDOW_SECONDS`), confirmed zero credential leakage.
- **Checkpoint 13.1 (Structured Diagnostic Logging):** Implemented `backend/app/core/logging.py` featuring `JsonLogFormatter` with automated credential redaction and `StructuredLoggingMiddleware` measuring latency in milliseconds, injecting `X-Request-ID`, and recording user context without capturing sensitive message bodies.
- **Checkpoint 13.2 (User & IP Rate Limiting Middleware):** Implemented `backend/app/api/middleware.py` featuring thread-safe sliding-window `RateLimiter` and `RateLimitingMiddleware` protecting `POST /api/chat`. Rejection on quota breach returns HTTP 429 Too Many Requests with JSON detail, dynamic `retry_after`, and `Retry-After` response header.
- **Checkpoint 13.3 (Automated Test Suite for Phase 13):** Created `backend/tests/api/test_rate_limiting.py` (4 tests) and `backend/tests/api/test_logging.py` (3 tests) covering quota enforcement, 429 status code, isolated per-user/IP quotas, unconstrained non-chat routes, JSON log formatting, credential redaction, and `X-Request-ID` header injection.
- **Checkpoint 13.4 (Regression & Build Verification):** 211/211 backend tests passing, 0 ruff errors, 25/25 frontend tests passing, 0 TypeScript errors, clean Vite production build.

### 8.8 Completed Phase 14: Production Readiness and Deployment ✅
- **Checkpoint 14.1 (Production Configuration Audit):** Audited `.gitignore`, `backend/app/core/config.py`, and environment templates. Hardened `.gitignore` to block all service accounts, private keys, and credential files (`*.pem`, `*.key`, `*service-account*.json`, `*adminsdk*.json`). Confirmed zero secrets committed.
- **Checkpoint 14.2 (Production Backend Configuration & Containerization):** Authored root `Dockerfile` and `backend/Dockerfile` with minimal `python:3.11-slim` image, non-root user execution (`appuser`), dynamic cloud port binding, and health check probes. Created root and backend `.dockerignore` files.
- **Checkpoint 14.3 (Production Build & Packaging Pipelines):** Created automated build and validation scripts `scripts/build_production.ps1` and `scripts/build_production.sh`. Successfully executed build script validating prerequisites, backend linting (0 errors), 211 backend tests, 25 frontend tests, TypeScript check, and compiling production frontend bundle into `frontend/dist/`.
- **Checkpoint 14.4 (Deployment Guide):** Created comprehensive provider-neutral production deployment guide `docs/DEPLOYMENT.md` covering architecture, environment variable reference, Docker operations, Google Cloud Run deployment, AWS deployment, self-hosted VPS, Firestore rules/index deployment, HTTPS, smoke tests, and rollback procedures.
- **Checkpoint 14.5 (Pre-Deployment Verification & Handover):** All 15 phases (Phase 0 through Phase 14) completed, tested, and verified. 211/211 backend tests passing, 25/25 frontend tests passing, 0 linter errors, production bundle compiled.

### 8.9 Version 1 Production Readiness Status 🚀
- **Status:** **PRODUCTION READY**
- **Architecture:** Modular Monolith (FastAPI + React 19 + Firebase Auth + Cloud Firestore + NVIDIA Nemotron agent).
- **Security:** Zero `eval()` / `exec()`, strict tenant isolation (`users/{uid}/tasks/{taskId}`), Bearer token verification, rate limiting, and credential auto-redaction.

---

## 9. Approved Phased Implementation Sequence

Development must strictly follow the sequence established in `TaskMate_03_PHASES.md`:

```text
Phase 0:  Documentation & Repository Preparation [COMPLETED]
    │
Phase 1:  Project Environment and Skeleton [COMPLETED]
    │
Phase 2:  Firebase Setup and Authentication Foundation [COMPLETED]
    │
Phase 3:  Data Models and Task Service [COMPLETED]
    │
Phase 4:  Calculator and Date/Time Tools [COMPLETED]
    │
Phase 5:  Task Tool [COMPLETED]
    │
Phase 6:  LLM Connection and Structured Tool Calling (Nemotron) [COMPLETED]
    │
Phase 7:  Agent Loop (Nemotron) [COMPLETED]
    │
Phase 8:  FastAPI API Layer (Nemotron-backed endpoint) [COMPLETED]
    │
Phase 9:  React Frontend [COMPLETED]
    │
Phase 10: Frontend + Backend Integration (React → FastAPI → Nemotron → Tools) [COMPLETED]
    │
Phase 11: Testing and Error Handling [COMPLETED]
    │
Phase 12: Security and Tenant Isolation Review [COMPLETED]
    │
Phase 13: Performance, Observability and Reliability [COMPLETED]
    │
Phase 14: Production Readiness and Deployment [COMPLETED]
```

---

## 10. Known Issues & Unresolved Technical Debt

1. **Backend Implementation Pending:** The production Python + FastAPI backend (`backend/app/`) has not yet been initialized. The current repository runs on an exploratory Node.js script (`server.ts`) which will be decommissioned during Phase 1–4.
2. **Mock Persistence Active:** The React UI currently saves task modifications to browser `localStorage`. Real-time Cloud Firestore synchronization (`users/{user_id}/tasks/{task_id}`) will replace this in Phase 3 and Phase 10.
3. **Simulated Authentication Active:** The frontend uses simulated authentication state (`authService.ts`). Live Firebase Authentication tokens and backend verification will be wired in Phase 2 and Phase 6.
4. **Nemotron Runtime Integration Pending:** The production agent loop backed by Nemotron has not yet been connected to the backend.
5. **Deployment Scripts Pending:** Production deployment manifests (e.g., Dockerfile, Cloud Run configuration) are deferred to Phase 14.

---

## 11. Long-Term Roadmap (Explicitly Deferred Post-V1)

The following advanced capabilities are recognized as valuable future roadmap items, but are **strictly out of scope for Version 1**:

- Multi-agent orchestration and specialized sub-agents.
- Retrieval-Augmented Generation (RAG) and vector databases.
- Multi-turn long-term conversational memory across weeks/months.
- Voice input / audio conversational assistant interface.
- External calendar integration (Google Calendar, Outlook).
- External messaging integrations (WhatsApp, Telegram, Slack).
- Email notifications and recurring cron triggers.
- Enterprise multi-tenant organization administration, RBAC, and subscription billing.
- Microservices splitting (only if independently scalable services become strictly necessary).
