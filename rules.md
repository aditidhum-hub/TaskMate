# TaskMate — AI Agent & Developer Rules

This document establishes the mandatory operational, architectural, coding, security, and quality rules for **TaskMate**. Every AI coding assistant and human developer working on this codebase **must strictly adhere to these rules throughout the entire project lifecycle**.

---

## 1. Prime Directive: Regression Safety & Deliberate Evolution

> [!IMPORTANT]
> **NEVER BREAK EXISTING FUNCTIONALITY UNLESS EXPLICITLY REQUESTED.**

- **Preserve Working Behavior:** When refactoring, extending, or fixing code, preserve all verified user-facing and backend behaviors.
- **Inspect Shared Dependencies:** Before modifying any shared module, component, hook, or service, inspect all consuming files to prevent unintended regressions.
- **Run Regression Tests:** After making any meaningful code changes, execute relevant test suites and verify that existing flows continue to work.
- **Controlled Migration:** Intentional architecture migrations (e.g., replacing early Node.js prototype scaffolding with the production Python/FastAPI backend) are permitted and expected **only when the currently approved implementation phase explicitly calls for it**.
- **Do Not Preserve Obsolete Architecture:** Do not preserve obsolete prototype architecture (e.g., Express microservice assumptions) merely because it existed earlier. Migrate cleanly according to the approved architecture.

---

## 2. Mandatory Context Reading

Before planning or implementing any meaningful change, an AI coding assistant **must read and inspect the relevant project context**:

1. `TaskMate_01_PRD.md` (or `docs/01_PRD.md`)
2. `02_ARCHITECTURE.md` (or `docs/02_ARCHITECTURE.md`, where present)
3. `TaskMate_03_PHASES.md` (or `docs/03_PHASES.md`)
4. `decisions.md` (Architectural Decision Records)
5. `rules.md` (Operational rules — this document)
6. `memory.md` (Long-term project memory and state)
7. `changelog.md` (Chronological release log)
8. `05_PROGRESS.md` (Phase progress tracker, where present)

### Execution Protocol:
1. **Determine the current phase** from the project documentation.
2. **Inspect the actual repository** to verify existing code state.
3. **Check accepted decisions** in `decisions.md` to avoid contradicting established architecture.
4. **Implement ONLY the requested / current phase**.
5. **Run tests** to verify correctness and stability.
6. **Update persistent documentation** (`memory.md`, `changelog.md`, `decisions.md`, `05_PROGRESS.md`) when appropriate.

---

## 3. Strict Phase Discipline

AI assistants must never jump ahead or silently implement future phases. Development proceeds one approved phase at a time.

```text
Read Current Phase Requirements
              ↓
Inspect Existing Implementation State
              ↓
Implement Current Phase Code
              ↓
Run Automated Tests & Fix Failures
              ↓
Verify Phase Acceptance Criteria
              ↓
Update Progress Documentation (05_PROGRESS.md / memory.md / changelog.md)
              ↓
            STOP
```

Do not automatically continue to the next phase without explicit user direction.

---

## 4. Authoritative Folder Structure

TaskMate converges toward the standard directory layout below. Do not scatter random scripts, temporary files, or scratch outputs in root or unapproved directories:

