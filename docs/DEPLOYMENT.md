# TaskMate — Production Deployment Guide

This document is the authoritative, provider-neutral production deployment guide for **TaskMate Version 1**. It details the architecture, environment configuration, containerization, cloud deployment workflows, security hardening, and operational verification procedures.

---

## 1. System Architecture & Deployment Topology

TaskMate Version 1 is structured as a **Modular Monolith** designed for high reliability, clean security boundaries, and minimal operational overhead:

```text
[ End User Browser ]
        │
        ▼  (HTTPS)
┌─────────────────────────────────────────────────────────────┐
│  Static Hosting / CDN (e.g., Firebase Hosting, Cloud CDN)   │
│  - React 19 + Vite + TypeScript production bundle (`dist/`) │
│  - Public client assets (HTML, CSS, JS)                     │
└──────────────────────────────┬──────────────────────────────┘
                               │
            API Requests       │  Firebase Auth (Direct JWT issuance)
         (Bearer Auth Token)   │  + Firestore Client Sync
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  Container Host / PaaS (e.g., Google Cloud Run, AWS, VPS)   │
│  - Python 3.11+ FastAPI backend (`backend/app/main:app`)    │
│  - Containerized via production `Dockerfile`                │
│  - Non-root user execution, Uvicorn server                  │
│  - Structured JSON logging (`X-Request-ID`, latency)        │
│  - Sliding-window rate limiter (60 req/min on `/api/chat`) │
└──────────────┬───────────────────────────────┬──────────────┘
               │                               │
               ▼                               ▼
┌──────────────────────────────┐ ┌─────────────────────────────┐
│   Firebase Admin Services    │ │  NVIDIA Nemotron LLM API    │
│ - Cryptographic JWT verify   │ │ - OpenAI-compatible endpoint│
│ - Cloud Firestore CRUD       │ │ - Structured tool calling   │
│   `users/{uid}/tasks/{id}`   │ │ - AST math & date resolver  │
└──────────────────────────────┘ └─────────────────────────────┘
```

### Key Architectural Tenets
- **Modular Monolith**: A single backend container encapsulates the API layer, agent loop, and approved tools.
- **Provider-Neutral Design**: Deployable to any standard OCI container platform (Google Cloud Run, AWS App Runner / ECS, Azure Container Apps, or Docker VPS).
- **Decoupled Frontend**: Static assets are pre-compiled and served via global CDN edge nodes for sub-second page loads.
- **Defense in Depth**: Zero dynamic code execution (`eval`/`exec`), mandatory HTTPS, server-enforced tenant isolation, credential auto-redaction, and sliding-window rate limiting.

---

## 2. Environment Variables & Secret Management

Production environments must provide configuration through system environment variables or cloud secret managers (e.g., Google Secret Manager, AWS Secrets Manager). **Never commit real `.env` files.**

### 2.1 Backend Server-Side Configuration

| Variable | Required | Default | Security Level | Description |
|---|:---:|:---:|:---:|---|
| `ENVIRONMENT` | Yes | `development` | Public | Set to `production` in production environments. |
| `DEBUG` | Yes | `true` | Public | Set to `false` in production. |
| `HOST` | No | `0.0.0.0` | Public | Bind address for Uvicorn. |
| `PORT` | No | `8000` | Public | Port to bind. Cloud Run/PaaS dynamically injects this. |
| `CORS_ORIGINS` | Yes | `["http://localhost:5173"]` | Sensitive | JSON array or comma-separated list of allowed frontend HTTPS origins. |
| `LLM_PROVIDER` | No | `nemotron` | Public | LLM provider identifier (`nemotron`). |
| `LLM_MODEL` | No | `nvidia/nemotron-3.5-lightning-30b-a3b` | Public | Model name for agent reasoning and tool calling. |
| `LLM_BASE_URL` | No | `https://integrate.api.nvidia.com/v1` | Public | OpenAI-compatible API base URL. |
| `NVIDIA_API_KEY` | Yes | `""` | **Secret** | NVIDIA API key for Nemotron completions. |
| `LLM_TIMEOUT` | No | `30.0` | Public | Timeout in seconds for LLM invocations. |
| `LOG_LEVEL` | No | `INFO` | Public | Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `LOG_FORMAT` | No | `json` | Public | Use `json` for structured cloud observability. |
| `RATE_LIMIT_REQUESTS` | No | `60` | Public | Maximum permitted requests per window on `/api/chat`. |
| `RATE_LIMIT_WINDOW_SECONDS` | No | `60` | Public | Duration of sliding rate limit window in seconds. |
| `FIREBASE_PROJECT_ID` | Yes | `""` | Public | Firebase project ID (e.g. `taskmate-prod`). |
| `FIREBASE_CLIENT_EMAIL` | Yes* | `""` | Sensitive | Service account email (if not using ADC). |
| `FIREBASE_PRIVATE_KEY` | Yes* | `""` | **Secret** | RSA private key (PEM string, with `\n` escaping). |
| `GOOGLE_APPLICATION_CREDENTIALS` | Alt* | `""` | Sensitive | Path to mounted service account JSON (alternative to env vars). |

