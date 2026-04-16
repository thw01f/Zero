# Deployment Guide

---

## Local Development

### Prerequisites

- Python 3.11+
- Node 20+
- [Ollama](https://ollama.ai) (for local LLM)
- Git

### Setup

```bash
# Clone
git clone git@github.com:thw01f/Zero.git
cd Zero

# Install all dependencies
make install

# Pull the LLM model (9GB, one-time)
ollama pull qwen2.5-coder:14b

# Configure
cp backend/.env.example backend/.env
# Edit backend/.env — defaults work for local dev with Ollama

# Seed demo data
make seed

# Start
make dev  # Starts both backend (:7860) and frontend (:5173)
```

Open `http://localhost:5173/?demo=demo-darklead-19c2af76` for the demo.

### Individual Servers

```bash
make backend   # FastAPI only on :7860 (serves built frontend too)
make frontend  # Vite dev server on :5173 with hot reload
```

---

## Environment Variables

```bash
# backend/.env

# LLM Configuration
ANTHROPIC_API_KEY=sk-ant-your-key-here  # Leave as-is to use Ollama
MODEL=claude-sonnet-4-6                  # Anthropic model (if using cloud)
USE_LOCAL_LLM=true                       # Force Ollama even if API key set
OLLAMA_URL=http://localhost:11434        # Ollama server URL
OLLAMA_MODEL=qwen2.5-coder:14b          # Model to use

# Database
DATABASE_URL=sqlite:///./darklead.db    # Local dev
# DATABASE_URL=sqlite:////data/darklead.db  # Docker/HF Spaces

# Optional
REDIS_URL=redis://localhost:6379/0      # For Celery (falls back to asyncio)
MAX_REPO_SIZE_MB=200                    # Reject repos larger than this
CLONE_TIMEOUT_S=60                      # Git clone timeout
LLM_FIX_BATCH_SIZE=20                  # Fixes generated per LLM call
ADVISORY_POLL_HOURS=6                   # CVE advisory refresh interval
SELF_HEALTH_INTERVAL_MIN=5             # Health check interval
NVD_API_KEY=                           # NVD API key (optional, increases rate limit)
GITHUB_TOKEN=                          # For scanning private repos
GITHUB_WEBHOOK_SECRET=                 # For webhook signature verification
```

---

## Docker

### Build & Run

```bash
# Build
docker build -t darklead:latest .

# Run (with Ollama sidecar)
docker run -p 7860:7860 \
  -e OLLAMA_URL=http://host.docker.internal:11434 \
  -e USE_LOCAL_LLM=true \
  -v $(pwd)/data:/data \
  darklead:latest

# Run with Anthropic API key
docker run -p 7860:7860 \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  -e USE_LOCAL_LLM=false \
  darklead:latest
```

### Dockerfile Stages

```dockerfile
# Stage 1: Build frontend
FROM node:20-slim AS frontend-builder
COPY frontend/ /app/frontend/
RUN npm ci --legacy-peer-deps && npm run build

# Stage 2: Install Python deps
FROM python:3.11-slim AS py-builder
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 3: Runtime
FROM python:3.11-slim
# Copy from stages, set non-root user (uid 1000 for HF Spaces)
USER 1000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
```

---

## Hugging Face Spaces

DarkLead is configured for HF Spaces Docker SDK deployment.

### `README.md` frontmatter
```yaml
---
title: DarkLead
emoji: 🔍
colorFrom: violet
colorTo: orange
sdk: docker
app_port: 7860
---
```

### Limitations on HF Spaces
- No Ollama (no GPU allocation for local LLM) → set `ANTHROPIC_API_KEY` in Space secrets
- No persistent filesystem → SQLite stored in `/data` volume
- No Redis → Celery disabled, asyncio background thread used

### Deployment Steps
1. Fork this repo to your HF account
2. Go to Space settings → Secrets → add `ANTHROPIC_API_KEY`
3. Set `USE_LOCAL_LLM=false` in Space variables
4. Push to trigger rebuild

---

## Production Checklist

- [ ] Set real `ANTHROPIC_API_KEY` or configure Ollama with GPU
- [ ] Set `DATABASE_URL` to persistent path (`sqlite:////data/darklead.db`)
- [ ] Set `GITHUB_WEBHOOK_SECRET` if using webhook integration
- [ ] Set `NVD_API_KEY` for higher CVE API rate limits
- [ ] Configure reverse proxy (nginx/caddy) in front of port 7860
- [ ] Enable HTTPS (TLS certificate)
- [ ] Review CORS settings in `main.py`
- [ ] Run `make seed` to populate demo data
- [ ] Test: `curl http://your-host/health`

---

## GitHub Actions CI

The repo includes 3 CI workflows (`.github/workflows/`):

| Workflow | Trigger | Jobs |
|----------|---------|------|
| `ci.yml` | Push to main/dev, PR | pytest + vue-tsc + vite build + bandit scan |
| `docker-build.yml` | Push to main, version tags | Docker BuildKit with GHA cache |

Run locally:
```bash
make test   # pytest backend/tests/
make lint   # ruff check + vue-tsc
```
