# TaskMate — Implementation Phases

**Document:** `03_PHASES.md`  
**Version:** 1.0 (Authoritative Roadmap)  
**Purpose:** Master implementation sequence for TaskMate  
**Primary Rule:** Implement and verify one phase at a time. Do not silently implement future phases.

---

# 1. Purpose of This Document

This document defines the exact, authoritative execution roadmap for **TaskMate**:

- The precise sequence of implementation phases (Phase 0 through Phase 14).
- The exact files and directory structures created in each phase.
- The approved technologies and runtime constraints.
- The role of Google Colab notebooks as an experimentation layer.
- The explicit milestones for integrating **Nemotron** as the runtime agent model.
- The test suites and acceptance criteria required before any phase is complete.
- The mandatory stop condition for each phase.

This roadmap operates in strict coordination with the project documentation hierarchy:

```text
TaskMate_01_PRD.md             (WHAT the product is)
      ↓
02_ARCHITECTURE.md             (HOW the product is structured)
      ↓
TaskMate_03_PHASES.md          (WHEN and IN WHAT ORDER it is built)
      ↓
rules.md                       (HOW AI and developers must behave)
      ↓
decisions.md                   (WHY decisions were taken and superseded)
      ↓
memory.md                      (Persistent long-term project memory)
      ↓
05_PROGRESS.md                 (Current execution progress tracker)
```

---

# 2. Implementation Philosophy

TaskMate is built as a clean, learning-friendly, production-style **Modular Monolith**.

The core system demonstrates the complete single-agent workflow:

```text
Natural-Language Request
          ↓
AI Agent (Intent Understanding & Entity Parsing)
          ↓
Reason / Tool Decision (Is a tool needed? Which approved tool?)
          ↓
Structured Argument Generation
          ↓
Tool Execution (Calculator / Date-Time / Task Tool)
          ↓
Firestore / Service Operation
          ↓
Observation of Real Tool Result
          ↓
Truthful Final Response + UI State Update
```

### Out-of-Scope for Version 1
To prevent architectural bloat and maintain focus on the core agent loop, the following are strictly deferred:
- Distributed microservices, service meshes, or message brokers.
- Kubernetes clusters and container orchestration meshes.
- Complex multi-agent communication frameworks.
- Retrieval-Augmented Generation (RAG) and vector databases.
- Model fine-tuning pipelines.
- Voice assistants and speech-to-text pipelines.
- External calendar or email integrations.
- Enterprise multi-tenant billing, organization administration, and complex RBAC.

---

# 3. Authoritative Repository Structure

The project converges toward this standardized repository layout:

```text
TaskMate/
│
├── docs/                             # Authoritative project documentation
│   ├── 01_PRD.md
│   ├── 02_ARCHITECTURE.md
│   ├── 03_PHASES.md
│   ├── 04_AGENT_DEVELOPMENT_RULES.md
│   └── 05_PROGRESS.md
│
├── decisions.md                      # Architectural Decision Records (ADRs)
├── rules.md                          # Permanent coding & agent rules
├── memory.md                         # Long-term project memory
├── changelog.md                      # Chronological release log
│
├── backend/                          # Production Python + FastAPI Modular Monolith
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI application entry point
│   │   │
│   │   ├── api/                      # HTTP routing and dependencies
│   │   │   ├── __init__.py
│   │   │   ├── routes_health.py      # GET /health
│   │   │   ├── routes_chat.py        # POST /api/chat
│   │   │   └── dependencies.py       # Firebase ID token verification
│   │   │
│   │   ├── agent/                    # Agent orchestration
│   │   │   ├── __init__.py
│   │   │   ├── agent.py              # Core reasoning loop
│   │   │   ├── prompts.py            # System instructions and prompt templates
│   │   │   ├── schemas.py            # Pydantic schemas for agent interactions
│   │   │   └── tool_registry.py      # Whitelist of approved tools and schemas
│   │   │
│   │   ├── tools/                    # Approved callable tools
│   │   │   ├── __init__.py
│   │   │   ├── calculator.py         # Safe AST arithmetic evaluator
│   │   │   ├── datetime_tool.py      # Deterministic system clock date resolver
│   │   │   └── task_tool.py          # CRUD wrapper for Firestore TaskService
│   │   │
│   │   ├── services/                 # External service integrations
│   │   │   ├── __init__.py
│   │   │   ├── firebase.py           # Firebase Admin SDK initialization
│   │   │   ├── task_service.py       # Firestore task operations
│   │   │   └── llm_service.py        # Provider-agnostic LLM client (Nemotron)
│   │   │
│   │   ├── models/                   # Pydantic domain models
│   │   │   ├── __init__.py
│   │   │   ├── task.py               # Task domain model
│   │   │   ├── chat.py               # Chat request and response schemas
│   │   │   └── user.py               # User session model
│   │   │
│   │   ├── core/                     # Cross-cutting concerns
│   │   │   ├── __init__.py
│   │   │   ├── config.py             # Environment configuration (BaseSettings)
│   │   │   ├── security.py           # Token verification helpers
│   │   │   └── logging.py            # Structured logging configuration
│   │   │
│   │   └── utils/                    # Shared Python utilities
│   │       ├── __init__.py
│   │       └── dates.py              # Date formatting helpers
│   │
│   ├── tests/                        # Comprehensive backend test suite
│   │   ├── unit/                     # Unit tests for tools and services
│   │   │   ├── test_calculator.py
│   │   │   ├── test_datetime_tool.py
│   │   │   ├── test_task_service.py
│   │   │   └── test_validation.py
│   │   ├── agent/                    # Agent intent and tool selection tests
│   │   │   ├── test_agent_intents.py
│   │   │   └── test_agent_tools.py
│   │   ├── api/                      # FastAPI endpoint tests
│   │   │   ├── test_health.py
│   │   │   └── test_chat.py
│   │   └── integration/              # End-to-end backend workflows
│   │       └── test_task_flow.py
│   │
│   ├── requirements.txt              # Production dependencies
│   ├── requirements-dev.txt          # Testing and linting dependencies
│   └── .env.example                  # Backend environment template
│
├── frontend/                         # React SPA (TypeScript + Vite + Tailwind CSS)
│   ├── src/
│   │   ├── components/               # React components (Workspace, Kanban, Dashboard, Chat)
│   │   ├── pages/                    # Page wrappers
│   │   ├── services/                 # API client services (calling backend)
│   │   ├── hooks/                    # Custom React hooks
│   │   ├── context/                  # Centralized state (AppContext)
│   │   ├── types/                    # Shared TypeScript domain types
│   │   ├── utils/                    # Frontend helpers and formatters
│   │   ├── App.tsx                   # Main application entry component
│   │   └── main.tsx                  # React DOM mount point
│   ├── public/                       # Static public assets
│   ├── package.json                  # Node dependencies and scripts
│   ├── vite.config.ts                # Vite build configuration
│   └── .env.example                  # Frontend public configuration template
│
├── notebooks/                        # Google Colab Validation Suite (Experimentation only)
│   ├── 01_environment_setup.ipynb
│   ├── 02_llm_connection.ipynb
│   ├── 03_tool_calling.ipynb
│   ├── 04_firebase_connection.ipynb
│   ├── 05_agent_loop.ipynb
│   ├── 06_api_testing.ipynb
│   └── 07_end_to_end_validation.ipynb
│
├── firebase/                         # Firebase Security & Indexes
│   ├── firestore.rules               # Firestore document security rules
│   └── firestore.indexes.json        # Firestore query index configurations
│
├── scripts/                          # Development runner scripts
│   ├── dev_backend.ps1               # Windows PowerShell backend launcher
│   ├── dev_frontend.ps1              # Windows PowerShell frontend launcher
│   ├── dev_backend.sh                # Linux/macOS backend launcher
│   └── dev_frontend.sh               # Linux/macOS frontend launcher
│
├── .gitignore
├── README.md
└── LICENSE
```

---

# 4. AI Model Strategy & Provider Abstraction

## 4.1 Runtime Model Policy
**Nemotron** is designated as the initial runtime LLM for TaskMate's tool-calling and agent-loop phases (Phases 6–8, 10).

- **Google AI Studio** was utilized as an early development and UI generation tool; it is **NOT** the TaskMate runtime agent.
- **Provider Abstraction:** The backend must never hard-code Nemotron or any specific vendor SDK into core agent logic.
- All model interactions are mediated through an abstract `LLMService` governed by environment variables:
  ```env
  LLM_PROVIDER=nemotron
  LLM_MODEL=nvidia/nemotron-4-340b-instruct
  LLM_API_KEY=your_api_key_here
  ```
- This abstraction allows seamless switching to local models (e.g., vLLM / Ollama) or alternative cloud endpoints without modifying agent prompts, tool definitions, or business logic.

---

# 5. Google Colab / Notebook Strategy

The `notebooks/` directory contains an isolated validation suite:

```text
notebooks/
├── 01_environment_setup.ipynb     # Verifies Python 3.11+, dependencies, and environment keys
├── 02_llm_connection.ipynb         # Tests direct connection and basic response from Nemotron
├── 03_tool_calling.ipynb          # Tests structured tool-calling schemas with Nemotron
├── 04_firebase_connection.ipynb   # Validates Firebase Admin credentials and Firestore read/writes
├── 05_agent_loop.ipynb            # Exercises the complete Nemotron reasoning + tool loop
├── 06_api_testing.ipynb           # Validates FastAPI endpoints (/health, /api/chat) via TestClient
└── 07_end_to_end_validation.ipynb # Runs conversational end-to-end scenarios against the live agent
```

### Notebook Operational Rules
- Notebooks are strictly for **learning, prototyping, prompt experimentation, and step-by-step validation**.
- Notebooks are **NOT** the production runtime or server host.
- Never commit credentials, private keys, or service-account JSON files inside notebooks.
- All verified code must be migrated to `backend/app/`.

