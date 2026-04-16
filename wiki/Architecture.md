# Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DarkLead Platform                            │
│                                                                     │
│  ┌──────────────┐     ┌─────────────────────────────────────────┐  │
│  │  Vue 3 SPA   │────▶│           FastAPI Backend               │  │
│  │  (port 5173) │◀────│           (port 7860)                   │  │
│  │              │ WS  │                                         │  │
│  │ FortiAnalyzer│     │  ┌─────────┐  ┌──────────┐  ┌───────┐  │  │
│  │ Dark Theme   │     │  │  Scan   │  │  Report  │  │ Chat  │  │  │
│  │              │     │  │ Routes  │  │  Routes  │  │ Route │  │  │
│  └──────────────┘     │  └────┬────┘  └────┬─────┘  └───┬───┘  │  │
│                        │       │             │             │      │  │
│                        │  ┌────▼─────────────▼─────────────▼───┐ │  │
│                        │  │         13-Step Scan Pipeline       │ │  │
│                        │  │  clone → detect → LOC → scan →     │ │  │
│                        │  │  triage → fixes → misconfig →      │ │  │
│                        │  │  modules → compliance → updates →  │ │  │
│                        │  │  summary → persist → WebSocket     │ │  │
│                        │  └────────────────┬────────────────────┘ │  │
│                        │                   │                       │  │
│                        │  ┌────────────────▼────────────────────┐ │  │
│                        │  │         Scanner Ensemble            │ │  │
│                        │  │  bandit  ruff   lizard  semgrep     │ │  │
│                        │  │  gitleaks trivy pip-audit npm-audit │ │  │
│                        │  │  checkov hadolint radon osv-scanner │ │  │
│                        │  │  tfsec  eslint  pmd  spotbugs  env  │ │  │
│                        │  └────────────────┬────────────────────┘ │  │
│                        │                   │                       │  │
│                        │  ┌────────────────▼────────────────────┐ │  │
│                        │  │           LLM Layer                 │ │  │
│                        │  │  Ollama (local)  │  Anthropic API   │ │  │
│                        │  │  qwen2.5-coder   │  claude-sonnet   │ │  │
│                        │  └─────────────────────────────────────┘ │  │
│                        │                                           │  │
│                        │  ┌──────────┐  ┌──────────┐  ┌────────┐ │  │
│                        │  │  SQLite  │  │ APSched  │  │  WS   │ │  │
│                        │  │    DB    │  │(Advisory)│  │Manager│ │  │
│                        │  └──────────┘  └──────────┘  └────────┘ │  │
│                        └─────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 13-Step Scan Pipeline

Each `POST /api/scan` triggers an async pipeline that runs in a background thread:

| Step | Name | What happens |
|------|------|-------------|
| 1 | **clone** | `git clone --depth=1` into `/tmp/darklead-XXXX/` |
| 2 | **detect** | Detect languages, file count, framework fingerprinting |
| 3 | **loc** | Count lines of code by language using `loc_counter` |
| 4 | **scan** | Run all 19 static scanners in `asyncio.gather()` |
| 5 | **triage** | LLM assigns CWE, OWASP, severity, explanation to each finding |
| 6 | **fixes** | LLM generates diff-ready code fixes (batched, 20/batch) |
| 7 | **misconfig** | Detect IaC misconfigs (Dockerfile, YAML, .env, Terraform) |
| 8 | **modules** | Group files into semantic modules (api/models/utils/…) |
| 9 | **compliance** | Map findings → OWASP 2021 → NIST SP 800-53 controls |
| 10 | **updates** | Query OSV.dev + NVD for dependency CVEs |
| 11 | **summary** | LLM generates executive summary + remediation roadmap |
| 12 | **persist** | Write everything to SQLite via SQLAlchemy |
| 13 | **WebSocket** | Broadcast final result + grade to all connected clients |

WebSocket events pushed after each step: `{"step": "scan", "progress": 30, "message": "Running 19 scanners..."}`

---

## Component Map

