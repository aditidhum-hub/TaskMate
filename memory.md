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

### 8.3 Pending Production Features ⏳
- **Phase 1:** Setup of `backend/` directory, Python 3.11 virtual environment, `requirements.txt`, and basic FastAPI skeleton (`backend/app/main.py`).
- **Phase 2:** Live Firebase project configuration, service account integration, and backend JWT verification dependency (`dependencies.py`).
- **Phase 3:** Python Pydantic models (`models/task.py`) and Firestore task service (`services/task_service.py`).
- **Phase 4:** Python implementations of Calculator Tool (`tools/calculator.py`) and Date/Time Tool (`tools/datetime_tool.py`).
- **Phase 5:** Python implementation of Task Tool (`tools/task_tool.py`) wiring agent actions to Firestore task service.
- **Phase 6:** Nemotron LLM connection and structured tool calling via provider-agnostic `services/llm_service.py`.
- **Phase 7:** Agent loop implementation in `agent/agent.py` orchestrating Nemotron with approved tools.
- **Phase 8:** FastAPI API layer exposing `GET /health` and `POST /api/chat` backed by the Nemotron agent loop.
- **Phase 9:** Production alignment of React frontend components to backend API contracts.
- **Phase 10:** Integration of React frontend with production FastAPI backend (`POST /api/chat`).
- **Phases 11–14:** Comprehensive Pytest/Vitest suites, security reviews, performance tuning, and production deployment.

---

## 9. Approved Phased Implementation Sequence

Development must strictly follow the sequence established in `TaskMate_03_PHASES.md`:

```text
Phase 0:  Documentation & Repository Preparation [COMPLETED]
    │
Phase 1:  Project Environment and Skeleton [NEXT UP]
    │
Phase 2:  Firebase Setup and Authentication Foundation
    │
Phase 3:  Data Models and Task Service
    │
Phase 4:  Calculator and Date/Time Tools
    │
Phase 5:  Task Tool
    │
Phase 6:  LLM Connection and Structured Tool Calling (Nemotron)
    │
Phase 7:  Agent Loop (Nemotron)
    │
Phase 8:  FastAPI API Layer (Nemotron-backed endpoint)
    │
Phase 9:  React Frontend
    │
Phase 10: Frontend + Backend Integration (React → FastAPI → Nemotron → Tools)
    │
Phase 11: Testing and Error Handling
    │
Phase 12: Security and Tenant Isolation Review
    │
Phase 13: Performance, Observability and Reliability
    │
Phase 14: Production Readiness and Deployment
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
