# TaskMate — Product Requirements Document (PRD)

**Version:** 1.0  
**Status:** Draft / Implementation Ready  
**Project Type:** AI-powered task management application  
**Primary Goal:** Build a small, practical Agentic AI application that can understand user requests, decide when tools are needed, execute those tools, and return useful results.

---

## 1. Product Overview

TaskMate is an AI-powered task management application that allows users to manage tasks using normal natural-language messages.

Instead of forcing users to use many forms and buttons, TaskMate allows requests such as:

- "Create a task to study Python tomorrow."
- "Show my pending tasks."
- "What is today's date?"
- "I have 20 chapters and 5 days. How many chapters should I study each day?"
- "Delete my task 'Complete assignment'."

The application uses an AI Agent that can understand the request and select an appropriate tool.

### Core idea

```text
User
  ↓
React Frontend
  ↓
FastAPI Backend
  ↓
AI Agent
  ↓
Understand request
  ↓
Decide whether a tool is required
  ↓
Call appropriate tool
  ↓
Get result
  ↓
Generate final response
  ↓
Frontend
```

Firebase is used for user authentication and task data storage.

---

# 2. Problem Statement

Traditional task management applications require users to manually navigate screens, enter task information, select dates, and perform separate operations for viewing or deleting tasks.

Users should be able to interact with their task manager using simple natural language. The system should understand the request, identify the required operation, use the correct tool, and provide a clear response.

The project therefore aims to demonstrate a practical Agentic AI workflow while keeping the application small, understandable, testable, and suitable for learning.

---

# 3. Product Vision

Build a simple AI task assistant that demonstrates the complete basic agent workflow:

```text
Understand
    ↓
Reason / Decide
    ↓
Select Tool
    ↓
Execute Tool
    ↓
Observe Result
    ↓
Respond
```

TaskMate is not intended to be a general-purpose autonomous AI system. Its first version focuses on reliable task management and a small set of useful tools.

---

# 4. Target Users

### Primary Users

- Students
- Individual users
- Beginners who want simple task management
- Users who prefer natural-language interaction

### Project Audience

The application is also designed as a learning project demonstrating:

- Agentic AI
- LLM integration
- Tool calling
- FastAPI
- React
- Firebase
- Testing
- API integration

---

# 5. Product Goals

## 5.1 Main Goals

1. Provide a simple AI chat interface for task management.
2. Demonstrate a real Agent + Tool workflow.
3. Allow authenticated users to create, read, update, and delete their own tasks.
4. Use Firebase for authentication and persistent task storage.
5. Provide calculator and date/time tools.
6. Expose the agent through a FastAPI backend.
7. Connect the backend with a React frontend.
8. Maintain a clean architecture that can be extended later.

## 5.2 Success Criteria

The first complete version should allow a user to:

- Sign in.
- Create a task using natural language.
- View tasks using natural language.
- Update a task.
- Delete a task.
- Ask the current date/time.
- Perform a simple calculation through the calculator tool.
- Receive a clear response from the agent.
- Access only their own task data.
- Use the application through the React interface.

---

# 6. Scope

## 6.1 In Scope — Version 1

### User Authentication

- User registration/sign-in using Firebase Authentication.
- User session handling.
- Sign-out.
- Authentication state available to the frontend.
- Backend requests associated with the authenticated user.

### Task Management

Task fields:

```text
id
user_id
title
description
due_date
priority
status
created_at
updated_at
```

Supported task operations:

- Create task
- List tasks
- Get task details
- Update task
- Mark task as completed
- Delete task

### AI Agent

The agent should:

- Understand natural-language requests.
- Decide whether a tool is required.
- Select the correct tool.
- Pass structured arguments to the tool.
- Use tool results to produce the final response.
- Avoid calling unnecessary tools.
- Return a clear answer when no tool is required.
- Handle invalid or incomplete requests safely.

### Tools

Version 1 tools:

1. Calculator Tool
2. Date/Time Tool
3. Task Tool

### Frontend

- Login/sign-up interface.
- Main TaskMate chat interface.
- Task list/dashboard.
- Basic loading states.
- Error messages.
- Task completion status.
- Responsive layout.

### Backend

