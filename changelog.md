# TaskMate — Changelog

All notable changes to the **TaskMate** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added

- **Phase 10 — Checkpoint 10.1: Backend E2E Integration Test Suite:**
  - Implemented `backend/tests/integration/test_e2e_flow.py` covering task creation, listing, calculation, completion, and multi-turn conversational scenarios.
  - 6/6 integration tests passing; 152/152 total backend pytests passing; 0 ruff errors.
- **Phase 10 — Checkpoint 10.2: Firestore Client-Side SDK Integration:**
  - Integrated Cloud Firestore client singleton in `frontend/src/services/firebase.ts`.
  - Implemented user-scoped Firestore operations in `frontend/src/services/taskService.ts` (`users/{uid}/tasks/{task_id}`).
  - Added resilient offline/demo fallback to local storage cache.
  - 10/10 frontend verification tests passing; 0 TypeScript errors.
- **Phase 10 — Checkpoint 10.3: Live Chat API & UI State Synchronization:**
  - Connected conversational chat in `aiService.ts` to `POST /api/chat` with Firebase Bearer token authentication via `apiClient.ts`.
  - Implemented `applyAiToolEffects` in `AppContext.tsx` synchronizing AI task operations (`create_task`, `complete_task`, `update_task`, `delete_task`) directly into React state.
  - Enforced deduplication to prevent duplicate tasks when processing `created_task`.
  - Prevented duplicate Firestore writes by treating backend agent execution as authoritative and updating local storage cache.
  - Enabled live reactivity for Kanban columns (*Pending*, *In Progress*, *Completed*) and Dashboard derived metrics without page refresh.
  - Sanitized and safely handled HTTP 401, 422, 500, and network errors without crashing React or leaking stack traces.
  - Added automated tests 11–18 in `frontend/src/tests/test_phase9_frontend.mjs` (18/18 total frontend tests passing).
  - Production build (`npm run build`) and lint (`npm run lint`) clean with 0 errors.

- **Phase 10 — Checkpoint 10.4: Google Colab End-to-End Validation Notebook:**
  - Authored comprehensive validation notebook at `notebooks/07_end_to_end_validation.ipynb`.
  - Implemented all 7 required sections:
    1. Environment configuration (path handling, secure credential masking, testing environment).
    2. FastAPI TestClient setup & route health/auth checks.
    3. Scenario 1 (Creation): `"Create a high priority task to study Python tomorrow."` validating date-time resolution, task creation, high priority, pending status, and due date.
    4. Scenario 2 (Query): `"Show my pending tasks."` validating status filtering and grounded list response.
    5. Scenario 3 (Calculation): `"I have 30 chapters and 6 days. How many per day?"` validating AST calculator dispatch (`30 / 6 = 5`).
    6. Scenario 4 (Completion): `"Mark task 'study Python' as completed."` validating task status mutation to completed.
    7. Frontend Integration & State Synchronization Model validating dynamic state reactivity, deduplication, Kanban columns, and Dashboard metric recalculation mirroring `AppContext.tsx`.
  - Verified 100% successful execution across all 7 code cells with assertions passing.

- **Phase 10 — Checkpoint 10.5: Full Regression Testing, Build Verification & Documentation:**
  - Executed full backend pytest regression suite: 152/152 passed with 0 failures across api, unit, agent, and integration suites.
  - Verified backend linter with zero errors (`ruff check backend/`).
  - Executed frontend automated test suite: 18/18 passed with 0 failures (`src/tests/test_phase9_frontend.mjs`).
  - Verified frontend TypeScript and linter with zero errors (`tsc --noEmit`).
  - Validated production build (`vite build` finished in ~5.28s, generating assets in `frontend/dist/`).
  - Assessed end-to-end runtime environment: NVIDIA API live and operational; Cloud Firestore API in Google Cloud Console project `taskmate-d9f55` currently disabled (`403 SERVICE_DISABLED`), transparently documented and thoroughly backed by deterministic integration test coverage.
  - Phase 10 officially marked COMPLETED across all master documentation records.