---

# 6. Master Phase Overview

| Phase | Title | Core Objective |
| :---: | :--- | :--- |
| **0** | **Documentation & Repository Preparation** | Align PRD, Architecture, Phases, ADRs, Rules, and Memory. |
| **1** | **Project Environment and Skeleton** | Initialize Python 3.11+ backend, FastAPI shell, and scripts. |
| **2** | **Firebase Setup and Authentication Foundation** | Configure Firebase project, client Auth, and backend token verification. |
| **3** | **Data Models and Task Service** | Implement Pydantic task schemas, Firestore persistence, and user-scoped CRUD. |
| **4** | **Calculator and Date/Time Tools** | Implement safe AST math evaluator and deterministic date resolver. |
| **5** | **Task Tool** | Build the agent Task Tool wrapping Firestore operations. |
| **6** | **LLM Connection & Structured Tool Calling** | Connect **Nemotron** and verify structured function calling schemas. |
| **7** | **Agent Loop** | Build the complete **Nemotron** reasoning loop with tool execution. |
| **8** | **FastAPI API Layer** | Expose `GET /health` and `POST /api/chat` backed by the Nemotron agent. |
| **9** | **React Frontend** | Align the React SPA (Workspace, Kanban, Dashboard, Chat) with backend contracts. |
| **10** | **Frontend + Backend Integration** | Wire React frontend to FastAPI `/api/chat` with live Firebase tokens. |
| **11** | **Testing and Error Handling** | Execute full `pytest` suite, frontend tests, and error sanitization. |
| **12** | **Security and Tenant Isolation Review** | Audit user-scoped data boundaries (`users/{user_id}/tasks/{task_id}`). |
| **13** | **Performance, Observability and Reliability** | Implement structured logging, rate limiting on `/api/chat`, and metrics. |
| **14** | **Production Readiness and Deployment** | Verify HTTPS, environment hygiene, CORS, and deployment manifests. |

---

# PHASE 0 — Documentation & Repository Preparation

## Objective
Establish complete, non-contradictory architectural documentation and persistent AI context files before writing code.

## Requirements
- Review `TaskMate_01_PRD.md` and ensure alignment with `02_ARCHITECTURE.md`.
- Establish `decisions.md` documenting Architectural Decision Records (ADR-001 through ADR-019).
- Establish `rules.md` detailing operational, coding, and security invariants.
- Establish `memory.md` capturing technical stack contracts, API schemas, and feature inventories.
- Establish `changelog.md` maintaining standard SemVer release history.

## Files
- `TaskMate_01_PRD.md`
- `TaskMate_03_PHASES.md`
- `decisions.md`
- `rules.md`
- `memory.md`
- `changelog.md`

## Implementation Work
1. Reconcile all documents to establish the **Modular Monolith** pattern.
2. Formally designate **Python + FastAPI** as backend and **Nemotron** as runtime agent.
3. Explicitly designate Google AI Studio as a development/prototyping tool.
4. Mark historical prototype decisions (Node/Express host, direct Gemini SDK) as superseded.

## Tests & Verification
- Verify that PRD, Architecture, Phases, ADRs, and Rules do not conflict.
- Verify folder structure matches the approved modular monolith layout.

## Acceptance Criteria
- All 4 persistent AI context files (`decisions.md`, `rules.md`, `memory.md`, `changelog.md`) exist, are mutually consistent, and contain zero unsupported benchmark claims.

## Stop Condition
**STOP.** Update progress tracking before proceeding.

---

# PHASE 1 — Project Environment and Skeleton

## Objective
Initialize the production Python 3.11+ backend environment, FastAPI application shell, and development runner scripts.

## Requirements
- Python 3.11+ virtual environment setup.
- Basic FastAPI skeleton exposing a functional health probe.
- Clean development runner scripts for PowerShell and Bash.

## Files to Create / Modify
- `backend/app/__init__.py`
- `backend/app/main.py`
- `backend/app/core/config.py`
- `backend/app/api/routes_health.py`
- `backend/requirements.txt`
- `backend/requirements-dev.txt`
- `backend/.env.example`
- `scripts/dev_backend.ps1`
- `scripts/dev_backend.sh`
- `notebooks/01_environment_setup.ipynb`

## Implementation Work
1. Configure `backend/requirements.txt` (`fastapi`, `uvicorn[standard]`, `pydantic`, `pydantic-settings`, `httpx`).
2. Implement `backend/app/core/config.py` loading environment settings via Pydantic `BaseSettings`.
3. Implement `backend/app/api/routes_health.py` with `GET /health` returning service status and timestamp.
4. Mount health routes in `backend/app/main.py`.
5. Author `notebooks/01_environment_setup.ipynb` to verify Python version and environment dependencies.

## Tests
- Run `01_environment_setup.ipynb` to confirm environment variables and imports.
- Launch FastAPI locally and run test:
  ```bash
  pytest backend/tests/api/test_health.py
  ```