- FastAPI server.
- Authentication verification.
- Agent service.
- Tool layer.
- Firebase service layer.
- API request/response models.
- Error handling.
- Logging suitable for development.

### Storage

Firebase:

- Firebase Authentication for users.
- Cloud Firestore for task data.

---

# 7. Out of Scope — Version 1

The following should NOT be implemented in the first version:

- Multi-agent architecture.
- Complex autonomous planning.
- Voice assistant.
- Image understanding.
- Email sending.
- Calendar synchronization.
- WhatsApp/Telegram integration.
- Payment systems.
- Advanced recommendation systems.
- Long-term autonomous memory.
- Complex RAG pipelines.
- Fine-tuning an LLM.
- Background autonomous agents.
- Large-scale workflow automation.

These can be considered future extensions.

---

# 8. Functional Requirements

## FR-01 — User Registration

The system shall allow a new user to create an account using supported Firebase Authentication methods.

## FR-02 — User Login

The system shall allow an existing user to sign in.

## FR-03 — User Logout

The system shall allow the user to sign out securely.

## FR-04 — Create Task

The system shall create a task containing at minimum a title and user ownership.

Example:

```text
User:
Create a task called "Complete Python assignment".

Agent:
Understands intent
↓
Task Tool
↓
Create task
↓
Confirmation
```

## FR-05 — List Tasks

The system shall return tasks belonging only to the authenticated user.

Example:

```text
User:
Show my pending tasks.

Agent
↓
Task Tool
↓
Firestore
↓
Pending tasks
```

## FR-06 — Update Task

The system shall allow supported task fields to be updated.

Example:

```text
Change the priority of "Complete assignment" to high.
```

## FR-07 — Complete Task

The system shall allow a task to be marked completed.

## FR-08 — Delete Task

The system shall allow a user to delete their own task.

## FR-09 — Calculator

The calculator tool shall support safe basic arithmetic required by the application.

Examples:

```text
20 / 5
15 + 10
100 * 0.2
```

The tool must not execute arbitrary operating-system commands or unsafe code.

## FR-10 — Date/Time

The date/time tool shall provide current date/time information needed for task interpretation.

Examples:

```text
What is today's date?
What day is tomorrow?
```

## FR-11 — Agent Tool Selection

The agent shall determine whether a request requires:

- no tool,
- calculator tool,
- date/time tool,
- task tool.

## FR-12 — Tool Arguments

The agent shall send structured arguments to tools.

Example:

```json
{
  "title": "Study Python",
  "due_date": "2026-09-12",
  "priority": "medium"
}
```

## FR-13 — Final Response

After tool execution, the agent shall generate a concise user-facing response.

## FR-14 — Error Handling

The system shall return understandable errors when:

- Authentication is invalid.
- A required task does not exist.
- Input is invalid.
- Tool execution fails.
- Firebase is unavailable.
- LLM communication fails.
- The request cannot be understood.

## FR-15 — Ownership

A user shall only be able to read or modify their own tasks.

---

# 9. Non-Functional Requirements

## NFR-01 — Usability

The application should be simple enough for a first-time user to understand without documentation.

## NFR-02 — Performance

Normal task operations should respond quickly under development/demo workloads.

## NFR-03 — Reliability

The system should handle common errors without crashing the entire application.

## NFR-04 — Maintainability

Business logic, agent logic, tools, Firebase access, and API routes should remain separated.

## NFR-05 — Security

- Firebase Authentication shall be used for identity.
- Backend requests shall verify authentication.
- Task access shall be restricted by authenticated user identity.
- Secrets shall be stored in environment variables or secure configuration.
- `.env` files containing secrets shall not be committed to GitHub.
- Client-side keys that Firebase intentionally exposes must still be protected by correct Firebase security rules and backend authorization design.

## NFR-06 — Testability

Important tools, services, agent behavior, and API endpoints shall have automated tests.

## NFR-07 — Extensibility

The architecture should allow additional tools to be added without rewriting the complete agent.

---

# 10. Agent Requirements

## 10.1 Agent Responsibilities

The agent is responsible for:

1. Understanding the user's request.
2. Identifying the user's intent.
3. Determining whether tool use is necessary.
4. Selecting one or more approved tools.
5. Preparing structured tool arguments.
6. Executing the tool through the backend.
7. Reading the tool result.
8. Producing the final response.