- **Phase 11: Testing and Error Handling:**
  - **Checkpoint 11.1 (Centralized Error Handling & Sanitization):** Implemented `backend/app/core/errors.py` with custom exception classes (`TaskMateError`, `NotFoundError`, `UnauthorizedError`, `ValidationError`, `ServiceUnavailableError`) and global exception handlers mounted in `main.py`. Ensures 0 internal stack traces, DB paths, or secrets leak in 500 errors. 8/8 API error tests passing.
  - **Checkpoint 11.2 (Tool & Agent Boundary Conditions):** Added 23 unit boundary tests (`test_error_boundaries.py`) covering Calculator (division by zero, syntax errors, overflow, disallowed lookups), Date/Time (unrecognized/invalid dates), and Task Tool (non-existent task operations). Added 6 agent tests (`test_agent_error_handling.py`) verifying timeout handling, provider 500s, and truthful failure reporting.
  - **Checkpoint 11.3 (Frontend Defensive Error Handling & Rollback):** Added 7 frontend tests (`test_phase11_error_handling.mjs`) verifying optimistic creation/update/move/delete rollbacks, AI chat input unlocking, raw HTML 502 error sanitization, and offline network handling. 25/25 total frontend tests passing.
  - **Checkpoint 11.4 (E2E Error Resilience Suite):** Implemented 6 full-stack integration tests in `test_error_resilience.py` verifying system behavior under LLM timeout, auth rejection, division by zero, non-existent task IDs, and unexpected agent crashes.
  - **Checkpoint 11.5 (Full Regression & Build Verification):** 195/195 backend pytests passing, 0 ruff errors, 25/25 frontend tests passing, 0 TypeScript errors, clean Vite production build.

### Planned

- Phase 12: Security and Tenant Isolation Review.

---

## [0.13.0] — 2026-09-12

### Added

- **Phase 9: React Frontend (`frontend/src/`):**
  - Implemented `KanbanBoard.tsx` providing an interactive 3-column workflow (*Pending*, *In Progress*, *Completed*) with real-time status shifting, task badges, and category/priority filter integration.
  - Implemented `apiClient.ts` connecting the React frontend to FastAPI `/api/chat` and `/api/health` endpoints with dynamic Firebase ID token Bearer authentication and sanitized error handling.
  - Defined canonical TypeScript domain and API models in `types/index.ts` (`Task`, `TaskPriority`, `TaskStatus`, `UserProfile`, `ChatMessage`, `NavView`, `TaskFilters`, `ProductivitySummary`, `KanbanColumn`, `ChatRequestPayload`, `ChatResponsePayload`, `ApiError`).
  - Enhanced centralized state management in `AppContext.tsx` with optimistic UI updates, clean error rollback, canonical derived metrics, and `moveTaskStatus`.
  - Added Kanban navigation route and view mode toggle in `Header.tsx`, `App.tsx`, and `TaskPanel.tsx`.
  - Configured Vite dev server proxy in `vite.config.ts` routing `/api` and `/health` requests to `http://127.0.0.1:8000`.
  - Created automated frontend verification suite in `src/tests/test_phase9_frontend.mjs` verifying summary calculations, optimistic mutations with rollback, Kanban state transitions, Bearer token injection, error mapping, and search/sort logic (8/8 passing).
  - Validated frontend build (`npm run lint` and `npm run build` with 0 errors).
  - Regression verified full backend test suite (146/146 pytests passing) and linter cleanliness (0 ruff errors).


---

## [0.12.0] — 2026-09-12

### Added

- **Phase 8: FastAPI API Layer (`backend/app/api/`, `backend/app/models/`):**
  - Implemented `POST /api/chat` route in `backend/app/api/routes_chat.py` backed by `TaskMateAgent` and the Nemotron agent loop.
  - Defined Pydantic validation schemas in `backend/app/models/chat.py` (`ChatRequest` and `ChatResponse`) with whitespace-trimmed validation and extra field rejection.
  - Enforced cryptographic Firebase ID token verification dependency (`get_current_user`) requiring valid Bearer tokens for all `/api/chat` interactions.
  - Mounted `chat_router` in `backend/app/main.py` with CORS middleware configured for frontend origins.
  - Added structured diagnostics logging latency, user context, tool calls count, and success status.
  - Authored Google Colab experimentation notebook `notebooks/06_api_testing.ipynb`.
  - Created automated test suite in `backend/tests/api/test_chat.py` with 16 unit, validation, auth, and CORS tests (146/146 total backend tests passing).
  - Manually verified all endpoints live on `127.0.0.1:8000` (`GET /health`, unauthenticated `/api/chat`, invalid token rejection, input validation, and authenticated chat execution).
  - Clean linter verification with 0 errors (`ruff check backend/`).

