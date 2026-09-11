# TaskMate — Changelog

All notable changes to the **TaskMate** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned

- Implement the production Python + FastAPI backend application under `backend/app/` according to the approved phase plan (`TaskMate_03_PHASES.md`).
- Integrate Firebase Authentication and implement backend Firebase ID token verification middleware.
- Implement the Cloud Firestore-backed task service with user-scoped storage (`users/{user_id}/tasks/{task_id}`).
- Connect Nemotron as the runtime agent model through the configurable `LLMService` abstraction layer.
- Connect the React frontend with the FastAPI `/api/chat` endpoint and verify end-to-end task workflows.
- Execute validation notebooks (`notebooks/01_*.ipynb` through `07_*.ipynb`) in Google Colab.
- Author and run automated unit and integration test suites using `pytest` for the backend and `vitest` for the frontend.
- Perform security and authorization validation prior to production deployment preparation.

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