## 10.2 Agent Must Not

The agent must not:

- Directly manipulate the database without going through approved services/tools.
- Access another user's data.
- Execute arbitrary Python or shell commands.
- Invent successful tool results.
- Claim that an operation succeeded when the tool failed.
- Modify application architecture without approval.
- silently implement future project phases.

## 10.3 Example Agent Flow

```text
User:
Create a high priority task "Study AI" for tomorrow.

             ↓

        Agent receives request

             ↓

       Detect task creation

             ↓

       Date/Time Tool
       ↓
       Determine tomorrow

             ↓

         Task Tool
       ↓
    Create task in Firestore

             ↓

       Tool result received

             ↓

       Agent response

             ↓

Task created successfully for tomorrow.
```

---

# 11. Tool Specifications

## 11.1 Calculator Tool

### Purpose

Perform safe arithmetic calculations.

### Example Interface

```python
calculate(expression: str) -> float
```

### Supported Examples

```text
20 + 5
20 / 5
100 * 0.15
(10 + 5) * 2
```

### Restrictions

Do not use unrestricted `eval()`.

The implementation must parse or safely evaluate only supported arithmetic expressions.

---

## 11.2 Date/Time Tool

### Purpose

Provide current date/time information for agent reasoning.

### Example Functions

```python
get_current_date()
get_current_datetime()
```

Possible supported operations:

- Today
- Tomorrow
- Yesterday
- Date formatting
- Basic date interpretation

---

## 11.3 Task Tool

### Purpose

Perform task operations against Firestore.

Possible operations:

```text
create_task
list_tasks
get_task
update_task
complete_task
delete_task
```

All operations must receive the authenticated user's identity.

---

# 12. Firebase Requirements

Firebase will be used instead of building a separate database layer for Version 1.

## 12.1 Firebase Authentication

Use Firebase Authentication for:

- Account creation
- Login
- Logout
- User identity

The frontend obtains the authenticated user's Firebase ID token.

The backend verifies the token before protected operations.

## 12.2 Cloud Firestore

Cloud Firestore stores task documents.

Recommended logical structure:

```text
tasks
 ├── task_document_1
 │    ├── user_id
 │    ├── title
 │    ├── description
 │    ├── due_date
 │    ├── priority
 │    ├── status
 │    ├── created_at
 │    └── updated_at
 │
 ├── task_document_2
 └── ...
```

The implementation may use a user-subcollection structure instead if it provides cleaner authorization and querying.

The final structure must be documented in the architecture file.

## 12.3 Firebase Security

Firestore access rules must prevent one authenticated user from reading or modifying another user's task documents.

Authentication and authorization must not depend only on hiding UI elements.

---

# 13. API Requirements

The FastAPI backend should expose a small and understandable API.

### Health

```text
GET /health
```

### Agent Chat

```text
POST /api/chat
```

Example request:

```json
{
  "message": "Show my pending tasks"
}
```

Example response:

```json
{
  "response": "You have 3 pending tasks.",
  "tool_used": "task_tool"
}
```

The exact schema may be refined in `02_ARCHITECTURE.md`.

### Authentication

Protected endpoints must verify the Firebase ID token.

The backend must derive the user identity from the verified token rather than trusting a user ID supplied freely by the client.

---

# 14. Frontend Requirements

The frontend will use React.

Recommended screens:

## 14.1 Authentication Screen

- Sign in
- Sign up
- Logout
- Authentication errors

## 14.2 Main Chat Screen

Components:

```text
Header
  ↓
TaskMate title
  ↓
Chat messages
  ↓
Input box
  ↓
Send button
```

## 14.3 Task Dashboard

Display:

- Task title
- Due date
- Priority
- Status
- Completion state
- Basic actions

The dashboard is a convenience interface. The AI chat remains the main demonstration of agent functionality.

---

# 15. User Experience Requirements

The user should receive immediate visual feedback for:

- Loading
- Sending message
- Successful task creation
- Successful task update
- Successful task deletion
- Authentication errors
- API errors

The interface should avoid technical error messages such as raw stack traces.

Example:

Instead of:

```text
FirestoreException: PERMISSION_DENIED
```

Show:

```text
Sorry, I could not access your tasks. Please try again.
```

Development logs may contain detailed technical information.

---

# 16. Data Validation

Task input shall be validated before storage.

### Title

- Required
- Non-empty
- Reasonable maximum length

### Description

- Optional
- Reasonable maximum length

### Priority

Allowed values:

```text
low
medium
high
```

### Status

Allowed values:

```text
pending
completed
```

### Due Date

- Must be a valid date when supplied.
- Natural-language dates should be converted to a consistent stored format.

---

# 17. Error Handling Strategy

Errors should be handled at multiple levels.

```text
Frontend
   ↓
API
   ↓
Agent
   ↓
Tool
   ↓
Firebase / External LLM
```

Each layer should:

1. Detect failure.
2. Log useful development information.
3. Return a safe error.
4. Avoid exposing secrets or internal stack traces to the user.

The agent must not fabricate a successful result after a failed tool call.

---

# 18. Security Requirements

Minimum security controls:

- Firebase Authentication.
- Firebase ID token verification on the backend.
- User-scoped Firestore queries.
- Firestore security rules.
- No secrets committed to GitHub.
- `.env` included in `.gitignore`.
- `.env.example` contains only placeholder values.
- API validation through Pydantic/FastAPI models.
- No arbitrary code execution through calculator input.
- No shell-command execution by the agent.
- Avoid logging access tokens, secrets, or sensitive user content unnecessarily.

---

# 19. Technology Constraints

The implementation should remain simple.

## Frontend

- React
- JavaScript or TypeScript
- Stitch for UI/design support
- Google AI Studio may be used to generate/refine frontend code
- GitHub for version control

## Backend

- Python
- FastAPI
- Pydantic

## AI

- LLM accessed through a suitable supported API/model.
- Hugging Face may be used where appropriate, but it is not mandatory for the first working agent.
- The design must keep the model provider replaceable.

## Database / Authentication

- Firebase Authentication
- Cloud Firestore

## Testing

- Pytest for backend tests
- Frontend testing framework may be selected during architecture planning.

## Development Tools

- VS Code / Antigravity
- Git
- GitHub
- Python virtual environment

---

# 20. Environment Variables

Secrets and configuration must be externalized.

Example:

```env
LLM_API_KEY=
LLM_MODEL=
FIREBASE_PROJECT_ID=
FIREBASE_CLIENT_EMAIL=
FIREBASE_PRIVATE_KEY=
```

The exact Firebase configuration approach may be adjusted according to the selected Firebase Admin SDK setup.

Rules:

- Never commit production secrets.
- `.env` must be ignored by Git.
- `.env.example` must be committed with placeholders.
- Required environment variables must be documented in `README.md`.

---

# 21. Project Structure Requirement

The project should follow a clean separation similar to:

```text
TaskMate/
│
├── docs/
│   └── 01_PRD.md
│
├── frontend/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── agent/
│   │   ├── tools/
│   │   ├── services/
│   │   ├── models/
│   │   └── api/
│   │
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
│
├── tests/
│
├── .gitignore
└── README.md
```

The exact structure will be finalized in `02_ARCHITECTURE.md`.

---

# 22. Testing Requirements

Testing shall be introduced during development rather than only at the end.

## Unit Tests

Test:

- Calculator tool
- Date/time tool
- Task service
- Input validation

## Agent Tests

Test examples:

```text
Create task request
List tasks request
Delete task request
Calculator request
Date request
Normal conversational request
Unknown request
Invalid task request
```

## API Tests

Test:

- Health endpoint
- Chat endpoint
- Authentication failure
- Valid authenticated request
- Invalid request body
- Tool failure handling

## Integration Tests

At least one end-to-end flow should be tested:

```text
Frontend/API
   ↓
Agent
   ↓
Task Tool
   ↓
Firebase
   ↓
Result
   ↓
Response
```

---

# 23. Observability and Logging

Development logs should make it possible to understand:

```text
Request received
↓
Authenticated user
↓
Intent identified
↓
Tool selected
↓
Tool arguments
↓
Tool result
↓
Final response
```