---

## [0.11.0] — 2026-09-12

### Added

- **Phase 7: Agent Loop Orchestration (Nemotron):**
  - Implemented `TaskMateAgent` in `backend/app/agent/agent.py` orchestrating the full iterative agent reasoning loop: Prompt -> Nemotron -> Tool Selection -> Observation Feedback -> Truthful Synthesis.
  - Defined `TASKMATE_SYSTEM_PROMPT` in `backend/app/agent/prompts.py` enforcing mandatory tool usage for math/dates, strict grounding in tool observations, zero result fabrication, and honest error reporting.
  - Supported multi-step tool execution (e.g. resolve relative date via `get_date_time` then invoke `create_task`) with a configurable `max_iterations` safety bound (default: 5) to prevent infinite loops.
  - Implemented `_sanitize_response_content` stripping `<think>...</think>` tags to prevent raw chain-of-thought leakage in end-user responses.
  - Enforced multi-tenant isolation and security guards: verified `user_id` injection on all `TaskTool` calls, parameter validation, and prompt forgery neutralization.
  - Created Google Colab experimentation notebook `notebooks/05_agent_loop.ipynb`.
  - Authored comprehensive test suite in `backend/tests/agent/test_agent_loop.py` with 20 unit and security tests covering create, list, get, update, complete, delete, calculate, datetime, multi-step chaining, no-tool conversation, ambiguous request handling, tool failures, and LLM error resilience (130/130 total backend tests passing).
  - Clean linter verification with 0 errors (`ruff check backend/`).

---

## [0.10.0] — 2026-09-12

### Added

- **Phase 6: LLM Connection and Structured Tool Calling (Nemotron):**
  - Implemented `LLMService` in `backend/app/services/llm_service.py` connecting to NVIDIA Nemotron via OpenAI-compatible endpoint (`{LLM_BASE_URL}/chat/completions`).
  - Added configuration support for `NVIDIA_API_KEY`, `LLM_API_KEY`, `LLM_BASE_URL`, `NVIDIA_BASE_URL`, and `LLM_TIMEOUT` in `backend/app/core/config.py`.
  - Defined OpenAI-compatible function calling schemas in `backend/app/agent/schemas.py` for all 6 task operations (`create_task`, `list_tasks`, `get_task`, `update_task`, `complete_task`, `delete_task`) and utility tools (`calculate`, `get_date_time`).
  - Implemented `ToolRegistry` in `backend/app/agent/tool_registry.py` providing schema discovery, argument validation, and safe dispatching to `TaskTool` and utility functions.
  - Enforced strict tenant isolation: `user_id` is hidden from schemas exposed to the LLM, and any `user_id` injected into tool arguments by the LLM is automatically stripped. `TaskTool` is bound exclusively to the authenticated caller's verified `user_id`.
  - Implemented two-turn conversational flow in `LLMService.run_conversation_turn` handling tool execution and natural-language synthesis.
  - Authored Google Colab experimentation notebooks: `notebooks/02_llm_connection.ipynb` and `notebooks/03_tool_calling.ipynb`.
  - Created comprehensive test suite in `backend/tests/agent/test_agent_tools.py` with 20 automated unit and security tests covering all 16 required verification points (110/110 total backend tests passing).
  - Verified linter cleanliness with zero warnings or errors (`ruff check backend/`).

---

## [0.9.0] — 2026-09-12

### Added

- **Phase 5: Task Tool (`backend/app/tools/`):**
  - Implemented agent-facing `TaskTool` in `backend/app/tools/task_tool.py` connecting the agent loop to `TaskService`.
  - Injected verified `user_id` context upon initialization (`TaskTool(user_id=...)`), preventing LLM prompt forgery and enforcing multi-tenant isolation.
  - Implemented all 6 approved agent task operations: `create_task`, `list_tasks`, `get_task`, `update_task`, `complete_task`, and `delete_task`.
  - Standardized structured dictionary returns with `success: bool`, formatted messages, payload data, and descriptive errors for LLM observations.
  - Implemented dynamic operation dispatcher `execute(operation: str, **kwargs)`.
  - Authored comprehensive test suite in `backend/tests/unit/test_task_tool.py` (17 tests) covering all operations, error handling, input validation, and multi-tenant security isolation (90/90 total backend tests passing).
  - Clean linter verification with zero errors (`ruff check backend/`).