*\* Note: On Google Cloud Run or GCE with an attached service account that has Firestore access, Application Default Credentials (ADC) are discovered automatically, making `FIREBASE_CLIENT_EMAIL` and `FIREBASE_PRIVATE_KEY` optional.*

### 2.2 Frontend Client-Side Configuration (`frontend/.env.production`)

Frontend variables are baked into static JavaScript bundles at build time. **Only public configuration is permitted.**

| Variable | Required | Sample Production Value | Description |
|---|:---:|---|---|
| `VITE_API_BASE_URL` | Yes | `https://api.taskmate.example.com` | Base HTTPS URL of production FastAPI backend. |
| `VITE_FIREBASE_API_KEY` | Yes | `AIzaSy...` | Firebase Web API key (public identifier). |
| `VITE_FIREBASE_AUTH_DOMAIN` | Yes | `taskmate-prod.firebaseapp.com` | Firebase Authentication domain. |
| `VITE_FIREBASE_PROJECT_ID` | Yes | `taskmate-prod` | Firebase project ID. |
| `VITE_FIREBASE_STORAGE_BUCKET` | Yes | `taskmate-prod.appspot.com` | Firebase Storage bucket. |
| `VITE_FIREBASE_MESSAGING_SENDER_ID` | Yes | `123456789012` | FCM sender ID. |
| `VITE_FIREBASE_APP_ID` | Yes | `1:123456789012:web:abcdef` | Firebase Web App ID. |

---

## 3. Containerization & Docker Operations

TaskMate provides production-grade container specifications with non-root security execution:

- **Root Dockerfile**: [`Dockerfile`](file:///d:/Project/TaskMate/Dockerfile)
- **Backend Dockerfile**: [`backend/Dockerfile`](file:///d:/Project/TaskMate/backend/Dockerfile)
- **Container Exclusions**: [`.dockerignore`](file:///d:/Project/TaskMate/.dockerignore)

### 3.1 Building the Container Image

Build from the repository root:
```bash
docker build -t taskmate-backend:latest -f Dockerfile .
```

Or build from within the `backend/` directory:
```bash
cd backend
docker build -t taskmate-backend:latest -f Dockerfile .
```

### 3.2 Testing the Container Locally

```bash
docker run -d \
  --name taskmate-backend \
  -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e DEBUG=false \
  -e NVIDIA_API_KEY="your_actual_key" \
  -e FIREBASE_PROJECT_ID="taskmate-prod" \
  -e CORS_ORIGINS='["http://localhost:5173"]' \
  taskmate-backend:latest
```

Verify liveness probe:
```bash
curl -i http://localhost:8000/health
```

Expected output:
```http
HTTP/1.1 200 OK
content-type: application/json

{"status":"ok","service":"TaskMate Backend","timestamp":"2026-09-12T22:15:00Z"}
```

---

## 4. Production Build & Validation Script

TaskMate includes automated production packaging scripts that perform end-to-end linting, unit testing, integration regression, and bundle compilation:

- **PowerShell (Windows)**: [`scripts/build_production.ps1`](file:///d:/Project/TaskMate/scripts/build_production.ps1)
- **Bash (Linux/macOS)**: [`scripts/build_production.sh`](file:///d:/Project/TaskMate/scripts/build_production.sh)

### Running the Production Build Pipeline

```powershell
# On Windows:
powershell.exe -ExecutionPolicy Bypass -File .\scripts\build_production.ps1

# On Linux / macOS:
chmod +x ./scripts/build_production.sh
./scripts/build_production.sh
```

**Verification Steps Executed by Script:**
1. Validates Node.js (18+), npm, and Python (3.11+) runtimes.
2. Runs Ruff linter on backend code (ensuring 0 errors).
3. Executes complete 211-test backend regression suite (`pytest backend/tests/`).
4. Runs frontend TypeScript verification (`npm run lint`).
5. Executes frontend test suites (Phase 9 & Phase 11 tests).
6. Compiles production assets into `frontend/dist/`.

---

## 5. Firebase & Firestore Production Setup

### 5.1 Deploying Firestore Security Rules

Deploy the verified multi-tenant isolation rules from [`firebase/firestore.rules`](file:///d:/Project/TaskMate/firebase/firestore.rules):

```bash
firebase deploy --only firestore:rules --project <your-firebase-project-id>
```

**Enforced Rules Summary:**
- `users/{userId}`: Only authenticated users whose `request.auth.uid == userId` can read/write.
- `users/{userId}/tasks/{taskId}`: Strictly restricts all read, list, create, update, and delete actions to the document owner (`request.auth.uid == userId`).
- Cross-tenant access is rejected with permission denied at the database kernel.

### 5.2 Deploying Firestore Composite Indexes

Deploy required query indexes from [`firebase/firestore.indexes.json`](file:///d:/Project/TaskMate/firebase/firestore.indexes.json):

```bash
firebase deploy --only firestore:indexes --project <your-firebase-project-id>
```

---

## 6. Cloud Deployment Targets

### Option A: Google Cloud Run (Recommended Container Target)

Google Cloud Run provides serverless container scaling, automatic HTTPS termination, integrated secret management, and zero infrastructure maintenance.

#### Step 1 — Build and Push Container Image to Artifact Registry
```bash
# Set environment variables
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"
export REPO="taskmate"
export IMAGE="taskmate-backend"

# Create repository if not already created
gcloud artifacts repositories create $REPO \
    --repository-format=docker \
    --location=$REGION \
    --description="TaskMate Docker Repository"

# Build and submit image via Cloud Build
gcloud builds submit --tag ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${IMAGE}:latest .
```

#### Step 2 — Store Secrets in Google Secret Manager
```bash
# Create and populate secrets
echo -n "your_nvidia_api_key" | gcloud secrets create nvidia-api-key --data-file=-
echo -n "your_firebase_private_key" | gcloud secrets create firebase-private-key --data-file=-
```

#### Step 3 — Deploy Backend Service to Cloud Run
```bash
gcloud run deploy taskmate-backend \
    --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${IMAGE}:latest \
    --region=$REGION \
    --platform=managed \
    --allow-unauthenticated \
    --min-instances=0 \
    --max-instances=10 \
    --memory=512Mi \
    --cpu=1 \
    --set-env-vars="ENVIRONMENT=production,DEBUG=false,LOG_FORMAT=json,RATE_LIMIT_REQUESTS=60,RATE_LIMIT_WINDOW_SECONDS=60,FIREBASE_PROJECT_ID=${PROJECT_ID},CORS_ORIGINS=['https://taskmate.example.com']" \
    --set-secrets="NVIDIA_API_KEY=nvidia-api-key:latest,FIREBASE_PRIVATE_KEY=firebase-private-key:latest"
```

#### Step 4 — Deploy Frontend to Firebase Hosting
1. In `frontend/.env.production`, set `VITE_API_BASE_URL` to the Cloud Run service URL output by Step 3.
2. Build frontend:
   ```bash
   cd frontend && npm run build
   ```
3. Deploy static assets:
   ```bash
   firebase deploy --only hosting --project ${PROJECT_ID}
   ```

---

### Option B: AWS (App Runner / ECS Fargate + S3 / CloudFront)

1. **Backend**:
   - Push container image to AWS Elastic Container Registry (ECR).
   - Deploy as an **AWS App Runner** service or ECS Fargate task.
   - Inject secrets via AWS Secrets Manager.
   - Configure health check at `/health`.
2. **Frontend**:
   - Sync `frontend/dist/` to an S3 bucket configured for static website hosting.
   - Distribute via AWS CloudFront CDN with HTTPS and TLS 1.3.

---

### Option C: Generic VPS / Docker Compose (Self-Hosted)

For deployment to a Linux VPS (Ubuntu/Debian) with Docker and Caddy/Nginx reverse proxy:

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    restart: always
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
      - HOST=0.0.0.0
      - PORT=8000
      - CORS_ORIGINS=["https://taskmate.example.com"]
      - NVIDIA_API_KEY=${NVIDIA_API_KEY}
      - FIREBASE_PROJECT_ID=${FIREBASE_PROJECT_ID}
      - FIREBASE_CLIENT_EMAIL=${FIREBASE_CLIENT_EMAIL}
      - FIREBASE_PRIVATE_KEY=${FIREBASE_PRIVATE_KEY}
      - LOG_LEVEL=INFO
      - LOG_FORMAT=json
    expose:
      - "8000"

  caddy:
    image: caddy:2-alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./frontend/dist:/srv:ro
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      - backend

volumes:
  caddy_data:
  caddy_config:
```

```caddyfile
# Caddyfile (Automatic Let's Encrypt HTTPS)
taskmate.example.com {
    encode gzip zstd

    # Route API and health endpoints to backend container
    handle /api/* {
        reverse_proxy backend:8000
    }
    handle /health {
        reverse_proxy backend:8000
    }

    # Serve static frontend SPA
    handle {
        root * /srv
        try_files {path} /index.html
        file_server
    }
}
```

---

## 7. Security & Hardening Checklist

Before going live in production, verify each item:

- [x] **No Secrets Committed**: Verified via Git history and `.gitignore`.
- [x] **Zero Dynamic Execution**: Strict AST arithmetic evaluation (`ast.parse`) with zero `eval()` / `exec()`.
- [x] **Strict Authentication**: All conversational agent queries (`POST /api/chat`) require valid cryptographic Firebase ID tokens. Unauthenticated requests receive HTTP 401.
- [x] **Strict Authorization & Tenant Isolation**: Database access scoped exclusively to authenticated `user_id`. Client/LLM-supplied IDs are stripped.
- [x] **Rate Limiting Active**: 60 requests/minute per client on `/api/chat` returns HTTP 429 Too Many Requests and `Retry-After`.
- [x] **Diagnostic Sanitization**: Unhandled exceptions return generic 500 errors; internal traces and file paths are never exposed to clients.
- [x] **Credential Redaction in Logs**: Sensitive keys (`password`, `token`, `authorization`, `api_key`, `secret`, `private_key`) are automatically redacted in structured JSON logs.
- [x] **Container Hardening**: Dockerfile executes as unprivileged `appuser` (UID 10001).
- [x] **Mandatory HTTPS**: In transit data protected via TLS 1.2+ / TLS 1.3.

---

## 8. Operational Verification & Health Probes

### 8.1 Post-Deployment Smoke Test Script

Run these smoke tests against the deployed production endpoint:

```bash
export API_URL="https://api.taskmate.example.com"

# 1. Health Probe Check
curl -s -f "$API_URL/health" | jq .
# Expected: {"status":"ok","service":"TaskMate Backend",...}

# 2. Unauthenticated Request Rejection Check
curl -s -o /dev/null -w "%{http_code}\n" -X POST "$API_URL/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message":"hello"}'
# Expected: 401

# 3. Disallowed CORS Preflight Check
curl -s -I -X OPTIONS "$API_URL/api/chat" \
  -H "Origin: https://malicious-site.example.com" \
  -H "Access-Control-Request-Method: POST"
# Expected: No 'Access-Control-Allow-Origin' header returned
```

---

## 9. Rollback & Disaster Recovery Procedures

### 9.1 Backend Container Rollback
- **Google Cloud Run**: 
  ```bash
  gcloud run services update-traffic taskmate-backend \
      --to-revisions=taskmate-backend-00001-abc=100 \
      --region=us-central1
  ```
  Traffic is instantly redirected to the previous healthy revision with zero downtime.
- **AWS / Docker**:
  Re-deploy the previous tagged image digest:
  ```bash
  docker pull taskmate-backend:<previous-stable-tag>
  ```

### 9.2 Frontend Rollback
- **Firebase Hosting**:
  Roll back instantly via Firebase Console or CLI:
  ```bash
  firebase hosting:rollback --project <project-id>
  ```
- **S3 / CDN**: Re-sync the previously archived `dist/` bundle to the bucket and invalidate the CDN cache.