```text
TaskMate/
│
├── docs/                     # Core specifications and plans
│   ├── 01_PRD.md
│   ├── 02_ARCHITECTURE.md
│   ├── 03_PHASES.md
│   ├── 04_AGENT_DEVELOPMENT_RULES.md
│   └── 05_PROGRESS.md
│
├── decisions.md              # Architectural Decision Records (ADRs)
├── rules.md                  # Permanent AI & developer rules (this document)
├── memory.md                 # Long-term project memory & technical contracts
├── changelog.md              # Chronological release and change history
│
├── backend/                  # Production Python + FastAPI Modular Monolith
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI application entry point
│   │   ├── api/              # Route handlers and dependency injection
│   │   ├── agent/            # Agent orchestration, prompts, and tool registry
│   │   ├── tools/            # Approved tool implementations (calc, datetime, task)
│   │   ├── services/         # External integrations (Firebase Admin, LLMService)
│   │   ├── models/           # Domain schemas and Pydantic validation entities
│   │   ├── core/             # Configuration, security, logging
│   │   └── utils/            # Shared Python helpers
│   ├── tests/                # Pytest suites (unit, agent, api, integration)
│   ├── requirements.txt      # Production runtime dependencies
│   ├── requirements-dev.txt  # Testing and linting dependencies
│   └── .env.example          # Template for backend environment variables
│
├── frontend/ (or src/)       # React SPA
│   ├── src/
│   │   ├── components/       # Reusable UI component hierarchy
│   │   │   ├── chat/         # AI Assistant panel and status indicators
│   │   │   ├── dashboard/    # Productivity metrics and visual analytics
│   │   │   ├── layout/       # Navigation header and containers
│   │   │   ├── modals/       # Task edit and authentication modals
│   │   │   ├── tasks/        # Kanban board, task list, filter bars
│   │   │   ├── ui/           # Design primitives (Button, Toast, Badge)
│   │   │   └── workspace/    # Unified workspace view
│   │   ├── pages/            # Page-level route views (if applicable)
│   │   ├── services/         # Client API services and backend connectors
│   │   ├── hooks/            # Custom React hooks
│   │   ├── context/          # React Context providers (AppContext)
│   │   ├── types/            # TypeScript domain interfaces
│   │   └── utils/            # Pure UI utilities and date formatters
│   ├── package.json
│   ├── vite.config.ts
│   └── .env.example          # Template for public client variables
│
├── notebooks/                # Google Colab Experimentation & Validation
│   ├── 01_environment_setup.ipynb
│   ├── 02_llm_connection.ipynb
│   ├── 03_tool_calling.ipynb
│   ├── 04_firebase_connection.ipynb
│   ├── 05_agent_loop.ipynb
│   ├── 06_api_testing.ipynb
│   └── 07_end_to_end_validation.ipynb
│
├── firebase/                 # Firebase Infrastructure Configuration
│   ├── firestore.rules       # Security rules enforcing user isolation
│   └── firestore.indexes.json # Index configuration for Firestore queries
│
├── scripts/                  # Development and validation runner scripts
├── tests/                    # Top-level integration / E2E test suites
├── README.md
└── .gitignore
```

> [!CAUTION]
> **No Production Logic in Notebooks:** Production backend business logic must reside in `backend/app/`. Notebooks under `notebooks/` are strictly for experimentation and validation.

---

## 5. Python Backend Rules

The TaskMate backend is a **Modular Monolith** built with **Python 3.11+**, **FastAPI**, and **Pydantic**:

- **Strict Type Annotations:** Use Python type hints (`str`, `int`, `Optional[T]`, `List[T]`, Pydantic models) on all functions, service methods, and route handlers.
- **Pydantic Validation:** Validate all incoming HTTP payloads, tool invocation arguments, and external responses using Pydantic `BaseModel`.
- **Modular Monolith Boundaries:** Keep internal modules decoupled. Direct imports between domain modules (`api/`, `agent/`, `tools/`, `services/`, `models/`) must follow clean dependency layering:
  - `api/` depends on `services/`, `agent/`, and `models/`.
  - `agent/` depends on `tools/`, `models/`, and `services/`.
  - `tools/` depends on `services/` and `models/`.
  - `services/` depends on `models/` and external libraries.
- **PEP 8 Compliance:** Follow PEP 8 standards. Code formatting and linting should conform to standard tools (`ruff`, `black`).
- **No Unnecessary Frameworks:** Do not introduce heavy ORMs, Celery workers, Redis brokers, or secondary web frameworks into Version 1.

---

## 6. TypeScript & React Frontend Rules

- **Strict Mode:** TypeScript `strict: true` must remain active at all times.
- **Avoid `any`:** Disallow untyped `any` across frontend code. Use explicit interfaces and types for:
  - Component props
  - REST API contracts
  - Task and User domain models
  - Chat message structures
  - Service responses
- **Smart Inference:** Do not redundantly annotate simple local variables where TypeScript's type inference is unambiguous and safe.
- **Functional Components & Hooks:** Use functional React components (`React.FC<Props>` or `function Component(props: Props): JSX.Element`) with standard React hooks (`useState`, `useEffect`, `useCallback`, `useMemo`).
- **Clean Layer Separation:**
  - **UI (`components/`)**: Visual presentation only.
  - **State (`context/`, `hooks/`)**: Global application state and reactive hooks.
  - **Services (`services/`)**: HTTP communication with backend endpoints.
  - **Utilities (`utils/`)**: Pure UI helpers, string formatting, and date display.
  - **Types (`types/`)**: Centralized TypeScript declarations.