---

## [0.8.0] — 2026-09-12

### Added

- **Phase 4: Calculator and Date/Time Tools (`backend/app/tools/`):**
  - Implemented safe AST-based arithmetic evaluator in `backend/app/tools/calculator.py` adhering to strict **Zero `eval()` Policy**.
  - Supported arithmetic operations: `+`, `-`, `*`, `/`, `//`, `%`, `**`, `^` (power alias), unary `+`/`-`, and parentheses.
  - Whitelisted safe mathematical functions: `sqrt`, `round` (1 or 2 arguments), `abs`, `ceil`, `floor`.
  - Enforced code injection protection: blocks `__import__`, `eval`, `exec`, `open`, variable lookups, and attribute access.
  - Handled division by zero (`ZeroDivisionError`) and syntax errors gracefully.
  - Implemented deterministic Date/Time tool in `backend/app/tools/datetime_tool.py` providing real-time system clock grounding.
  - Parsed natural language relative dates: `"today"`, `"now"`, `"tomorrow"`, `"yesterday"`, `"in N days"`, `"in N weeks"`, `"in N hours"`, `"next <weekday>"`, and explicit ISO dates (`YYYY-MM-DD`).
  - Added optional `anchor` parameter for deterministic testing.
  - Authored comprehensive test suites in `backend/tests/unit/test_calculator.py` (24 tests) and `backend/tests/unit/test_datetime_tool.py` (11 tests) — all 35 tests passing (73/73 total backend tests passing).
  - Linter verification clean with zero errors (`ruff check backend/`).

---

## [0.7.0] — 2026-09-12

### Added

- **Phase 3: Data Models and Task Service (`backend/`, `firebase/`):**
  - Implemented Pydantic models in `backend/app/models/task.py`: `TaskCreate`, `TaskUpdate`, `TaskResponse`, `TaskPriority` enum (`low`, `medium`, `high`), and `TaskStatus` enum (`pending`, `in_progress`, `completed`).
  - Added strict domain validation: string trimming, non-empty title constraints (1–200 characters), description limits (<=2000 characters), and ISO-8601 UTC timestamp generation.
  - Implemented `get_firestore_client()` helper in `backend/app/services/firebase.py` for accessing Firestore client from the initialized Firebase Admin app.
  - Implemented user-scoped `TaskService` in `backend/app/services/task_service.py` strictly partitioning all queries, mutations, and deletions under `users/{user_id}/tasks/{task_id}`.
  - Implemented complete CRUD lifecycle: `create_task`, `list_tasks` (with optional status and priority filters), `get_task`, `update_task`, `complete_task`, and `delete_task`.
  - Added parameter guards enforcing non-empty `user_id` and `task_id` with `ValueError`.
  - Configured Firestore security rules in `firebase/firestore.rules` enforcing `request.auth.uid == userId` for all task document operations.
  - Configured composite index definitions in `firebase/firestore.indexes.json` for status and priority with created_at ordering.
  - Created comprehensive unit test suite in `backend/tests/unit/test_task_service.py` with 25 passing tests verifying models, full CRUD operations, and multi-tenant security isolation (38/38 total backend tests passing).


### Added