Sensitive information must not be logged unnecessarily.

---

# 24. Acceptance Criteria

Version 1 is considered complete only when all of the following are true:

### Authentication

- User can register/sign in.
- User can sign out.
- Protected backend operations require valid authentication.

### Tasks

- User can create a task through the agent.
- User can list tasks.
- User can update a task.
- User can complete a task.
- User can delete a task.
- Task data persists in Firestore.
- Users cannot access another user's tasks.

### Tools

- Calculator works for supported arithmetic.
- Date/time tool works.
- Task tool works.

### Agent

- Agent selects the correct tool for common supported requests.
- Agent passes valid structured arguments.
- Agent uses tool results in the final answer.
- Agent does not claim success when a tool fails.

### API

- FastAPI server starts successfully.
- `/health` works.
- `/api/chat` works for authenticated requests.
- Invalid requests return controlled errors.

### Frontend

- User can log in.
- User can send a message.
- User can see the agent response.
- User can see task information.
- Loading and errors are handled clearly.

### Quality

- Automated tests pass.
- No production secrets are committed.
- README contains setup instructions.
- Architecture and implementation remain consistent with this PRD.

---

# 25. Future Scope

Possible future features:

- Multiple specialized agents.
- Calendar integration.
- Reminder notifications.
- Email integration.
- Recurring tasks.
- Voice input/output.
- Task prioritization.
- Personal productivity analytics.
- RAG-based personal knowledge.
- Long-term memory.
- Multi-step planning.
- External tool ecosystem.
- Background task automation.

Future features must not be implemented during Version 1 unless explicitly added to a later phase.

---

# 26. Product Principles

The project should follow these principles:

### Simple First

Build the smallest working agent before adding advanced frameworks.

### Tool-First Reliability

Important actions must be performed through explicit tools/services rather than hidden side effects.

### User Ownership

Every task belongs to an authenticated user.

### Transparent Execution

The system should be able to identify which tool was used during development/testing.

### Test Before Expansion

Do not add new agent capabilities until existing functionality is tested.

### Phase Discipline

Only the currently approved implementation phase should be developed.

---

# 27. Definition of Done

A feature is considered done when:

```text
Requirement implemented
        ↓
Code reviewed
        ↓
Automated tests added
        ↓
Tests passed
        ↓
Application manually verified
        ↓
Acceptance criteria satisfied
        ↓
Documentation updated
```

A feature is NOT done merely because the code was written.

---

# 28. Implementation Dependency Order

The recommended order is:

```text
1. Project setup
        ↓
2. Firebase configuration
        ↓
3. Basic data models
        ↓
4. Calculator tool
        ↓
5. Date/time tool
        ↓
6. Task service + task tool
        ↓
7. Agent
        ↓
8. FastAPI endpoints
        ↓
9. Authentication integration
        ↓
10. React frontend
        ↓
11. Frontend/backend integration
        ↓
12. Testing
        ↓
13. Security review
        ↓
14. Deployment preparation
```

The detailed execution plan belongs in `03_PHASES.md`.

---

# 29. Relationship With Other Project Documents

This PRD defines **WHAT** TaskMate should be.

Other documents will define:

```text
01_PRD.md
   ↓
WHAT are we building?

02_ARCHITECTURE.md
   ↓
HOW is it structured?

03_PHASES.md
   ↓
WHAT do we implement first, second, third?

04_AGENT_DEVELOPMENT_RULES.md
   ↓
HOW should Antigravity implement it?

05_PROGRESS.md
   ↓
WHAT has already been completed?
```

No implementation document should intentionally contradict this PRD without an explicit approved change.

---

# 30. Final Product Definition

TaskMate Version 1 is a small AI task-management application that combines:

```text
React
  +
FastAPI
  +
AI Agent
  +
Tool Calling
  +
Firebase Authentication
  +
Cloud Firestore
  +
Automated Testing
```

The most important learning outcome is not the task list itself.

The main technical outcome is demonstrating a working:

```text
Natural Language Request
        ↓
AI Agent
        ↓
Decision
        ↓
Tool Selection
        ↓
Tool Execution
        ↓
Tool Result
        ↓
AI Response
```

This forms the foundation for more advanced agentic AI projects later.