```
darklead/
├── backend/
│   └── app/
│       ├── main.py              # FastAPI app, lifespan, SPA serving
│       ├── config.py            # Pydantic Settings (env vars)
│       ├── database.py          # SQLAlchemy engine + SessionLocal
│       ├── models.py            # ORM: Job, Issue, Module, Misconfig, Advisory…
│       ├── schemas.py           # Pydantic request/response models
│       ├── routes/
│       │   ├── scan.py          # POST /scan, GET /scan/jobs
│       │   ├── report.py        # GET /report/{jobId}
│       │   ├── analyze.py       # POST /analyze/code, GET /analyze/models
│       │   ├── chat.py          # POST /chat/{jobId}
│       │   ├── monitor.py       # GET /advisories (SSE)
│       │   ├── ws.py            # WS /ws/{jobId}
│       │   ├── health.py        # GET /health
│       │   ├── export.py        # GET /export/{jobId}/{format}
│       │   ├── diff.py          # POST /diff/generate
│       │   ├── search.py        # GET /search/findings
│       │   ├── stats.py         # GET /stats/overview, /stats/trends
│       │   └── webhook.py       # POST /webhook/github
│       ├── mcp/
│       │   ├── llm_layer.py     # Dual LLM: Ollama + Anthropic routing
│       │   ├── scanners/        # 19 scanner tool implementations
│       │   └── orchestrator.py  # asyncio.gather() all scanners
│       ├── utils/               # 20+ utility modules
│       ├── scanners/            # Advanced scanner: SQL, config, Docker
│       └── middleware/          # RequestId, Timing
├── frontend/
│   └── src/
│       ├── App.vue              # Shell: header + sidebar + router-view
│       ├── router/index.ts      # Vue Router routes
│       ├── stores/              # Pinia: report, scan, alerts, settings, history
│       ├── views/               # 20+ dashboard panels
│       ├── components/          # 25+ reusable UI components
│       └── composables/         # useWebSocket, useTheme, useApi, useClipboard…
├── Dockerfile                   # 3-stage build (node-builder / py-builder / runtime)
├── Makefile                     # make dev / test / lint / seed
└── .github/workflows/           # CI: test + build + bandit + docker
```

---

## Data Flow

```
User submits URL
      │
      ▼
POST /api/scan ──► Job created (status=queued) ──► Background thread spawned
                                                          │
                                              ┌───────────▼───────────┐
                                              │  _scan_pipeline()     │
                                              │  async, 13 steps      │
                                              │  WS broadcast/step    │
                                              └───────────┬───────────┘
                                                          │
                                              ┌───────────▼───────────┐
                                              │  asyncio.gather()     │
                                              │  19 scanners          │
                                              │  parallel execution   │
                                              └───────────┬───────────┘
                                                          │
                                              ┌───────────▼───────────┐
                                              │  LLM triage batch     │
                                              │  Ollama/Anthropic     │
                                              │  JSON extraction      │
                                              └───────────┬───────────┘
                                                          │
                                              ┌───────────▼───────────┐
                                              │  debt_score.py        │
                                              │  weighted formula     │
                                              │  0-100 → A/B/C/D/F   │
                                              └───────────┬───────────┘
                                                          │
                                              ┌───────────▼───────────┐
                                              │  SQLite persist       │
                                              │  Job + Issues +       │
                                              │  Modules + Misconfigs │
                                              └───────────┬───────────┘
                                                          │
                                              WS broadcast ──► Frontend update
```

---

## Technology Choices

| Concern | Choice | Rationale |
|---------|--------|-----------|
| **API framework** | FastAPI | Async-native, automatic OpenAPI docs, pydantic validation |
| **Database** | SQLite + SQLAlchemy | Zero-infra for hackathon; trivially swappable to Postgres |
| **Task queue** | asyncio thread (Redis/Celery optional) | No Redis dependency for bare-metal deploy |
| **LLM local** | Ollama + qwen2.5-coder:14b | Best coding LLM at 9GB, runs on consumer GPU |
| **LLM cloud** | Anthropic Claude | Highest quality fallback, same API pattern |
| **Frontend** | Vue 3 + Pinia + Vite | Composition API ideal for reactive dashboard data |
| **Styling** | Tailwind + custom CSS | Utility-first + custom `.ft-*` Fortinet design tokens |
| **Charts** | ApexCharts + d3 | ApexCharts for timeseries; d3 for treemap heatmap |
| **Scheduling** | APScheduler | Advisory CVE polling every 6h, health checks every 5min |
| **Containerization** | Docker multi-stage | node-builder → py-builder → slim runtime (400MB image) |
