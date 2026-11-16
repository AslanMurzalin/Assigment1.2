# DevOps & Observability Guide

> This document covers everything introduced in **GitHub Issues #53–#58**: separate environments, CI/CD promotion, OpenTelemetry, Prometheus metrics, Grafana dashboards, alert rules, and the AI On-Call Responder.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Issue #53 — Dev & Production Environments](#issue-53--dev--production-environments)
3. [Issue #54 — Manual CI/CD Promotion Workflow](#issue-54--manual-cicd-promotion-workflow)
4. [Issue #55 — OpenTelemetry Collection](#issue-55--opentelemetry-collection)
5. [Issue #56 — Application Metrics & Grafana Dashboard](#issue-56--application-metrics--grafana-dashboard)
6. [Issue #57 — Prometheus Alerts & Alertmanager](#issue-57--prometheus-alerts--alertmanager)
7. [Issue #58 — AI On-Call Responder](#issue-58--ai-on-call-responder)
8. [Quick-Start Cheatsheet](#quick-start-cheatsheet)
9. [Environment Variables Reference](#environment-variables-reference)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Link Saver Stack                         │
│                                                                 │
│  ┌──────────────┐   ┌────────────────────────────────────────┐  │
│  │  React SPA   │   │  FastAPI Backend (port 8000)           │  │
│  │  (Vite)      │   │  - /metrics   → Prometheus scrape      │  │
│  └──────────────┘   │  - /health    → Healthcheck endpoint   │  │
│                     │  - OTel SDK → OTLP gRPC → Collector    │  │
│                     └────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │ OTLP gRPC :4317
                              ▼
              ┌───────────────────────────────┐
              │   OTel Collector (port 4317)  │
              │   - Receives: traces + metrics│
              │   - Exports: Jaeger + Prom.   │
              └───────────┬───────────────────┘
                 ┌────────┘───────────┐
                 ▼                    ▼
      ┌──────────────────┐  ┌──────────────────────┐
      │  Prometheus      │  │  Jaeger (port 16686)  │
      │  (port 9090)     │  │  - Distributed traces │
      │  - Scrapes app   │  └──────────────────────┘
      │  - Fires alerts  │
      └────────┬─────────┘
               │ alerts
               ▼
      ┌──────────────────┐       ┌──────────────────────────┐
      │  Alertmanager    │──────▶│  AI On-Call Responder    │
      │  (port 9093)     │webhook│  (port 8080)             │
      └──────────────────┘       │  - FastAPI webhook server│
               │                 │  - Gemini 2.5 Flash LLM  │
               ▼                 │  - Heuristic fallback    │
      ┌──────────────────┐       └──────────────────────────┘
      │  Grafana         │
      │  (port 3000)     │
      │  - Dashboard     │
      │  - Datasources   │
      └──────────────────┘
```

---

## Issue #53 — Dev & Production Environments

**Goal:** Completely separate `development` and `production` Docker Compose environments so changes can be safely tested before going live.

### Key Differences

| Aspect | Development | Production |
|--------|-------------|------------|
| Compose file | `docker-compose.dev.yml` | `docker-compose.prod.yml` |
| Docker build stage | `backend-base` (Python only, no frontend build) | `runtime` (full image with static SPA bundled) |
| Hot-reload | ✅ `--reload` enabled, source mounted as bind volume | ❌ No hot-reload; immutable image |
| Database | `linksaver_dev` (named volume: `linksaver_dev_db_data`) | `linksaver_prod` (named volume: `linksaver_prod_db_data`) |
| `DEBUG` env | `true` | `false` |
| Secrets validation | Falls back to insecure defaults | `POSTGRES_PASSWORD` and `SECRET_KEY` **required** (fail-fast) |
| Resource limits | None | CPU/Memory limits enforced via `deploy.resources` |
| App healthcheck | None | `python -c "urllib.request.urlopen('/health')"` every 10s |

### Dockerfile Multi-Stage Design

The single `Dockerfile` has **3 named stages**:

```
Stage 1  │  FROM node:20-alpine AS frontend-builder
         │  → Builds React SPA to /app/frontend/dist
         │
Stage 2  │  FROM python:3.11-slim AS backend-base
         │  → Installs ffmpeg, nodejs, Python deps
         │  → Copies backend/app + alembic
         │  ← Used by docker-compose.dev.yml  (target: backend-base)
         │
Stage 3  │  FROM backend-base AS runtime
         │  → COPY --from=frontend-builder dist → app/static
         │  ← Used by docker-compose.prod.yml (default target: runtime)
```

This design means dev builds **skip the frontend build entirely**, reducing build time from ~4 minutes to ~30 seconds on subsequent runs.

### Running Development Environment

```bash
# Copy and configure environment
cp .env.development.example .env.development

# Start dev stack (hot-reload enabled)
docker compose -f docker-compose.dev.yml up --build

# Verify
curl http://localhost:8000/health
# → {"status":"ok","version":"1.0.0"}
```

### Running Production Environment

```bash
# Copy and fill in REQUIRED secrets
cp .env.production.example .env.production
# Edit: POSTGRES_PASSWORD, SECRET_KEY, BHAPI_TOKEN

# Start prod stack
docker compose -f docker-compose.prod.yml up --build -d

# Tail logs
docker compose -f docker-compose.prod.yml logs -f app
```

> **Important:** The prod compose enforces `POSTGRES_PASSWORD` and `SECRET_KEY` via `${VAR:?error message}` syntax. The container will refuse to start if these are unset.

---

## Issue #54 — Manual CI/CD Promotion Workflow

**Goal:** A manually triggered GitHub Actions workflow that acts as a guarded promotion gate from development to production — requiring human confirmation, running all tests, and building the final Docker image.

### File: `.github/workflows/promote.yml`

The workflow is triggered **only via `workflow_dispatch`** (never automatically):

```
GitHub Actions → Actions tab → "Promote to Production" → Run workflow
```

### Required Inputs

| Input | Description | Example |
|-------|-------------|---------|
| `environment` | Target environment (always `production`) | `production` |
| `release_tag` | Docker image tag for this release | `v1.2.0` or `prod-20261116` |
| `reason` | Human-readable changelog summary | `"Fixed marketplace extractor timeout"` |
| `confirm_promotion` | Safety gate — must type exactly `promote` | `promote` |

### Workflow Jobs

```
Job 1: pre-promotion-verification
  ├── Validate "promote" confirmation string (exit 1 if wrong)
  ├── Checkout code
  ├── Set up Python 3.11
  ├── Install system deps (ffmpeg, nodejs)
  ├── pip install backend + AI responder requirements
  ├── pytest backend/tests + observability/ai_oncall_responder/tests
  ├── Set up Node.js 20
  ├── npm ci + npm run build (frontend typecheck & bundle)
  └── ✅ All gates passed → proceed

Job 2: promote-and-release  (needs: pre-promotion-verification)
  ├── Checkout code
  ├── Set up Docker Buildx
  ├── Build full production Docker image (target: runtime)
  │   Tags: linksaver:<tag>, linksaver:prod, linksaver:latest
  └── Write GitHub Step Summary with audit trail
```

### How to Trigger

1. Go to your repository → **Actions** tab
2. Click **"Promote to Production"** in the left sidebar
3. Click **"Run workflow"**
4. Fill in the form fields — type `promote` in the confirmation box
5. Click the green **"Run workflow"** button

> The workflow uses `concurrency: group: production-promotion` with `cancel-in-progress: false` to prevent simultaneous promotions.

---

## Issue #55 — OpenTelemetry Collection

**Goal:** Instrument the FastAPI backend with OpenTelemetry to emit traces, metrics, and logs that flow through a central collector.

### Components

| Component | Image | Port | Role |
|-----------|-------|------|------|
| OTel Collector | `otel/opentelemetry-collector-contrib:0.100.0` | 4317 (gRPC), 4318 (HTTP) | Receives OTLP data; fans out to Prometheus + Jaeger |
| Jaeger | `jaegertracing/all-in-one:1.56` | 16686 | Distributed trace storage & UI |

### How OTel Is Initialized in FastAPI

The setup lives in `backend/app/core/telemetry.py` and is called once at application startup from `main.py`:

```python
# backend/app/main.py
from app.core.telemetry import setup_telemetry

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_telemetry(app)
    yield
```

`setup_telemetry()` does the following:
1. Checks if running under pytest — if so, **skips the OTLP exporter** to avoid connection errors during local tests
2. Creates an OTel `TracerProvider` with `service.name` from config
3. Attaches a `BatchSpanProcessor` pointing at the OTel Collector via gRPC
4. Calls `FastAPIInstrumentor.instrument_app()` for automatic HTTP span generation
5. Registers the `/metrics` Prometheus scrape endpoint
6. Attaches the Prometheus HTTP middleware

### Configuration

```bash
# In your .env file:
OTEL_ENABLED=true
OTEL_SERVICE_NAME=linksaver-backend
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
```

Set `OTEL_ENABLED=false` to disable OTel without removing the code (e.g. for lightweight local dev without the observability stack).

### OTel Collector Pipeline

```yaml
# observability/otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc: { endpoint: 0.0.0.0:4317 }
      http: { endpoint: 0.0.0.0:4318 }

processors:
  batch: { timeout: 1s, send_batch_size: 256 }

exporters:
  prometheus:   { endpoint: "0.0.0.0:8889" }  # Scraped by Prometheus
  otlp/jaeger:  { endpoint: "jaeger:4317" }    # Traces → Jaeger UI
  debug:        { verbosity: normal }           # Logs → collector stdout

service:
  pipelines:
    traces:  receivers[otlp] → processors[batch] → exporters[otlp/jaeger, debug]
    metrics: receivers[otlp] → processors[batch] → exporters[prometheus]
    logs:    receivers[otlp] → processors[batch] → exporters[debug]
```

### Viewing Traces

1. Start the observability stack (see [Quick-Start Cheatsheet](#quick-start-cheatsheet))
2. Open **Jaeger UI**: http://localhost:16686
3. Select service `linksaver-backend` → **Find Traces**
4. Each HTTP request appears as a trace with child spans for database queries, extractor calls, etc.

---

## Issue #56 — Application Metrics & Grafana Dashboard

**Goal:** Define application-specific Prometheus metrics and auto-provision a Grafana dashboard that displays them.

### Custom Metrics Defined

All metrics are defined in `backend/app/core/telemetry.py` using `prometheus_client`:

| Metric Name | Type | Labels | What It Measures |
|-------------|------|--------|-----------------|
| `linksaver_http_requests_total` | Counter | `method`, `endpoint`, `status` | Every HTTP request by method, path, and response code |
| `linksaver_http_request_duration_seconds` | Histogram | `method`, `endpoint` | End-to-end request latency |
| `linksaver_links_created_total` | Counter | `site_type`, `domain` | Links saved — split by type (youtube / ozon / generic) |
| `linksaver_extraction_duration_seconds` | Histogram | `extractor_type` | Time spent in each metadata extractor |
| `linksaver_extraction_failures_total` | Counter | `extractor_type`, `error_type` | Failed extraction attempts with error classification |
| `linksaver_youtube_downloads_total` | Counter | `status` (`success`/`failure`) | YouTube streaming attempts |
| `linksaver_youtube_download_duration_seconds` | Histogram | — | Total time for 720p video mux + stream |
| `linksaver_auth_failures_total` | Counter | — | HTTP 401 responses (failed logins / bad tokens) |

### Where Metrics Are Instrumented

| File | Metric(s) Instrumented |
|------|------------------------|
| `backend/app/core/telemetry.py` | HTTP middleware → `linksaver_http_requests_total`, `linksaver_http_request_duration_seconds`, `linksaver_auth_failures_total` |
| `backend/app/services/link_service.py` | `linksaver_links_created_total` incremented on each successful link save |
| `backend/app/services/extractors/dispatcher.py` | `linksaver_extraction_duration_seconds`, `linksaver_extraction_failures_total` around each extractor call |
| `backend/app/services/streaming.py` | `linksaver_youtube_downloads_total`, `linksaver_youtube_download_duration_seconds` |

### Scraping Endpoint

```
GET http://localhost:8000/metrics
Content-Type: text/plain; version=0.0.4; charset=utf-8
```

This is a standard Prometheus text exposition format endpoint, automatically excluded from the HTTP middleware tracking to avoid self-referential metrics.

### Grafana Dashboard

The dashboard is **auto-provisioned** at startup — no manual import required.

| Provisioning File | Purpose |
|-------------------|---------|
| `observability/grafana/provisioning/datasources/datasources.yml` | Registers Prometheus as the default datasource |
| `observability/grafana/provisioning/dashboards/dashboards.yml` | Points Grafana to the dashboard JSON directory |
| `observability/grafana/provisioning/dashboards/linksaver_dashboard.json` | The dashboard definition (8 panels) |

**Dashboard panels:**

1. **Request Rate** — `rate(linksaver_http_requests_total[1m])` by endpoint
2. **Error Rate (5xx)** — `rate(...{status=~"5.."}[1m])` with threshold annotation
3. **Request Latency P95** — `histogram_quantile(0.95, rate(linksaver_http_request_duration_seconds_bucket[5m]))`
4. **Links Saved** — `increase(linksaver_links_created_total[1h])` by `site_type`
5. **Extraction Duration P90** — `histogram_quantile(0.90, ...)` by `extractor_type`
6. **Extraction Failures** — `rate(linksaver_extraction_failures_total[5m])`
7. **YouTube Downloads** — `rate(linksaver_youtube_downloads_total[5m])` by `status`
8. **Auth Failures** — `rate(linksaver_auth_failures_total[2m])`

**Access Grafana:** http://localhost:3000 — login with `admin` / `admin`

---

## Issue #57 — Prometheus Alerts & Alertmanager

**Goal:** Define alert rules that fire when metrics cross critical thresholds, and route them to the AI On-Call Responder via Alertmanager webhook.

### Alert Rules

Defined in `observability/prometheus/alert.rules.yml`:

#### 1. `High5xxErrorRate` — Severity: **critical**

```promql
sum(rate(linksaver_http_requests_total{status=~"5.."}[2m])) > 0.05
OR
sum(increase(linksaver_http_requests_total{status=~"5.."}[1m])) > 3
```

- Fires after **30 seconds** sustained
- Triggered by: unhandled exceptions, database connection exhaustion, missing secrets

#### 2. `MarketplaceExtractorFailure` — Severity: **warning**

```promql
sum(increase(linksaver_extraction_failures_total[2m])) > 2
```

- Fires after **30 seconds** sustained
- Triggered by: BHAPI token expiry, Ozon/Wildberries anti-bot changes, network timeouts

#### 3. `YouTubeDownloadFailure` — Severity: **warning**

```promql
sum(increase(linksaver_youtube_downloads_total{status="failure"}[2m])) > 1
```

- Fires after **15 seconds** sustained
- Triggered by: YouTube cipher rotation, outdated yt-dlp binary, missing ffmpeg

#### 4. `HighAuthFailureRate` — Severity: **warning**

```promql
sum(increase(linksaver_auth_failures_total[2m])) >= 5
```

- Fires after **15 seconds** sustained
- Triggered by: brute-force attacks, credential stuffing, expired client tokens

### Alertmanager Routing

```yaml
# observability/alertmanager/alertmanager.yml
route:
  group_by: ['alertname', 'severity', 'service']
  group_wait: 5s
  repeat_interval: 1m
  receiver: 'ai-oncall-agent'

receivers:
  - name: 'ai-oncall-agent'
    webhook_configs:
      - url: 'http://ai-responder:8080/webhook/alert'
        send_resolved: true
        max_alerts: 10
```

All alerts route to the AI On-Call Responder webhook. The responder also receives `resolved` notifications so it can acknowledge auto-recovery.

### Checking Alert Status

- **Prometheus Alerts tab:** http://localhost:9090/alerts
- **Alertmanager UI:** http://localhost:9093

---

## Issue #58 — AI On-Call Responder

**Goal:** An autonomous FastAPI microservice that receives Alertmanager webhooks, uses **Google Gemini 2.5 Flash** to triage incidents, and returns a structured `IncidentReport` with severity, root cause, and remediation steps.

### Location

```
observability/ai_oncall_responder/
├── ai_responder/
│   ├── agent.py      ← Core AIIncidentAgent class + Gemini integration
│   ├── config.py     ← Settings (GEMINI_API_KEY, model, URLs)
│   ├── main.py       ← FastAPI app with /webhook/alert and /health
│   └── schemas.py    ← Pydantic models: AlertmanagerWebhook, IncidentReport
├── tests/
│   └── test_ai_responder.py   ← 6 pytest tests
├── requirements.txt
└── Dockerfile
```

### Webhook Contract

**POST `/webhook/alert`**

Accepts the standard Alertmanager webhook payload and returns:

```json
{
  "incident_id": "inc-a1b2c3d4",
  "created_at": "2026-11-16T11:00:00Z",
  "status": "action_required",
  "severity": "P1_CRITICAL",
  "summary": "Critical server error spike: API returning elevated 5xx responses.",
  "affected_components": ["backend-api", "database"],
  "probable_root_cause": "Unhandled exception in FastAPI request handlers...",
  "impact_assessment": "Users may experience failed link saves...",
  "remediation_steps": [
    "docker compose -f docker-compose.prod.yml logs --tail=100 app",
    "docker exec linksaver-db-prod pg_isready",
    "docker compose -f docker-compose.prod.yml restart app"
  ],
  "prevention_recommendations": [
    "Implement circuit breaker and connection pooling retries",
    "Add automated synthetic canary monitoring"
  ],
  "raw_alert_count": 1
}
```

### Triage Logic

The agent follows a 3-tier decision tree:

```
Incoming alert webhook
        │
        ▼
  status == "resolved"?
        │
       YES → Return auto-resolved P4_LOW report
        │
       NO
        │
        ▼
  GEMINI_API_KEY set?
        │
       YES → Call Gemini 2.5 Flash with full alert context
        │    Parse structured JSON response
        │
  Gemini fails / NO key
        │
        ▼
  Heuristic Engine
  ├── High5xxErrorRate    → P1_CRITICAL report + Docker restart commands
  ├── MarketplaceFailure  → P2_HIGH report + BHAPI diagnostic steps
  ├── YouTubeFailure      → P2_HIGH report + yt-dlp update steps
  ├── HighAuthFailure     → P2_HIGH report + rate-limit recommendations
  └── Unknown alert       → P3_MEDIUM report + Grafana dashboard link
```

### Severity Levels

| Level | Meaning | Example |
|-------|---------|---------|
| `P1_CRITICAL` | Service down or severely degraded | High 5xx error rate |
| `P2_HIGH` | Major feature broken | YouTube streaming down, marketplace scraper failing |
| `P3_MEDIUM` | Degraded non-critical feature | Unknown metric anomaly |
| `P4_LOW` | Informational / resolved | Alert auto-resolved |

### Gemini System Prompt

The agent identifies itself as a **Principal SRE** with full knowledge of the Link Saver stack and always responds with valid JSON structured exactly as `IncidentReport`. The model is configured with `response_mime_type: "application/json"` for deterministic output.

### Configuration

```bash
GEMINI_API_KEY=your_gemini_api_key_here   # Optional — heuristic fallback if absent
GEMINI_MODEL=gemini-2.5-flash              # Default model
PROMETHEUS_URL=http://prometheus:9090
JAEGER_URL=http://jaeger:16686
```

Get a free API key at: https://aistudio.google.com/apikey

### Testing the AI Responder Locally (Without Docker)

```bash
# Run unit tests
.venv\Scripts\pytest.exe observability/ai_oncall_responder/tests -v

# Start the FastAPI service directly
cd observability/ai_oncall_responder
..\..\.venv\Scripts\uvicorn.exe ai_responder.main:app --port 8080 --reload

# Health check
curl http://localhost:8080/health

# Send a test alert
curl -X POST http://localhost:8080/webhook/alert \
  -H "Content-Type: application/json" \
  -d '{
    "version": "4",
    "status": "firing",
    "alerts": [{
      "status": "firing",
      "labels": {"alertname": "High5xxErrorRate", "severity": "critical", "component": "backend"},
      "annotations": {"summary": "High 5xx error rate", "description": "5xx errors spiking"}
    }],
    "commonLabels": {"severity": "critical"},
    "commonAnnotations": {}
  }'
```

---

## Quick-Start Cheatsheet

### Start Dev Environment

```bash
docker compose -f docker-compose.dev.yml up --build
```

| URL | Purpose |
|-----|---------|
| http://localhost:8000 | Link Saver app (API + React SPA in dev) |
| http://localhost:8000/docs | Swagger UI |
| http://localhost:8000/health | Health check |
| http://localhost:8000/metrics | Prometheus metrics scrape |

### Start Observability Stack

```bash
docker compose -f observability/docker-compose.observability.yml up -d
```

| URL | Purpose | Credentials |
|-----|---------|-------------|
| http://localhost:3000 | Grafana dashboards | admin / admin |
| http://localhost:9090 | Prometheus + alerts | — |
| http://localhost:9093 | Alertmanager | — |
| http://localhost:16686 | Jaeger trace UI | — |
| http://localhost:8080 | AI On-Call Responder | — |

### Trigger CI/CD Promotion

```
GitHub → Actions → "Promote to Production" → Run workflow
```

Fill in: target=`production`, tag=`v1.x.0`, reason=`"..."`, confirm=`promote`

### Run All Tests

```bash
# Backend + AI Responder (27 tests total)
.venv\Scripts\pytest.exe backend/tests observability/ai_oncall_responder/tests -v

# Frontend build check
cmd /c "cd frontend && npm run build"
```

---

## Environment Variables Reference

### Application (Backend)

| Variable | Dev Default | Prod Required | Description |
|----------|-------------|---------------|-------------|
| `DATABASE_URL` | `postgresql+psycopg2://postgres:postgres@db:5432/linksaver_dev` | ✅ | Full PostgreSQL connection string |
| `SECRET_KEY` | `dev-insecure-secret-key-change-me-12345` | ✅ Required | JWT signing secret (use 32+ random chars) |
| `BHAPI_TOKEN` | *(empty)* | Optional | BHAPI.ru token for Ozon/WB extraction |
| `BHAPI_BASE_URL` | `https://bhapi.ru` | Optional | BHAPI base URL |
| `OTEL_ENABLED` | `true` | Optional | Enable/disable OTel instrumentation |
| `OTEL_SERVICE_NAME` | `linksaver-backend` | Optional | Service name in Jaeger traces |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://otel-collector:4317` | Optional | OTel Collector gRPC endpoint |

### AI On-Call Responder

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | *(empty)* | Google AI Studio API key (heuristic fallback if absent) |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model name |
| `PROMETHEUS_URL` | `http://prometheus:9090` | Prometheus base URL for metric queries |
| `JAEGER_URL` | `http://jaeger:16686` | Jaeger base URL for trace lookups |
| `PORT` | `8080` | AI responder service port |

### Template Files

- `.env.development.example` — template for dev secrets
- `.env.production.example` — template for prod secrets (required vars marked)
- `backend/.env.example` — backend-only env template

> **Security rule:** Never commit real `.env` files. They are listed in `.gitignore`. Always use the `.example` templates as reference.