## Acceptance Criteria
- `GET /health` returns `{"status": "ok", "service": "TaskMate Backend"}` with HTTP 200.
- No frontend or agent dependencies introduced into the backend skeleton.

## Stop Condition
**STOP.** Verify acceptance criteria, update progress, and stop.

---

# PHASE 2 — Firebase Setup and Authentication Foundation

## Objective
Establish the Firebase project configuration, client authentication foundation, and backend JWT verification dependency.

> [!IMPORTANT]
> **Phase Boundary:** Phase 2 establishes authentication only. Do NOT build task persistence or task CRUD in this phase.

## Requirements
- Firebase project initialization with Authentication enabled (Email/Password & Google OAuth).
- Backend dependency to verify Firebase ID tokens via the Firebase Admin SDK.
- Extraction of authenticated `user_id` context (`decoded_token["uid"]`).

## Files to Create / Modify
- `backend/app/services/firebase.py`
- `backend/app/core/security.py`
- `backend/app/api/dependencies.py`
- `backend/tests/api/test_auth_dependency.py`
- `frontend/src/services/authService.ts`
- `notebooks/04_firebase_connection.ipynb`

## Implementation Work
1. Initialize Firebase Admin SDK in `backend/app/services/firebase.py`.
2. Implement `verify_firebase_token()` in `backend/app/core/security.py` verifying JWT signatures.
3. Implement FastAPI dependency `get_current_user()` in `backend/app/api/dependencies.py` extracting Bearer tokens.
4. Implement client authentication foundation in `frontend/src/services/authService.ts`.
5. Author `notebooks/04_firebase_connection.ipynb` to test token validation against the Admin SDK.

## Tests
- Test with valid mock/test token $\rightarrow$ returns authenticated `user_id`.
- Test with expired or malformed token $\rightarrow$ raises HTTP 401 Unauthorized.
- Test with missing `Authorization` header $\rightarrow$ raises HTTP 401 Unauthorized.

## Acceptance Criteria
- Protected routes can depend on `get_current_user` to obtain the verified `user_id`.
- Zero client-supplied user IDs trusted for authorization.

## Stop Condition
**STOP.** Verify token verification, update progress, and stop.

---

# PHASE 3 — Data Models and Task Service

## Objective
Implement Pydantic domain models, Firestore database integration, and the user-scoped `TaskService`.

## Requirements
- Define core Task schema with strict validation.
- Store tasks under user-scoped Firestore path: `users/{user_id}/tasks/{task_id}`.
- Implement isolated CRUD operations in `TaskService`.

## Task Schema Definition
Core fields defined by PRD:
- `id`: string (UUID or Firestore document ID)
- `user_id`: string (owner UID)
- `title`: string (1–200 characters, required)
- `description`: string (optional)
- `due_date`: string (ISO-8601 string, optional)
- `priority`: string (`"low"`, `"medium"`, `"high"`)
- `status`: string (`"pending"`, `"completed"`)
- `created_at`: string (ISO-8601 timestamp)
- `updated_at`: string (ISO-8601 timestamp)

## Files to Create / Modify
- `backend/app/models/task.py`
- `backend/app/services/task_service.py`
- `backend/tests/unit/test_task_service.py`
- `firebase/firestore.rules`
- `firebase/firestore.indexes.json`

## Implementation Work
1. Define Pydantic models: `TaskCreate`, `TaskUpdate`, `TaskResponse` in `backend/app/models/task.py`.
2. Implement `TaskService` in `backend/app/services/task_service.py`:
   - `create_task(user_id, task_data)`
   - `list_tasks(user_id, status=None, priority=None)`
   - `get_task(user_id, task_id)`
   - `update_task(user_id, task_id, update_data)`
   - `complete_task(user_id, task_id)`
   - `delete_task(user_id, task_id)`
3. Author baseline `firebase/firestore.rules` enforcing `request.auth.uid == userId`.

## Tests
- Unit tests verifying task creation, listing, updating, and deletion with valid `user_id`.
- Security test verifying that user A cannot retrieve or update user B's task.

## Acceptance Criteria
- Full task lifecycle operates reliably against Firestore (or Firestore emulator).
- All task operations require and enforce the authenticated `user_id`.

## Stop Condition
**STOP.** Verify CRUD operations, update progress, and stop.

---

# PHASE 4 — Calculator and Date/Time Tools

## Objective
Implement safe, deterministic utility tools for arithmetic evaluation and temporal grounding.

## Requirements
- Safe arithmetic calculation with **Zero `eval()` Policy**.
- Deterministic relative/absolute date parsing using real-time system clock logic.
- Pure Python implementations independent of the LLM.

## Files to Create / Modify
- `backend/app/tools/calculator.py`
- `backend/app/tools/datetime_tool.py`
- `backend/tests/unit/test_calculator.py`
- `backend/tests/unit/test_datetime_tool.py`