- **Phase 2: Firebase Setup and Authentication Foundation (`backend/`, `frontend/`):**
  - Integrated `firebase-admin>=6.5.0` into backend requirements.
  - Implemented Firebase Admin SDK initialization in `backend/app/services/firebase.py` with support for service account credentials, environment variables, ADC, and offline fallback.
  - Implemented cryptographic JWT token verification in `backend/app/core/security.py` (`verify_firebase_token`) deriving authenticated `user_id` strictly from token claims (`decoded_token["uid"]`).
  - Implemented FastAPI security dependency `get_current_user` in `backend/app/api/dependencies.py` extracting Bearer tokens from `Authorization` header and raising HTTP 401 on missing, expired, or malformed credentials.
  - Author comprehensive pytest suite in `backend/tests/api/test_auth_dependency.py` covering valid tokens, expired tokens, malformed tokens, non-Bearer schemes, and live token mocks (8/8 tests passing).
  - Updated client authentication foundation in `frontend/src/services/authService.ts` to support `getIdToken()` for Bearer token transmission and Google authentication foundation.
  - Created Google Colab validation notebook `notebooks/04_firebase_connection.ipynb` validating Firebase Admin SDK and token verification.

---

## [0.5.0] — 2026-09-12

### Added

- **Phase 1: Production Python Backend Environment & Skeleton (`backend/`):**
  - Initialized Python 3.11+ modular monolith application structure under `backend/app/`.
  - Configured production dependencies in `backend/requirements.txt` (`fastapi`, `uvicorn[standard]`, `pydantic`, `pydantic-settings`, `httpx`).
  - Configured dev & test dependencies in `backend/requirements-dev.txt` (`pytest`, `pytest-asyncio`, `ruff`).
  - Implemented centralized environment settings in `backend/app/core/config.py` using Pydantic `BaseSettings` with support for `.env` loading, CORS configuration, and placeholder configuration for future phases.
  - Implemented `GET /health` and `GET /api/health` probes in `backend/app/api/routes_health.py` returning status, service name, and ISO-8601 UTC timestamp.
  - Built FastAPI application entry point in `backend/app/main.py` with CORS middleware, lifespan lifecycle handler, and OpenAPI documentation endpoints (`/docs`, `/redoc`, `/openapi.json`).
  - Created automated backend test suite in `backend/tests/api/test_health.py` verifying `/health`, `/api/health`, and `/` routes.
  - Created development launch runners for PowerShell (`scripts/dev_backend.ps1`) and Bash (`scripts/dev_backend.sh`).
  - Created Google Colab validation notebook `notebooks/01_environment_setup.ipynb` testing Python 3.11+ runtime, dependencies, config loading, and health endpoint response.
  - Created backend environment variable template `backend/.env.example`.
  - Updated `.gitignore` with Python virtual environments, caches, and test artifacts.

---

## [0.4.0] — 2026-09-11

### Added

- **Persistent AI Context System:**
  - Created `decisions.md` documenting Architectural Decision Records (ADR-001 through ADR-019), defining the modular monolith structure, React frontend, Python + FastAPI backend, Nemotron runtime agent, safe tool boundaries, and user-scoped authorization.
  - Created `rules.md` establishing mandatory guidelines for AI coding assistants and developers, including coding standards, folder structures, naming conventions, UI/UX consistency, git commit rules, and security policies.
  - Created `memory.md` maintaining long-term project memory, tech stack inventory, feature status, API endpoint specifications, Firestore schema definitions, and implementation roadmap.
  - Reconciled `changelog.md` to provide a verified chronological history of development.

### Changed

- **Architectural Reconciliation:**
  - Formally established the **Modular Monolith** architecture for Version 1, rejecting unnecessary distributed microservices and enterprise multi-tenant overhead.
  - Designated **Python 3.11+ + FastAPI + Pydantic** as the authoritative production backend service (`backend/app/`), marking the earlier Node.js Express host as superseded (ADR-003, ADR-017).
  - Designated **Nemotron** as the initial runtime agent model for the LLM tool-calling and agent-loop phases, while keeping the provider configurable via environment variables (ADR-004, ADR-005).
  - Clarified that Google AI Studio was utilized strictly as a development and UI generation tool during early workspace prototyping, not as the production runtime agent.
  - Explicitly defined the single-user authorization boundary: deriving user identity exclusively from verified Firebase ID tokens and scoping tasks under `users/{user_id}/tasks/{task_id}` (ADR-010, ADR-019).
  - Clarified Google Colab notebooks as an isolated experimentation and validation environment, not the production application runtime (ADR-014).
  - Formatted superseded decisions (ADR-017, ADR-018, ADR-019) to preserve historical integrity while preventing contradictory architectural assumptions.

---

## [0.3.0] — 2026-09-11

### Added