---

## 7. Safe Arithmetic Evaluation Rules

- **Zero `eval()` Policy:** Under NO circumstances should `eval()`, `exec()`, or JavaScript `new Function()` be used for user-provided arithmetic, text parsing, or code execution.
- **Restricted Evaluator:** Calculator input must be processed through an isolated, safe parser:
  - In Python backend: Use an `ast`-based safe evaluator or an explicitly restricted grammar.
  - Allowed operations: binary operators (`+`, `-`, `*`, `/`, `%`, `^`), parentheses, and safe functions (`sqrt`, `round`, `abs`, `ceil`, `floor`).
  - Disallow all variable assignments, property accessors, statement executions, system calls, and global imports.
- **Architecture Note:** Do not permanently require a TypeScript file like `src/utils/safeEvaluator.ts` as the production engine once the backend Calculator Tool is operational in Python (`backend/app/tools/calculator.py`).

---

## 8. Agent Behavior & Safety Invariants

The TaskMate AI Agent operates within a strictly defined tool boundary.

### 8.1 Approved Version 1 Tools
1. **`Calculator Tool`**: Evaluates safe arithmetic expressions.
2. **`Date/Time Tool`**: Deterministically resolves current and relative dates (`"today"`, `"tomorrow"`, `"next Monday"`, `"in 5 days"`) using real-time system clock logic.
3. **`Task Tool`**: Performs CRUD actions on Firestore tasks:
   - `create_task`
   - `list_tasks`
   - `get_task`
   - `update_task`
   - `complete_task`
   - `delete_task`

### 8.2 Mandatory Agent Invariants
The agent **must**:
- Understand user intent accurately.
- Determine whether a tool is required before acting.
- Select **only** registered, approved tools.
- Generate valid, structured JSON arguments adhering to the tool schema.
- Execute tools through established backend service boundaries.
- Observe real tool execution results.
- Synthesize truthful final responses directly reflecting actual tool outcomes.

The agent must **NEVER**:
- Fabricate or simulate tool results.
- Claim success when a tool execution failed or threw an error.
- Execute arbitrary Python scripts, shell commands, or operating system subprocesses.
- Access the host filesystem outside approved logging/runtime operations.
- Bypass authentication or user ownership validation.
- Directly query or modify Cloud Firestore outside approved `TaskService` boundaries.

---

## 9. Authentication & Token Verification Rules

- **Identity Provider:** Use **Firebase Authentication** for user accounts (email/password, Google OAuth).
- **ID Token Verification:** Every protected request to the FastAPI backend must present a valid Firebase ID token in the `Authorization: Bearer <token>` header.
- **Verification Chain:**
  ```text
  Client Login (Firebase Auth)
         ↓
  Client transmits Firebase ID Token (JWT)
         ↓
  FastAPI Dependency verifies token via Firebase Admin SDK
         ↓
  Identity derived: user_id = decoded_token["uid"]
         ↓
  Backend authorizes request for user-scoped resource
  ```
- **Never Trust Client-Supplied Identity:** The backend must **never** trust a `user_id` passed in the request body, path parameter, or query string for authorization. Identity is derived solely from the cryptographically verified token.

---

## 10. Database & Firestore Security Rules

- **Database Engine:** **Cloud Firestore**.
- **Preferred Document Path:**
  ```text
  users/{user_id}/tasks/{task_id}
  ```
- **User-Scoped Isolation:** Every task document must be nested under the authenticated user's ID to enforce structural multi-tenant isolation.
- **No Cross-User Access:** Users must never be able to read, create, update, or delete tasks belonging to another user.
- **Defense in Depth:** Clearly distinguish and enforce:
  1. **Firebase Authentication:** Client identity verification.
  2. **Backend Authorization:** Server-enforced ownership verification inside `TaskService`.
  3. **Firestore Security Rules:** Direct database security rules enforcing `request.auth != null && request.auth.uid == userId`.

---

## 11. LLM Model Strategy & Provider Abstraction

- **Runtime Agent Model:** **Nemotron** is designated as the initial runtime LLM for the agent loop and structured tool-calling phases (Phases 6–8, 10).
- **Provider Abstraction:** Never hard-code Nemotron or any specific vendor throughout the codebase. The LLM connection must be mediated through an abstract `LLMService` governed by standardized environment variables:
  ```env
  LLM_PROVIDER=
  LLM_MODEL=
  LLM_API_KEY=
  ```