## Implementation Work
1. Implement `calculate(expression: str) -> float` in `backend/app/tools/calculator.py`:
   - Use Python's `ast` module to safely parse expressions into a binary operator tree.
   - Support `+`, `-`, `*`, `/`, `%`, `^`, parentheses, `sqrt`, `round`, `abs`, `ceil`, `floor`.
   - Explicitly disallow variable lookups, statements, imports, and function definitions.
   - Handle division by zero and invalid syntax gracefully with descriptive errors.
2. Implement `resolve_date_time(query: str) -> dict` in `backend/app/tools/datetime_tool.py`:
   - Parse `"today"`, `"tomorrow"`, `"yesterday"`, `"next monday"`, `"in N days"`.
   - Return normalized ISO-8601 string (`YYYY-MM-DD` or full ISO) and human-readable label.

## Tests
- Calculator: `20 + 5`, `20 / 5`, `(10 + 5) * 2`, division by zero, code injection attempts (`__import__`).
- Date/Time: `"today"`, `"tomorrow"`, `"in 3 days"`, and standard date formatting.

## Acceptance Criteria
- Calculator evaluates math with zero code injection risk.
- Date/time tool resolves relative offsets accurately based on system time.

## Stop Condition
**STOP.** Verify tool tests, update progress, and stop.

---

# PHASE 5 — Task Tool

## Objective
Implement the agent-facing **Task Tool** connecting agent actions to `TaskService`.

## Requirements
- Provide a unified, validated tool interface for task operations.
- Enforce that the authenticated user context is injected into every operation.
- Return structured tool outputs suitable for LLM reasoning.

## Files to Create / Modify
- `backend/app/tools/task_tool.py`
- `backend/tests/unit/test_task_tool.py`

## Implementation Work
1. Implement `TaskTool` wrapper in `backend/app/tools/task_tool.py` supporting:
   - `create_task(title, description, due_date, priority)`
   - `list_tasks(status, priority)`
   - `get_task(task_id)`
   - `update_task(task_id, ...)`
   - `complete_task(task_id)`
   - `delete_task(task_id)`
2. Ensure `user_id` is supplied from the active security context, never inferred from user prompt text.
3. Return serialized dictionaries with clear operation statuses (`{"success": True, "task": {...}}`).

## Tests
- Test task creation via tool call.
- Test task query filtering by status (`pending`, `completed`).
- Test error handling when attempting to retrieve a non-existent `task_id`.

## Acceptance Criteria
- All 6 task operations execute cleanly through the tool boundary.
- Tool returns unambiguous success and failure dictionaries.

## Stop Condition
**STOP.** Verify tool operations, update progress, and stop.

---

# PHASE 6 — LLM Connection and Structured Tool Calling

## Objective
Establish the LLM service connection using **Nemotron** as the initial runtime model, and verify structured tool-calling schemas.

## Requirements
- Configure LLM service via `LLM_PROVIDER`, `LLM_MODEL`, and `LLM_API_KEY`.
- Define JSON function schemas for `Calculator Tool`, `Date/Time Tool`, and `Task Tool`.
- Verify that **Nemotron** generates valid tool selection and structured arguments.

## Files to Create / Modify
- `backend/app/services/llm_service.py`
- `backend/app/agent/schemas.py`
- `backend/app/agent/tool_registry.py`
- `backend/tests/agent/test_agent_tools.py`
- `notebooks/02_llm_connection.ipynb`
- `notebooks/03_tool_calling.ipynb`

## Implementation Work
1. Implement `LLMService` in `backend/app/services/llm_service.py` connecting to Nemotron via an OpenAI-compatible / NVIDIA client.
2. Register tool declarations in `backend/app/agent/tool_registry.py`:
   - `calculate(expression)`
   - `get_date_time(query)`
   - `task_operation(action, ...)`
3. Validate structured output generation in `notebooks/02_llm_connection.ipynb` and `03_tool_calling.ipynb`.

## Tests
- Test prompt: `"What is 450 * 3?"` $\rightarrow$ LLM calls `calculate` with `{"expression": "450 * 3"}`.
- Test prompt: `"What is tomorrow's date?"` $\rightarrow$ LLM calls `get_date_time` with `{"query": "tomorrow"}`.
- Test prompt: `"Create a task to study Python"` $\rightarrow$ LLM calls `task_operation` with action `"create_task"`.
- Test conversational prompt: `"Hello, who are you?"` $\rightarrow$ LLM responds directly without tool calls.

## Acceptance Criteria
- Nemotron reliably selects the correct tool and outputs valid JSON arguments.
- Service fails gracefully if `LLM_API_KEY` is missing or invalid.

## Stop Condition
**STOP.** Verify tool-calling schemas, update progress, and stop.

---

# PHASE 7 — Agent Loop

## Objective
Construct the complete **Nemotron-backed Agent Loop** orchestrating intent analysis, tool execution, observation, and response synthesis.

## Requirements
- Build the iterative agent loop: prompt $\rightarrow$ model $\rightarrow$ tool call $\rightarrow$ tool result $\rightarrow$ final synthesis.
- Enforce agent safety invariants (no arbitrary code execution, no tool result fabrication).
- Conceal raw chain-of-thought from end users while retaining structured developer traces.