- **Interactive React 19 Frontend Prototype (`src/`):**
  - Application shell with navigation header supporting view routing between Workspace, Dashboard, Tasks, and AI Assistant (`src/App.tsx`, `src/components/layout/Header.tsx`).
  - **Workspace View (`src/components/workspace/WorkspaceView.tsx`):** Split-view combining rapid task entry, interactive Kanban columns, and the embedded assistant panel.
  - **Kanban Board (`src/components/tasks/KanbanBoard.tsx`):** Three-column board layout (*Pending*, *In Progress*, *Completed*) with direct status toggle controls and priority badges.
  - **Dashboard View (`src/components/dashboard/DashboardView.tsx`):** Productivity summary metrics tracking total tasks, completion percentage, high-priority counts, and category distribution.
  - **Tasks Panel (`src/components/tasks/TaskPanel.tsx`):** Filter bar supporting text search, status filters, priority filters, category filters, and sorting by due date, priority, or title.
  - **Modals & Overlays:** Task creation/edit dialog (`TaskModal.tsx`), authentication dialog (`AuthModal.tsx`), and floating toast notifications (`Toast.tsx`).
  - **State Management & Local Service Layer:** React `AppContext` providing centralized state with optimistic UI updates; `taskService.ts` managing CRUD operations via browser local storage with seed starter tasks; `authService.ts` managing mock user profiles for offline development.
- **Safe AST Math Evaluator (`src/utils/safeEvaluator.ts`):**
  - Recursive descent arithmetic tokenizer and parser supporting `+`, `-`, `*`, `/`, `%`, `^`, parentheses, and safe functions (`sqrt`, `round`, `abs`, `ceil`, `floor`).
  - Enforced zero `eval()` and zero `Function()` execution policy to prevent code injection.
  - Sanitized error handler masking internal error details for user-facing output.
- **Deterministic Temporal Resolver (`src/utils/safeEvaluator.ts`):**
  - Date resolution logic mapping expressions (*"today"*, *"tomorrow"*, *"yesterday"*, *"next monday"*, *"in N days"*) to standardized ISO-8601 strings and human-readable dates.
- **Exploratory Development Host Prototype (`server.ts`):**
  - Node.js Express server configured to run Vite in middleware mode during local development.
  - Health check endpoint `GET /api/health`.
  - Tool execution endpoints `POST /api/tools/calculate` and `POST /api/tools/date-time`.
  - Exploratory agent orchestration endpoint `POST /api/agent/chat` testing tool declarations with the Gemini SDK and an offline regex/heuristic fallback. *(Note: Preserved as historical prototype; superseded by planned FastAPI backend in ADR-003 and ADR-017).*

### Fixed

- Handled division by zero and malformed parentheses expressions safely within the AST arithmetic evaluator.
- Addressed layout shift between Kanban and list views when switching active task filters.

---

## [0.2.0] — 2026-09-11

### Added

- **Product Requirements Document (`TaskMate_01_PRD.md`):**
  - Documented product vision, problem statement, target audience, and primary success criteria.
  - Defined 15 Functional Requirements (FR-01 through FR-15) covering authentication, task lifecycle, tool integration, error handling, and user data ownership.
  - Defined 7 Non-Functional Requirements (NFR-01 through NFR-07) covering usability, reliability, security, maintainability, and testability.
  - Specified tool interfaces for Calculator, Date/Time, and Firestore Task operations.
  - Established data validation rules, security requirements, and acceptance criteria.
- **Implementation Phases Specification (`TaskMate_03_PHASES.md`):**
  - Detailed a 12-phase engineering roadmap from Phase 0 (Documentation & Preparation) to Phase 12 (Production Handover).
  - Outlined the Colab notebook validation strategy (`01_environment_setup.ipynb` through `07_end_to_end_validation.ipynb`).
  - Defined the target repository layout and phase-by-phase acceptance criteria.

---

## [0.1.0] — 2026-09-11

### Added

- Initial repository initialization with base configuration: `package.json`, `tsconfig.json`, `vite.config.ts`, `.env.example`, `.gitignore`.
- Configured foundational development dependencies: React 19, TypeScript, Vite, Tailwind CSS, Lucide React, and Motion.
- Set up initial project metadata.