- **Role of Google AI Studio:** Google AI Studio was used as an early development and UI generation tool. It is **NOT** the production runtime model for TaskMate.
- **No Vendor Lock-in:** Do not require provider-specific variables (e.g., `GEMINI_API_KEY`) as mandatory architectural rules for the production backend.

---

## 12. Google Colab Experimentation Rules

- **Validation Sandbox:** Google Colab notebooks (`notebooks/01_*.ipynb` through `07_*.ipynb`) are dedicated to isolated experimentation: testing model connections, verifying prompt templates, exercising tool-calling schemas, validating Firebase Admin keys, and testing end-to-end user flows.
- **Not a Production Runtime:** Colab notebooks must never be treated as production servers or hosting environments.
- **Production Code Placement:** All production-ready logic must be migrated to `backend/app/`, `frontend/src/`, and `firebase/`.
- **Zero Secrets in Notebooks:** Never commit notebooks containing hardcoded API keys, private keys, or service account JSON credentials.

---

## 13. REST API Design Rules

- **Approved Core Endpoints:**
  - `GET /health`: Public health check and uptime probe.
  - `POST /api/chat`: Protected primary conversational endpoint powering the agent loop.
- **No Unapproved Public Endpoints:** Internal tools (Calculator, Date/Time, Task CRUD) are executed internally by the agent loop. Do not expose them as public REST routes unless explicitly approved in architecture documentation.
- **Standardized API Contracts:** Every API endpoint must have:
  - Clear Pydantic request and response schemas.
  - Input validation with descriptive 422 error details.
  - Bearer token authentication on protected endpoints.
  - Predictable HTTP status codes (`200 OK`, `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `500 Internal Error`).
  - Sanitized error responses that never leak backend internals.

---

## 14. Frontend / Backend Security Boundary

- **Zero Secrets in Frontend:** The client bundle (`frontend/` or `src/`) must **NEVER** contain:
  - LLM API keys (`LLM_API_KEY`, Nemotron keys, etc.)
  - Firebase Admin SDK service account credentials or private keys
  - Database master credentials
  - Backend internal environment variables
- **Public Client Variables:** Only intentionally public client configurations (e.g., `VITE_FIREBASE_API_KEY`, `VITE_FIREBASE_PROJECT_ID`) may be exposed in frontend environment files.
- **Backend Responsibility:** All privileged operations (database modifications, tool executions, AI model requests) must execute on the backend.
- **Never Rely on UI Hiding:** Disabling or hiding UI buttons is purely a user experience convenience; security must always be enforced on the backend.

---

## 15. UI/UX Consistency Rules

TaskMate delivers a modern, focused, and intuitive productivity experience:

- **Visual Consistency:** Maintain uniform typography, padding, card borders, and brand accents using Tailwind utility classes.
- **Neutral Palette:** Soft warm/slate neutrals (`bg-stone-50`, `bg-white`, `border-stone-200`) paired with purposeful primary accents (`indigo-600`).
- **Semantic Status Colors:**
  - *Completed / Success*: Emerald
  - *In Progress / Warning*: Amber
  - *High Priority / Error*: Rose
  - *Pending / Low Priority*: Stone / Slate
- **Consumer Focus:** Do not introduce enterprise administration consoles, billing dashboards, or raw telemetry views into the primary user interface.
- **State Feedback:** Every view must provide clean loading states (skeletons), empty states (actionable illustrations), and clear error states.

---

## 16. Purposeful Micro-Animations

- **Subtle & Meaningful:** Use micro-interactions to enhance user feedback without causing distraction or performance degradation.
- **Approved Animations:**
  - Interactive hover and focus transitions on cards and buttons.
  - Message bubble entry animations.
  - AI thinking / processing indicator.
  - Task completion checkbox toggle animation.
  - Modal and toast slide/fade transitions.
  - Skeleton loading pulses.
- **Avoid Excess:** Never prioritize decorative animation over responsiveness, usability, or accessibility.

---

## 17. Accessibility (a11y) Standards

- **Semantic HTML:** Use proper HTML5 elements (`<header>`, `<main>`, `<nav>`, `<section>`, `<button>`, `<h1>`-`<h3>`).
- **Keyboard Navigation:** All interactive elements must be reachable and operable via the `Tab` and `Enter`/`Space` keys.
- **Focus Rings:** Ensure visible, high-contrast focus rings (`focus:ring-2 focus:ring-indigo-500`).
- **Aria Labels:** Provide `aria-label` attributes on icon-only buttons.
- **Color Independence:** Never rely solely on color to convey status; always pair colors with text labels or distinct icons.

---

## 18. Error Handling & Customer Sanitization

- **Never Swallow Errors Silently:** Always catch, log, and handle exceptions appropriately.
- **Mask Server Internals:** User-facing error messages must be friendly, clear, and actionable. **Never expose**:
  - Python or Node stack traces
  - File system paths
  - Database error details
  - API keys or tokens
  - Internal prompt templates or model internals
- **No Fabricated Success:** If an agent tool fails, the agent must acknowledge the failure honestly and inform the user rather than claiming success.

---

## 19. Logging & Observability Rules

- **Structured Diagnostic Logs:** Backend logs should record structured context for debugging:
  - `request_id`
  - `operation`
  - `tool_name`
  - `latency_ms`
  - `status` (`success` | `error`)
  - Authenticated `user_id`
- **Zero Sensitive Data in Logs:** Never log:
  - Passwords or credentials
  - API keys or private keys
  - Firebase ID tokens or authorization headers
  - Full private user message content unnecessarily

---

## 20. State Management & Single Source of Truth

- **Single Source of Truth:** Task state must be centralized (e.g., in `AppContext`).
- **Derived Metrics:** Dashboard and summary counts must be computed directly from the canonical task collection:
  ```typescript
  const total = tasks.length;
  const completed = tasks.filter(t => t.status === 'completed').length;
  const pending = tasks.filter(t => t.status === 'pending').length;
  ```
  Never hard-code separate, inconsistent counters.
- **Optimistic Updates with Rollback:** Optimistic UI updates are allowed for immediate user feedback, but if the backend network request fails, the state **must be rolled back** to its previous snapshot and the user notified via toast.

---

## 21. Git Commit & Repository Cleanliness Rules

- **Conventional Commits:** All git commit messages must follow the Conventional Commits specification:
  - `feat:` New user-facing feature or backend capability.
  - `fix:` Bug fix in code or logic.
  - `docs:` Documentation updates (`decisions.md`, `rules.md`, `memory.md`, PRD).
  - `refactor:` Code refactoring without changing functionality.
  - `test:` Adding or updating test suites.
  - `chore:` Dependency updates, configurations, build tooling.
- **Subject Length:** Keep commit messages concise, preferably under **72 characters**.
- **Never Commit Secrets:** Never commit:
  - `.env` files
  - API keys or credentials
  - Service account JSON files
  - Build output directories (`dist/`, `build/`)
  - Node or Python dependency directories (`node_modules/`, `__pycache__/`, `.venv/`)

---

## 22. Environment Variable Management Rules

- **Maintain `.env.example`:** Every new environment variable introduced must be documented with a placeholder string in `.env.example`.
- **Never Commit `.env`:** Ensure `.env` is listed in `.gitignore`.
- **Centralized Configuration:** Read environment variables through centralized config modules (`backend/app/core/config.py` using Pydantic `BaseSettings`).
- **Segregation of Scope:**
  - Frontend: Only public `VITE_` variables.
  - Backend: Private secrets stored strictly server-side.

---

## 23. Dependency Management Rules

Before introducing a new external library:
1. Check whether existing libraries or standard library modules (`math`, `datetime`, `ast`) already solve the problem.
2. Confirm the dependency is strictly necessary for the current phase.
3. Prefer stable, well-maintained, and focused libraries.
4. Avoid duplicate libraries serving overlapping functions.
5. Update `requirements.txt` / `package.json` immediately.
6. Verify builds and run regression tests.

---

## 24. Database Access & Tool Service Boundary

- **Service Layer Ownership:** All Firestore operations must execute through the dedicated task service (`backend/app/services/task_service.py`).
- **No Direct Component Calls:** Do not scatter Firestore queries across UI components, routes, or unrelated modules.
- **Tool Flow:**
  ```text
  Agent
    ↓
  Task Tool (tools/task_tool.py)
    ↓
  Task Service (services/task_service.py)
    ↓
  Cloud Firestore (users/{user_id}/tasks/{task_id})
  ```

---

## 25. Persistent Documentation Synchronization

Engineering work must keep project documentation synchronized:

| Document | When to Update |
| :--- | :--- |
| **`decisions.md`** | Whenever an architectural or product decision is made, refined, or superseded. |
| **`memory.md`** | Whenever durable project state, tech stack, API contracts, or completed features change. |
| **`changelog.md`** | Whenever meaningful features, bug fixes, or architectural changes are completed. |
| **`05_PROGRESS.md`** | Whenever a development phase is completed and verified against acceptance criteria. |
| **`01_PRD.md` / `03_PHASES.md`** | Only if authoritative product scope or phase requirements are officially modified. |

---

## 26. Architectural Decision Preservation Rule

- **Do Not Silently Override Decisions:** Never override an accepted Architectural Decision Record without a documented reason.
- **Protocol for Changes:**
  1. Document the problem and the reason for change.
  2. Record realistic alternatives considered.
  3. Create the new accepted decision in `decisions.md`.
  4. Explicitly mark the previous decision as `Superseded` with a cross-reference.

---

## 27. Current vs. Historical Prototype Code

- **Distinguish Prototype from Architecture:** TaskMate contains early exploratory code (e.g., `server.ts` Node/Express host). The AI must distinguish between historical prototype code and the approved target architecture (Python/FastAPI modular monolith).
- **No Premature Deletion:** Do not delete working prototype code solely because it is old.
- **Orderly Migration:** Remove or replace prototype modules only when the relevant phased milestone officially replaces them with production services.

---

## 28. Comprehensive Testing Rules

- **Backend Testing (`pytest`):**
  - Unit tests for tools (`test_calculator.py`, `test_datetime_tool.py`).
  - Unit tests for task services and validation schemas.
  - Agent intent and tool selection tests.
  - API endpoint tests using FastAPI `TestClient`.
  - Integration tests for end-to-end task workflows.
- **Frontend Testing:**
  - Component rendering and interaction tests.
  - AppContext state transition and rollback tests.
- **Regression Testing:** Run tests after every meaningful modification before marking a task complete.

---

## 29. Security & Correctness Priorities

When trade-offs arise during development, adhere to these non-negotiable priorities:

1. **Security vs. Convenience:** **SECURITY WINS.**
2. **Correctness vs. Speed:** **CORRECTNESS WINS.**
3. **Approved Architecture vs. Temporary Shortcut:** **APPROVED ARCHITECTURE WINS.**

---

## 30. Pre-Completion AI Checklist

Before declaring any engineering task or phase step complete, verify:

- [ ] Current phase confirmed; no future-phase code written.
- [ ] Existing repository inspected; working functionality preserved.
- [ ] Code strictly follows folder boundaries (`backend/app/`, `frontend/src/`).
- [ ] Python 3.11+ type annotations and Pydantic validation enforced.
- [ ] TypeScript strict mode active with zero compilation errors.
- [ ] Safe evaluation enforced (zero `eval()`, zero `exec()`).
- [ ] Agent operates within approved tool boundary (`Calculator`, `Date/Time`, `Task`).
- [ ] No tool results fabricated; honest failure reporting verified.
- [ ] Authentication and user-scoped data isolation enforced (`users/{user_id}/tasks/{task_id}`).
- [ ] Zero secrets committed in source control or client bundles.
- [ ] Automated tests added or updated, and regression tests executed.
- [ ] Clean error handling without stack trace or key leakage.
- [ ] UI remains consistent with modern productivity design standards.
- [ ] `decisions.md` updated if architectural decisions were made.
- [ ] `memory.md` updated if durable state or features changed.
- [ ] `changelog.md` updated for meaningful user-facing or architectural changes.
- [ ] `05_PROGRESS.md` updated if a phase milestone was completed.

---

## 31. Guiding Philosophy: Deliberate Evolution

TaskMate evolves deliberately. Every engineering change must optimize in this exact priority order:

$$\text{Correctness} \longrightarrow \text{Security} \longrightarrow \text{Maintainability} \longrightarrow \text{Regression Safety} \longrightarrow \text{Testability} \longrightarrow \text{Simplicity} \longrightarrow \text{Performance}$$

Do not introduce complexity without an explicit, documented architectural justification.