## Agent Loop Architecture
```text
User Message + Authenticated User Context
                ↓
Agent Prompt Assembly (System Instructions + Approved Tool Schemas)
                ↓
Invoke Nemotron
                ↓
Tool Call Requested?
    ├── NO  → Return synthesized conversational response
    │
    └── YES → 
           Validate structured tool arguments
                ↓
           Execute approved tool (Calculator / Date-Time / Task Tool)
                ↓
           Append real tool result to model message history
                ↓
           Re-invoke Nemotron to synthesize final answer
                ↓
           Return truthful final response
```

## Files to Create / Modify
- `backend/app/agent/agent.py`
- `backend/app/agent/prompts.py`
- `backend/tests/agent/test_agent_loop.py`
- `notebooks/05_agent_loop.ipynb`

## Implementation Work
1. Implement `TaskMateAgent` in `backend/app/agent/agent.py`.
2. Define system instructions in `backend/app/agent/prompts.py` instructing Nemotron to:
   - Always use tools for arithmetic and dates.
   - Rely strictly on tool output.
   - Never claim success if a tool returns an error.
3. Validate end-to-end loop in `notebooks/05_agent_loop.ipynb`.

## Tests
- Test arithmetic intent: `"I have 15 lessons and 3 days. How many per day?"` $\rightarrow$ calls `calculate`, responds with 5.
- Test date + task creation: `"Create a task to study math tomorrow"` $\rightarrow$ resolves date, creates task, confirms title and date.
- Test error handling: tool execution error $\rightarrow$ agent truthfully explains error to user.

## Acceptance Criteria
- Agent executes multi-step tool calls reliably and synthesizes clean, friendly responses without leaking prompt internals or raw tool traces.

## Stop Condition
**STOP.** Verify agent loop, update progress, and stop.

---

# PHASE 8 — FastAPI API Layer

## Objective
Expose the Nemotron-backed agent and system health checks through production FastAPI endpoints.

## Requirements
- Expose `GET /health` (public) and `POST /api/chat` (protected).
- Enforce Firebase ID token verification dependency on `/api/chat`.
- Implement Pydantic request/response schemas, CORS middleware, and global exception handlers.

## API Specification

### 1. `GET /health`
- **Purpose:** Service uptime and health probe.
- **Auth:** Public.
- **Response:** `{"status": "ok", "service": "TaskMate Backend", "timestamp": "..."}`

### 2. `POST /api/chat`
- **Purpose:** Primary conversational interaction endpoint.
- **Auth:** `Authorization: Bearer <Firebase_ID_Token>`.
- **Request Body:**
  ```json
  {
    "message": "Create a task to finish lab report tomorrow"
  }
  ```
- **Response Body:**
  ```json
  {
    "response": "I've created the task 'finish lab report' due tomorrow (2026-09-12).",
    "tool_used": "task_tool",
    "created_task": {
      "id": "task-uuid-123",
      "title": "finish lab report",
      "due_date": "2026-09-12",
      "priority": "medium",
      "status": "pending"
    }
  }
  ```

## Files to Create / Modify
- `backend/app/api/routes_chat.py`
- `backend/app/models/chat.py`
- `backend/app/main.py`
- `backend/tests/api/test_chat.py`
- `notebooks/06_api_testing.ipynb`

## Implementation Work
1. Implement Pydantic schemas in `backend/app/models/chat.py` (`ChatRequest`, `ChatResponse`).
2. Implement route handler in `backend/app/api/routes_chat.py` injecting `get_current_user`.
3. Add CORS middleware in `backend/app/main.py` allowing configured frontend origins.
4. Validate routes in `notebooks/06_api_testing.ipynb` using FastAPI `TestClient`.

## Tests
- Test `/health` returns HTTP 200.
- Test `/api/chat` with valid token returns HTTP 200 and expected response structure.
- Test `/api/chat` without token returns HTTP 401.
- Test `/api/chat` with empty message returns HTTP 422.

## Acceptance Criteria
- Protected chat endpoint successfully bridges incoming HTTP requests to the Nemotron agent loop.

## Stop Condition
**STOP.** Verify API endpoints, update progress, and stop.

---

# PHASE 9 — React Frontend

## Objective
Build and align the React SPA components with production API contracts and design standards.

## Requirements
- Full user interface: Workspace, Kanban board, Dashboard analytics, Tasks filtering panel, and AI Assistant chat panel.
- Client authentication state management (Sign-in, Sign-up, Sign-out modals).
- Clean separation of UI components, centralized state (`AppContext`), and API services.

## Files to Create / Modify
- `frontend/src/App.tsx`
- `frontend/src/components/layout/Header.tsx`
- `frontend/src/components/workspace/WorkspaceView.tsx`
- `frontend/src/components/tasks/KanbanBoard.tsx`
- `frontend/src/components/tasks/TaskPanel.tsx`
- `frontend/src/components/dashboard/DashboardView.tsx`
- `frontend/src/components/chat/AiAssistantPanel.tsx`
- `frontend/src/components/modals/TaskModal.tsx`
- `frontend/src/components/modals/AuthModal.tsx`
- `frontend/src/context/AppContext.tsx`
- `frontend/src/services/apiClient.ts`
- `frontend/src/types/index.ts`

