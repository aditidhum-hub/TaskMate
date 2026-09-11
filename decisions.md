# TaskMate — Architectural & Product Decisions (ADR)

This document serves as the authoritative, permanent architectural decision log for **TaskMate**. It records the context, reasoning, trade-offs, and current status of every significant technical and product decision, ensuring consistent long-term context for AI coding assistants and engineering teams.

---

## Decision Index

| ID | Title | Date | Status |
| :--- | :--- | :--- | :--- |
| [ADR-001](#adr-001-modular-monolith-architecture-for-version-1) | Modular Monolith Architecture for Version 1 | 2026-09-11 | **Accepted** |
| [ADR-002](#adr-002-react-frontend-application) | React Frontend Application | 2026-09-11 | **Accepted** |
| [ADR-003](#adr-003-python-and-fastapi-backend-services) | Python and FastAPI Backend Services | 2026-09-11 | **Accepted** |
| [ADR-004](#adr-004-nemotron-as-initial-runtime-agent-model) | Nemotron as Initial Runtime Agent Model | 2026-09-11 | **Accepted** |
| [ADR-005](#adr-005-provider-agnostic-llm-configuration-and-service-abstraction) | Provider-Agnostic LLM Configuration and Service Abstraction | 2026-09-11 | **Accepted** |
| [ADR-006](#adr-006-safe-arithmetic-evaluation-no-unrestricted-eval) | Safe Arithmetic Evaluation (No Unrestricted `eval`) | 2026-09-11 | **Accepted** |
| [ADR-007](#adr-007-deterministic-datetime-resolution-tool) | Deterministic Date/Time Resolution Tool | 2026-09-11 | **Accepted** |
| [ADR-008](#adr-008-firebase-authentication-for-user-identity) | Firebase Authentication for User Identity | 2026-09-11 | **Accepted** |
| [ADR-009](#adr-009-cloud-firestore-for-persistent-task-storage) | Cloud Firestore for Persistent Task Storage | 2026-09-11 | **Accepted** |
| [ADR-010](#adr-010-user-scoped-task-data-and-server-enforced-authorization) | User-Scoped Task Data and Server-Enforced Authorization | 2026-09-11 | **Accepted** |
| [ADR-011](#adr-011-approved-agent-tool-boundaries-and-safety-guardrails) | Approved Agent Tool Boundaries and Safety Guardrails | 2026-09-11 | **Accepted** |
| [ADR-012](#adr-012-chain-of-thought-concealment-and-user-facing-status-updates) | Chain-of-Thought Concealment and User-Facing Status Updates | 2026-09-11 | **Accepted** |
| [ADR-013](#adr-013-centralized-frontend-state-management-with-rollback-on-failure) | Centralized Frontend State Management with Rollback on Failure | 2026-09-11 | **Accepted** |
| [ADR-014](#adr-014-google-colab-as-an-isolated-experimentation-and-validation-layer) | Google Colab as an Isolated Experimentation and Validation Layer | 2026-09-11 | **Accepted** |
| [ADR-015](#adr-015-strict-phase-by-phase-development-discipline) | Strict Phase-by-Phase Development Discipline | 2026-09-11 | **Accepted** |
| [ADR-016](#adr-016-graceful-error-handling-and-fallback-strategy) | Graceful Error Handling and Fallback Strategy | 2026-09-11 | **Proposed / Planned** |
| [ADR-017](#adr-017-historical-nodejs-and-express-prototype-host) | Historical Node.js and Express Prototype Host | 2026-09-11 | **Superseded** |
| [ADR-018](#adr-018-historical-google-ai-studio-prototyping-integration) | Historical Google AI Studio Prototyping Integration | 2026-09-11 | **Superseded** |
| [ADR-019](#adr-019-historical-multi-tenant-enterprise-premise) | Historical Multi-Tenant Enterprise Premise | 2026-09-11 | **Superseded** |

---

# Active Accepted Decisions

---

### ADR-001: Modular Monolith Architecture for Version 1

- **Date:** 2026-09-11
- **Status:** Accepted

#### Context / Problem
TaskMate requires a clear architectural boundary between its interactive user interface, business services, tool execution environment, and AI orchestration. We must avoid distributed systems complexity, microservices operational overhead, and premature infrastructure engineering while preserving clean internal modularity for future growth.

#### Decision Taken
For Version 1, TaskMate is structured as a **modular monolith**:
1. A dedicated **React frontend** handling graphical views, conversational chat UI, and client state.
2. A single **Python + FastAPI backend application** (`backend/app/`) containing internally decoupled modules:
   - `api/`: HTTP route handlers and dependencies.
   - `agent/`: Orchestration logic, prompts, and tool calling schemas.
   - `tools/`: Independent callable tool implementations (calculator, date/time, task tool).
   - `services/`: External integrations (Firebase Admin, LLM client, task persistence).
   - `models/`: Domain schemas and Pydantic validation entities.
   - `core/`: Configuration, security, and logging.
3. Complex microservices, Kubernetes clusters, service meshes, event buses, and distributed queues are strictly out of scope for Version 1.

#### Reasoning
- Keeps the system straightforward to develop, run locally, test, and debug.
- Avoids network serialization latency and partial network failures between internal components.
- Enforces strict interface boundaries through standard package imports, allowing modules to be extracted later if scale warrants.

#### Alternatives Considered
- **Distributed Microservices:** Unnecessary overhead, complex local orchestration, and higher operational cost for an initial product.
- **Serverless-Only Functions:** Cold-start penalties on LLM tool loops and complicated local integration testing.

#### Impact on Project
- Simplified development workflow and single backend service deployment.
- High cohesion within domain modules while avoiding premature distributed infrastructure.

---

### ADR-002: React Frontend Application

- **Date:** 2026-09-11
- **Status:** Accepted

#### Context / Problem
Users require a responsive, modern graphical interface to view, create, edit, filter, and track tasks alongside a conversational AI assistant. The interface must provide immediate visual feedback, optimistic updates, and clear status indicators without page reloads.

#### Decision Taken
The frontend is built using **React** with TypeScript, bundled via Vite, and styled using Tailwind CSS:
- Views include a unified **Workspace** (Kanban board and task creation), **Dashboard** (productivity metrics), **Tasks Panel** (search, filtering, and sorting), and **AI Assistant Panel** (chat interface).
- Communicates with the backend exclusively via standard REST JSON endpoints (`/api/chat`, `/api/health`).
- The frontend must never hold server-side secrets or direct administrative database access.

#### Reasoning
- React's component model and unidirectional data flow align naturally with task state updates and chat message streams.
- TypeScript ensures shared domain type consistency (`Task`, `TaskPriority`, `TaskStatus`, `ChatMessage`).
- Wide ecosystem support for accessible UI components and modern styling.

#### Alternatives Considered
- **Server-Side Rendered Templates (Jinja2 / Django Templates):** Sluggish interaction model for dynamic Kanban dragging and real-time conversational sidecars.
- **Next.js Full-Stack:** Adds framework-level server runtime complexity when the backend is explicitly designated as Python/FastAPI.

#### Impact on Project
- Clear separation between UI presentation in `src/` and backend logic in `backend/app/`.
- Frontend can be tested and developed independently with API contracts or mocks.

---

### ADR-003: Python and FastAPI Backend Services

- **Date:** 2026-09-11
- **Status:** Accepted

#### Context / Problem
The backend must provide reliable API routing, schema validation, asynchronous tool execution, and seamless integration with AI agent frameworks, Python data tooling, and notebook experiments.

#### Decision Taken
TaskMate's backend is implemented in **Python 3.11+** using **FastAPI** and **Pydantic**:
- Located under `backend/app/` with entry point `backend/app/main.py`.
- Uses Pydantic models for strict data validation on all incoming request bodies and tool parameters.
- Exposes standardized endpoints including `GET /api/health` and `POST /api/chat`.
- Hosts the agent loop, approved tool executions, and Firebase Admin SDK service integrations.

#### Reasoning
- Python is the primary ecosystem for modern AI/LLM libraries, notebooks, and agent frameworks.
- FastAPI provides high asynchronous performance, automatic OpenAPI documentation, and native Pydantic validation.
- Enables direct code sharing and seamless validation between Colab experimentation notebooks and the production backend.

#### Alternatives Considered
- **Node.js / Express:** Previously used in an exploratory prototype (see ADR-017), but lacks direct synergy with the Python AI ecosystem and notebook experimentation plan.
- **Django / Flask:** Flask lacks native async/Pydantic validation; Django introduces heavyweight ORM and admin boilerplate unnecessary for a Firestore-backed application.

#### Impact on Project
- Requires a Python 3.11+ runtime environment (`requirements.txt`) and standard ASGI server (e.g., Uvicorn).
- Backend team can directly leverage standard Python testing tools (`pytest`).

---

### ADR-004: Nemotron as Initial Runtime Agent Model

- **Date:** 2026-09-11
- **Status:** Accepted

#### Context / Problem
The agent loop requires an LLM with strong instruction-following capabilities, reliable tool selection, and structured argument generation. We need to clearly identify the approved runtime AI model while distinguishing development/scaffolding utilities from production runtime components.

#### Decision Taken
**Nemotron** is designated as the initial runtime and agent model for TaskMate during the LLM, tool-calling, and agent-loop implementation phases:
- Nemotron powers the agent reasoning loop: analyzing user prompts, deciding tool usage, generating structured arguments, and synthesizing final answers.
- **Clarification:** Google AI Studio / Gemini was used strictly as a development and UI generation tool during early workspace scaffolding, and is **not** the TaskMate runtime agent model.

#### Reasoning
- Nemotron provides competitive reasoning and structured function/tool-calling performance for domain-specific agent workflows.
- Establishes a concrete, tested baseline for Phase 4–7 agent implementation.

#### Alternatives Considered
- **Commercial Closed APIs (OpenAI / Anthropic):** High recurring cost, less flexible for customized open-weights evaluation in academic or private environments.
- **Small Unaligned SLMs (<3B parameters):** Unreliable structured tool calling output leading to frequent JSON parsing failures.

#### Impact on Project
- Backend LLM service must configure and test prompts against Nemotron capabilities.
- Configuration must be managed through environment variables rather than hardcoded references (see ADR-005).

---

### ADR-005: Provider-Agnostic LLM Configuration and Service Abstraction

- **Date:** 2026-09-11
- **Status:** Accepted

#### Context / Problem
While Nemotron is the approved initial runtime model, hard-coding a specific model provider or vendor SDK across the codebase creates tight coupling, hinders local testing, and complicates future model evaluations.

#### Decision Taken
Implement an abstract **LLM Service Layer** (`backend/app/services/llm_service.py`) driven by standardized environment variables:
```env
LLM_PROVIDER=
LLM_MODEL=
LLM_API_KEY=
```
- Core agent orchestration interacts only with the abstract `LLMService` interface.
- Provider-specific clients (e.g., NVIDIA NIM, OpenAI-compatible endpoints, Hugging Face) are encapsulated inside adapter classes.
- Under no circumstances should model names or endpoints be hardcoded inside business logic or tool definitions.

#### Reasoning
- Enables zero-downtime model switching via configuration updates.
- Facilitates unit testing with mock LLM responses without invoking external APIs.
- Protects the application architecture against upstream API deprecations or pricing changes.

#### Alternatives Considered
- **Direct Vendor SDK Coupling:** Faster initial setup but requires massive code refactoring if the runtime model changes.
- **Complex Multi-Provider Frameworks (LangChain / AutoGen):** Over-engineered abstractions that introduce opaque debugging layers and brittle dependency trees for V1.

#### Impact on Project
- Clean architectural boundary between agent logic and LLM provider implementations.
- Documentation must clearly describe supported environment variables in `.env.example`.

---

### ADR-006: Safe Arithmetic Evaluation (No Unrestricted `eval`)

- **Date:** 2026-09-11
- **Status:** Accepted

#### Context / Problem
Task management frequently involves numerical queries (*"I have 20 chapters to finish in 5 days, how many per day?"*). LLMs are prone to arithmetic hallucinations. However, using unrestricted dynamic execution (`eval()`, `exec()`, or `new Function()`) introduces catastrophic Remote Code Execution (RCE) vulnerabilities.

#### Decision Taken
The **Calculator Tool** must use an isolated, safe arithmetic evaluator:
- Restricts operations strictly to supported binary operators (`+`, `-`, `*`, `/`, `%`, `^`), parentheses, and safe mathematical functions (`sqrt`, `round`, `abs`, `ceil`, `floor`).
- Disallows all variable bindings, property accessors, statement executions, system calls, and global imports.
- Rejects malformed or unsafe expressions with sanitized, user-friendly error messages.

#### Reasoning
- Eliminates code injection attack surfaces completely.
- Provides reliable mathematical results to ground LLM reasoning.
- Operates deterministically with minimal computational overhead.

#### Alternatives Considered
- **Unrestricted `eval()` with regex blacklists:** Inherently flawed; string blacklists are routinely bypassed by obfuscated payloads.
- **Third-party heavy CAS libraries:** Large dependency footprint unnecessary for simple arithmetic budgeting.

#### Impact on Project
- The Calculator tool provides safe arithmetic evaluation in both the backend Python service and client-side validation utilities.

---

### ADR-007: Deterministic Date/Time Resolution Tool

- **Date:** 2026-09-11
- **Status:** Accepted

#### Context / Problem
Natural language task commands are heavily dependent on relative temporal references (*"today"*, *"tomorrow"*, *"yesterday"*, *"next Monday"*, *"in 3 days"*). Because LLMs have static knowledge cutoffs and lack internal real-time clocks, relying on the model's internal clock reasoning causes incorrect task scheduling.

#### Decision Taken
Implement a dedicated **Date/Time Tool** that resolves temporal expressions using deterministic system calendar logic:
- Queries the real-time system clock to establish ground-truth time.
- Resolves relative queries into standardized ISO-8601 date strings (`YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SSZ`) and localized human-readable labels.
- Injects current temporal context into the agent's reasoning environment.

#### Reasoning
- Guarantees consistent and accurate date calculations across all task creation and update workflows.
- Produces normalized ISO-8601 strings suitable for Firestore indexing, querying, and sorting.

#### Alternatives Considered
- **Prompting LLM with current date only:** Unreliable; models frequently miscalculate leap years, day-of-week offsets, or month boundaries.
- **Client-only local date generation:** Inconsistent when tasks are created or updated via backend API endpoints.

#### Impact on Project
- All task scheduling operations depend on the deterministic Date/Time tool for accurate temporal resolution.

---

### ADR-008: Firebase Authentication for User Identity

- **Date:** 2026-09-11
- **Status:** Accepted

#### Context / Problem
TaskMate requires authenticated user sessions to support multi-user isolation so that users access only their own tasks. Building a custom credential storage, hashing, session handling, and password reset service in Version 1 diverts effort from core agentic functionality.

#### Decision Taken
**Firebase Authentication** is selected as the identity provider for Version 1:
- Handles user registration, email/password login, OAuth providers (e.g., Google Sign-in), session tokens, and password management.
- The frontend obtains a Firebase ID token upon successful authentication.
- The backend verifies the Firebase ID token on every protected API call using the Firebase Admin SDK.

#### Reasoning
- Proven, battle-tested identity infrastructure requiring zero database user password storage.
- Standardized JWT (Firebase ID token) contains cryptographic proof of user identity.
- Clean integration with Cloud Firestore security rules.

#### Alternatives Considered
- **Custom JWT Auth with PostgreSQL:** Requires significant boilerplate (bcrypt hashing, refresh token rotation, email verification, CSRF protection).
- **OAuth-only through third-party social providers without Firebase:** Requires managing custom user session tables and token verification flows.

#### Impact on Project
- Frontend and backend must integrate standard Firebase SDKs.
- Clear separation between client authentication and backend authorization.

---

### ADR-009: Cloud Firestore for Persistent Task Storage

- **Date:** 2026-09-11
- **Status:** Accepted

#### Context / Problem
TaskMate requires a scalable, cloud-hosted document database for persisting task items and user preferences without demanding complex database migrations or relational server provisioning during initial phases.

#### Decision Taken
**Cloud Firestore** is selected as the primary database for Version 1:
- Task documents store title, description, due date, priority, status, category, and timestamps.
- Structured logically to support user isolation:
  ```text
  users/{user_id}/tasks/{task_id}
  ```
  *(Alternative top-level `tasks/{task_id}` with mandatory `user_id` field is permissible only if strictly indexed and validated).*
- Firestore indexes must be defined in `firebase/firestore.indexes.json`.

#### Reasoning
- Real-time synchronization capabilities for dynamic UI updates across multiple tabs or devices.
- Fully managed, zero server maintenance, and generous free tier for development.
- Native document security model aligned with Firebase Authentication.

#### Alternatives Considered
- **Relational SQL (PostgreSQL / SQLite):** Excellent for complex multi-table joins, but adds schema migration overhead and lacks built-in client real-time synchronization for V1.
- **MongoDB Atlas:** Similar document model but lacks seamless native integration with Firebase Authentication tokens and security rules.

#### Impact on Project
- Task data models in Python (`backend/app/models/task.py`) and TypeScript (`src/types.ts`) must mirror Firestore document structures.

---

### ADR-010: User-Scoped Task Data and Server-Enforced Authorization

- **Date:** 2026-09-11
- **Status:** Accepted

#### Context / Problem
In a multi-user application, cross-user data leakage is a critical security vulnerability. Relying solely on client-side filtering or trusting a `user_id` passed in the HTTP request body allows malicious users to view or tamper with other users' tasks.

#### Decision Taken
Strict **User-Scoped Isolation and Server-Enforced Authorization** is mandatory across the entire stack:
1. **Token Verification:** Every protected backend endpoint must extract the `Authorization: Bearer <token>` header and verify the Firebase ID token using the Firebase Admin SDK.
2. **Derived Identity:** The backend must **always derive the `user_id` directly from the verified token (`decoded_token["uid"]`)**. Under no circumstances should a `user_id` supplied in the request payload or query parameter be trusted for authorization.
3. **Firestore Security Rules:** Server-enforced Firestore rules must validate that `request.auth.uid == user_id` for all direct database access.
4. **Scope Boundary:** Version 1 focuses exclusively on individual authenticated user data. Multi-tenant organizational RBAC, tenant billing, subscription tiers, and team workspace administration are strictly out of scope for V1.

#### Reasoning
- Implements the principle of least privilege and defense-in-depth.
- Prevents Insecure Direct Object Reference (IDOR) attacks.
- Keeps V1 scope tight and focused on robust personal task management.

#### Alternatives Considered
- **Client-Side Authorization Only:** Rejected; trivial to bypass with direct curl or API requests.
- **Full Multi-Tenant Enterprise RBAC in V1:** Premature complexity that distracts from validating the agent-loop core value proposition.

#### Impact on Project
- Every backend tool execution and database query must receive the verified `user_id` context.

---

### ADR-011: Approved Agent Tool Boundaries and Safety Guardrails

- **Date:** 2026-09-11
- **Status:** Accepted

#### Context / Problem
Autonomous agents with unconstrained capabilities present major safety, stability, and security risks. An agent must never execute arbitrary shell commands, access unauthorized files, or fabricate execution results.

#### Decision Taken
The TaskMate agent operates within a strictly defined, **approved tool boundary**:
- **Approved Tools for Version 1:**
  1. `Calculator Tool`: Evaluates safe arithmetic expressions.
  2. `Date/Time Tool`: Resolves temporal expressions and returns current timestamps.
  3. `Task Tool`: Executes strictly defined CRUD operations on tasks (`create_task`, `list_tasks`, `get_task`, `update_task`, `complete_task`, `delete_task`).
- **Explicit Negative Guardrails — The Agent Must NEVER:**
  - Fabricate tool results or claim success when a tool fails.
  - Execute shell commands, terminal scripts, or arbitrary code.
  - Bypass authentication or authorization checks.
  - Access or manipulate Firestore directly outside approved service boundaries.
  - Invoke any tool not registered in the approved tool registry.

#### Reasoning
- Guarantees predictable, bounded behavior.
- Prevents prompt injection attacks from escalating into server or database compromise.
- Ensures truthful, reliable communication with the user.

#### Alternatives Considered
- **Open-Ended Agent with Code Interpreter:** High security risk, unnecessary for standard task management.
- **Unvalidated Function Execution:** Exposes backend services to unexpected runtime crashes and parameter injection.

#### Impact on Project
- The tool registry (`backend/app/agent/tool_registry.py`) must strictly whitelist and validate all tool declarations and arguments.

---

### ADR-012: Chain-of-Thought Concealment and User-Facing Status Updates

- **Date:** 2026-09-11
- **Status:** Accepted

#### Context / Problem
Agent reasoning loops produce internal monologues, intermediate tool arguments, raw JSON payloads, and stack traces. Exposing these internal mechanics directly to non-technical users creates visual noise, causes confusion, and leaks internal prompt instructions.

#### Decision Taken
Implement a strict separation between **user-facing conversational output** and **diagnostic telemetry**:
- **User-Facing UI:** Receives only friendly, concise status updates during processing:
  - *"Thinking..."*
  - *"Checking your tasks..."*
  - *"Creating your task..."*
  - Followed by the final synthesized conversational response.
- **Internal Chain-of-Thought:** Raw model thoughts, intermediate scratchpads, and prompt internals are **never** rendered in the primary user chat bubble.
- **Developer Diagnostics:** Detailed execution traces (tool name, arguments, latency in ms, status) are logged to server logs or restricted developer diagnostic views.

#### Reasoning
- Delivers a clean, professional, and trustworthy consumer user experience.
- Preserves full observability for developers without cluttering user interfaces.

#### Alternatives Considered
- **Exposing full raw reasoning streams to user:** Overwhelms users with technical jargon and intermediate reasoning artifacts.
- **Completely silent execution:** Leaves users uncertain whether their command is being processed or if the application has hung.

#### Impact on Project
- Frontend chat components render status chips while awaiting responses; backend filters diagnostic payloads from public response schemas.

---

### ADR-013: Centralized Frontend State Management with Rollback on Failure

- **Date:** 2026-09-11
- **Status:** Accepted

#### Context / Problem
Task updates originate from multiple UI surfaces (Kanban drag-and-drop, task creation modals, chat assistant commands). The UI must update immediately to feel responsive, but must also maintain consistency if backend network requests fail.

#### Decision Taken
Frontend state is managed via **centralized React Context and custom hooks** (`AppContext`, `useApp()`):
- Maintains the active task list, user session, active filters, and notification state as a single source of truth.
- Employs **optimistic updates** for common actions (e.g., toggling task completion status):
  - The UI reflects the change immediately.
  - If the backend request fails, the state **must roll back** to its previous state, and an error notification must alert the user.

#### Reasoning
- Ensures a fluid user experience without waiting for network round-trips for simple toggles.
- Guarantees eventual consistency between the client and server.
- Avoids the boilerplate of external state management libraries for Version 1 scope.

#### Alternatives Considered
- **Redux / MobX:** Excessive boilerplate for the scope of Version 1.
- **Purely Pessimistic Updates (wait for server response):** Introduces perceptible UI lag for basic interactions like checking off a checkbox.

#### Impact on Project
- All state mutations must store previous state snapshots to enable clean rollbacks upon network errors.

---

### ADR-014: Google Colab as an Isolated Experimentation and Validation Layer

- **Date:** 2026-09-11
- **Status:** Accepted

#### Context / Problem
Developing agentic workflows, prompt templates, and tool integrations benefits from iterative, cell-by-cell experimentation before committing code to the production backend. However, experimental notebooks must not become tangled with production application code.

#### Decision Taken
**Google Colab notebooks** (`notebooks/01_*.ipynb` through `07_*.ipynb`) are designated strictly as an **isolated experimentation, learning, and validation layer**:
- Notebooks are used to verify LLM connections, test prompt variations, inspect tool calling schemas, and validate Firebase connections.
- **Notebooks are NOT the production runtime.**
- Production business logic, service boundaries, and route handlers must live exclusively in `backend/app/`.

#### Reasoning
- Keeps the production repository clean, version-controlled, and testable.
- Provides a sandbox for reproducible data-driven experiments without destabilizing the application backend.

#### Alternatives Considered
- **Developing directly in production files without notebooks:** Slows down prompt iteration and LLM behavior exploration.
- **Running production backend from notebook servers:** Fragile, unversioned, and unsuitable for web application hosting.

#### Impact on Project
- Notebooks in `notebooks/` serve as educational and validation artifacts; all verified patterns must be ported cleanly to `backend/app/`.

---

### ADR-015: Strict Phase-by-Phase Development Discipline

- **Date:** 2026-09-11
- **Status:** Accepted

#### Context / Problem
AI-assisted development risks scope creep, premature optimization, and incomplete feature implementations when agents attempt to jump ahead across multiple project phases simultaneously.

#### Decision Taken
All development must follow a **strict phase-by-phase discipline** governed by `TaskMate_03_PHASES.md`:
1. Work is restricted exclusively to the currently approved phase.
2. Under no circumstances should an AI agent silently implement future phases.
3. The operational loop for every phase must be:
   $$\text{Implement} \longrightarrow \text{Test} \longrightarrow \text{Verify} \longrightarrow \text{Update Progress} \longrightarrow \text{Stop}$$
4. Explicit review and verification are required before advancing to the subsequent phase.

#### Reasoning
- Ensures high software quality, high test coverage, and complete documentation at every milestone.
- Prevents architectural regressions and unverified code buildup.

#### Alternatives Considered
- **Ad-hoc Feature Implementation:** Causes incomplete features, untracked technical debt, and broken integration points.

#### Impact on Project
- Clear progress tracking in `memory.md` and `changelog.md` mapped directly to established phase criteria.

---

# Proposed / Planned Decisions

---

### ADR-016: Graceful Error Handling and Fallback Strategy

- **Date:** 2026-09-11
- **Status:** Proposed / Planned

#### Context / Problem
External AI APIs are subject to network timeouts, rate limiting, and intermittent service degradation. An application should not crash or present unhandled exceptions when third-party services become temporarily unavailable.

#### Decision Taken
A **graceful error handling and fallback strategy** is planned for the backend agent service:
- When the LLM provider experiences timeouts or API errors, the system must catch exceptions, log telemetry, and return sanitized, helpful explanations to the user (*"The assistant is currently unable to process your request. Please try again shortly."*).
- Simple rule-based deterministic fallback responses for basic offline commands (e.g., date checks or math evaluation) may be evaluated as an optional resilience enhancement.
- **Evidence Note:** While exploratory fallback routines exist in initial frontend prototypes, a fully verified production backend fallback service in FastAPI remains **Proposed / Planned** and will be implemented and validated in Phase 5 and Phase 7.

#### Reasoning
- Protects user experience during external dependency disruptions.
- Prevents internal system details or API error bodies from leaking to the client.

#### Alternatives Considered
- **Hard failure with generic 500 error:** Poor user experience; fails to communicate actionable information.

#### Impact on Project
- Requires comprehensive unit and integration tests simulating API timeouts and network failures.

---

# Historical Superseded Decisions

---

### ADR-017: Historical Node.js and Express Prototype Host

- **Date:** 2026-09-11
- **Status:** Superseded

#### Context / Problem
During initial Phase 0/1 exploratory UI development, a Node.js Express server (`server.ts`) was set up to host the Vite development middleware and serve static assets alongside exploratory mock routes.

#### Decision Taken
An Express server was temporarily used to serve the Vite frontend and host exploratory API endpoints.

#### Superseded By
- [ADR-001: Modular Monolith Architecture for Version 1](#adr-001-modular-monolith-architecture-for-version-1)
- [ADR-003: Python and FastAPI Backend Services](#adr-003-python-and-fastapi-backend-services)

#### Supersession Reason
The authoritative architectural direction establishes **Python + FastAPI** as the production backend service (`backend/app/`) to align with the Python AI ecosystem, notebook validation workflows, and Pydantic validation requirements. The frontend runs as a standard React SPA using Vite's native development server.

---

### ADR-018: Historical Google AI Studio Prototyping Integration

- **Date:** 2026-09-11
- **Status:** Superseded

#### Context / Problem
Early frontend workspace scaffolding utilized Google AI Studio and the `@google/genai` Gemini SDK for initial rapid UI prototyping.

#### Decision Taken
Gemini Flash was tentatively wired into the initial frontend prototype script.

#### Superseded By
- [ADR-004: Nemotron as Initial Runtime Agent Model](#adr-004-nemotron-as-initial-runtime-agent-model)
- [ADR-005: Provider-Agnostic LLM Configuration and Service Abstraction](#adr-005-provider-agnostic-llm-configuration-and-service-abstraction)

#### Supersession Reason
The authoritative runtime AI model for TaskMate is **Nemotron**, abstracted behind a provider-agnostic LLM service layer. Google AI Studio was an initial prototyping/generation tool, not the production runtime agent.

---

### ADR-019: Historical Multi-Tenant Enterprise Premise

- **Date:** 2026-09-11
- **Status:** Superseded

#### Context / Problem
Early exploratory mock scripts referenced enterprise multi-tenant constructs (e.g., `tenantId`, `tenantTasks`, organization administration).

#### Decision Taken
Enterprise multi-tenancy was tentatively referenced in exploratory prototype files.

#### Superseded By
- [ADR-010: User-Scoped Task Data and Server-Enforced Authorization](#adr-010-user-scoped-task-data-and-server-enforced-authorization)

#### Supersession Reason
The approved scope of TaskMate Version 1 is strictly focused on personal task management with authenticated single-user data isolation. Multi-tenant organizational RBAC, tenant billing, and enterprise subscriptions are not approved for Version 1 and have been removed from current architectural requirements.

---

## Consistency Check

The following items represent architectural dependencies and details that remain open or pending implementation verification across the codebase:

1. **Backend Service Convergence (Phase 1–4):** The repository currently contains early prototype scaffolding in `server.ts`. As Phase 1 and Phase 4 proceed, the backend will be established under `backend/app/` (FastAPI + Pydantic) and the prototype script will be decommissioned.
2. **Firestore Collection Layout (`users/{user_id}/tasks/{task_id}` vs. Top-Level `tasks`):** While `users/{user_id}/tasks/{task_id}` is preferred for natural isolation, the exact query patterns for date-based range filtering will be finalized and documented during Phase 3 and Phase 6 data modeling.
3. **Nemotron Provider Endpoint Integration:** The specific API endpoint format (e.g., NVIDIA NIM, local vLLM, or OpenAI-compatible endpoint) will be finalized in `backend/app/services/llm_service.py` during Phase 4 without hardcoding provider assumptions into the agent loop.