## Implementation Work
1. Implement centralized state management in `AppContext.tsx` handling tasks, active filters, and notifications.
2. Implement `AiAssistantPanel.tsx` displaying user messages, friendly agent status indicators (*"Thinking..."*, *"Checking your tasks..."*), and quick action chips.
3. Implement `KanbanBoard.tsx` with columns for *Pending*, *In Progress*, and *Completed*.
4. Implement `DashboardView.tsx` computing derived metrics from canonical task state.
5. Author client service connector in `frontend/src/services/apiClient.ts`.

## Tests
- Frontend component rendering and interaction tests.
- Verify that UI updates optimistically and rolls back cleanly upon service error.

## Acceptance Criteria
- User can navigate views, open modals, toggle task states, and input chat messages without visual glitches or unhandled console errors.

## Stop Condition
**STOP.** Verify frontend components, update progress, and stop.

---

# PHASE 10 — Frontend + Backend Integration

## Objective
Connect the React SPA frontend directly to the production FastAPI backend and verify live end-to-end task workflows.

## End-to-End Integration Flow
```text
React User Action (Chat prompt or UI button)
                 ↓
Frontend transmits Firebase ID Token + Prompt
                 ↓
FastAPI Backend (POST /api/chat)
                 ↓
Token Verification (Firebase Admin SDK derives user_id)
                 ↓
Nemotron Agent Loop (Intent analysis + Tool selection)
                 ↓
Tools Execution (Calculator / Date-Time / Task Tool)
                 ↓
Cloud Firestore (Scoped to users/{user_id}/tasks/{task_id})
                 ↓
Truthful Synthesized Response returned to Client
                 ↓
React UI dynamically updates Kanban, Dashboard, and Chat
```

## Files to Create / Modify
- `frontend/src/services/aiService.ts`
- `frontend/src/services/taskService.ts`
- `backend/tests/integration/test_e2e_flow.py`
- `notebooks/07_end_to_end_validation.ipynb`

## Implementation Work
1. Wire `frontend/src/services/aiService.ts` to execute `POST /api/chat` against the live FastAPI backend with `Authorization: Bearer <token>`.
2. Connect task creation responses directly into `AppContext` to ensure instant UI synchronization.
3. Validate complete conversational flows in `notebooks/07_end_to_end_validation.ipynb`.

## Verification Scenarios
1. **Creation Scenario:** `"Create a high priority task to study Python tomorrow."`
   - Agent resolves date, invokes `create_task`, updates Firestore.
   - React UI immediately displays new card in the *Pending* column.
2. **Query Scenario:** `"Show my pending tasks."`
   - Agent invokes `list_tasks(status="pending")`, summarizes results accurately.
3. **Calculation Scenario:** `"I have 30 chapters and 6 days. How many per day?"`
   - Agent invokes `calculate("30 / 6")`, returns 5.
4. **Completion Scenario:** `"Mark task 'study Python' as completed."`
   - Agent updates status to completed; Dashboard metrics reflect updated completion rate.

## Acceptance Criteria
- All 4 conversational scenarios execute end-to-end with real database persistence and truthful conversational feedback.

## Stop Condition
**STOP.** Verify end-to-end workflows, update progress, and stop.

---

# PHASE 11 — Testing and Error Handling

## Objective
Execute comprehensive automated test suites across backend and frontend, and verify defensive error handling.

## Requirements
- Full backend `pytest` coverage across unit, agent, API, and integration directories.
- Comprehensive error handling masking internal server traces and database errors.
- Verification that the agent reports failures truthfully without hallucinating success.

## Files to Create / Modify
- `backend/tests/unit/*`
- `backend/tests/agent/*`
- `backend/tests/api/*`
- `backend/tests/integration/*`
- `backend/app/core/errors.py`

## Implementation Work
1. Implement global exception handlers in `backend/app/core/errors.py` sanitizing 500 errors into customer-safe messages.
2. Add unit tests for boundary conditions:
   - Malformed arithmetic expressions in Calculator Tool.
   - Unrecognized date strings in Date/Time Tool.
   - Non-existent task IDs in Task Tool.
   - Missing or expired Firebase ID tokens.
   - Network timeouts when communicating with Nemotron.
3. Verify that failed operations prompt the React frontend to roll back optimistic updates and render toast alerts.

## Tests
- Run all backend tests:
  ```bash
  pytest backend/tests/ -v --cov=backend/app
  ```

## Acceptance Criteria
- All automated tests pass with zero critical warnings.
- Server stack traces, private prompt internals, and database paths are never leaked to clients.

## Stop Condition
**STOP.** Verify test results, update progress, and stop.

---

# PHASE 12 — Security and Tenant Isolation Review

## Objective
Conduct a comprehensive security and user isolation audit before production staging.

## V1 User Isolation Principle
```text
Authenticated User Context (Firebase UID)
                 ↓
Backend Server-Derived Identity (decoded_token["uid"])
                 ↓
User-Scoped Data Access: users/{user_id}/tasks/{task_id}
```

> [!IMPORTANT]
> **V1 Scope Boundary:** Version 1 guarantees strict single-user data isolation. Enterprise RBAC, organization administration portals, and tenant billing are strictly out of scope.

## Security Audit Checklist
- [ ] **Token Verification:** Every protected endpoint derives `user_id` strictly from verified JWT tokens.
- [ ] **No Client-Supplied Identity Trust:** Client-supplied `user_id` values in request bodies or query parameters are ignored for authorization.
- [ ] **Cross-User Access Prevention:** User A cannot view, edit, or delete User B's tasks under any circumstance.
- [ ] **Firestore Security Rules:** Server-side rules enforce `request.auth.uid == userId`.
- [ ] **Safe Code Execution:** Absolute zero `eval()` or `exec()` in backend code.
- [ ] **Secret Hygiene:** Zero API keys, private keys, or credentials committed to git or exposed in client bundles.
- [ ] **CORS Security:** Restricted to approved frontend origins.

## Files to Review / Modify
- `firebase/firestore.rules`
- `backend/app/core/security.py`
- `backend/app/services/task_service.py`
- `backend/tests/integration/test_security_isolation.py`

## Acceptance Criteria
- Automated security tests verify that cross-user data access attempts return HTTP 403 / 404.
- Security audit checklist passes completely.

## Stop Condition
**STOP.** Document security review in `05_PROGRESS.md`, and stop.

---

# PHASE 13 — Performance, Observability and Reliability

## Objective
Equip TaskMate with structured logging, diagnostic observability, and rate-limiting protections.

## Requirements
- Structured JSON logging capturing request ID, latency, tool calls, and user ID (no sensitive data).
- Rate-limiting protection on `/api/chat` to protect against API abuse and runaway costs.
- Performance profiling ensuring responsive interactions.

## Files to Create / Modify
- `backend/app/core/logging.py`
- `backend/app/api/middleware.py`
- `backend/tests/api/test_rate_limiting.py`

## Implementation Work
1. Configure structured logging in `backend/app/core/logging.py`:
   - Log: `request_id`, `user_id`, `tool_name`, `latency_ms`, `status_code`.
   - Never log: passwords, API keys, tokens, or private conversation text.
2. Implement IP / User rate limiting on `POST /api/chat` using standard middleware.
3. Configure request timeout handling for external Nemotron API invocations.

## Tests
- Test rate-limiter: exceeding threshold returns HTTP 429 Too Many Requests.
- Verify log outputs conform to structured JSON format without credential leakage.

## Acceptance Criteria
- Application emits clean diagnostic logs and handles external timeouts gracefully.

## Stop Condition
**STOP.** Verify observability and reliability, update progress, and stop.

---

# PHASE 14 — Production Readiness and Deployment

## Objective
Prepare TaskMate for production deployment with verified environment hygiene, documentation, and operational scripts.

## Deployment Scope
- Prepare deployment configuration without locking into a specific cloud provider until officially selected in architecture reviews (e.g., Cloud Run, App Engine, or container host).
- Enforce production configuration requirements:
  - HTTPS enforcement.
  - Strict CORS origin whitelisting.
  - Production Firebase project and Firestore security rules deployed.
  - Server-side environment variables injected securely via secret manager.
  - Built frontend assets served securely.

## Files to Create / Modify
- `Dockerfile` (or `backend/Dockerfile`)
- `scripts/build_production.ps1`
- `scripts/build_production.sh`
- `docs/DEPLOYMENT.md`
- `05_PROGRESS.md`

## Final Pre-Deployment Verification
- [ ] No `.env` or secret files committed in git history.
- [ ] All automated backend and frontend test suites pass.
- [ ] Production Firestore rules deployed and verified.
- [ ] Health endpoint `/health` functional.
- [ ] End-to-end task workflows verified with Nemotron agent.
- [ ] Deployment guide documented in `docs/DEPLOYMENT.md`.

## Acceptance Criteria
- TaskMate is fully deployable according to documented instructions and verified operational checkpoints.

## Stop Condition
**STOP.** Complete final milestone report, update `05_PROGRESS.md` and `memory.md`, and present completion handover.

---

# 7. Non-Negotiable Phase Execution Gate

Every phase must be executed with strict engineering discipline:

```text
Read Current Phase Requirements
              ↓
Inspect Existing Repository State
              ↓
Implement Current Phase Work Only
              ↓
Execute Tests & Verify Behavior
              ↓
Confirm All Acceptance Criteria Met
              ↓
Update Progress Tracker (05_PROGRESS.md)
              ↓
            STOP
```

Under no circumstances may an AI assistant begin work on subsequent phases without explicit direction from the user.
