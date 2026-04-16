# Configuration

All configuration is via environment variables loaded from `backend/.env`.

---

## Default Admin Account

A default admin account is seeded automatically on first startup:

| Field | Value |
|-------|-------|
| **Username** | `admin` |
| **Password** | `zero` |
| **Email** | `admin@darklead.local` |
| **Role** | `admin` |

To change the password after login: go to **Profile → Security → Change Password**.

To override the JWT signing secret (strongly recommended in production):
```bash
JWT_SECRET=your-random-256-bit-secret
```

---

## Complete Variable Reference

### LLM Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | `sk-ant-your-key-here` | Anthropic API key. Leave as default to use Ollama. |
| `MODEL` | `claude-sonnet-4-6` | Anthropic model ID when using cloud backend |
| `USE_LOCAL_LLM` | `false` | Force Ollama even if API key is set |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama server base URL |
| `OLLAMA_MODEL` | `qwen2.5-coder:14b` | Ollama model name |

**Backend selection logic:**
- If `USE_LOCAL_LLM=true` → always use Ollama
- If API key starts with `sk-ant-your` → use Ollama
- Otherwise → use Anthropic

### Database

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./darklead.db` | SQLAlchemy DB URL |

Examples:
```bash
sqlite:///./darklead.db                           # Relative path (local dev)
sqlite:////data/darklead.db                       # Absolute path (Docker)
postgresql+psycopg2://user:pass@localhost/dbname  # PostgreSQL (production)
```

### Scanning Limits

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_REPO_SIZE_MB` | `200` | Reject repos larger than this |
| `CLONE_TIMEOUT_S` | `60` | Git clone timeout in seconds |
| `LLM_FIX_BATCH_SIZE` | `20` | Number of fixes generated per LLM call |

### Optional Integrations

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis for Celery. Falls back to asyncio thread if unavailable. |
| `NVD_API_KEY` | _(empty)_ | NVD API key. Optional — without key, rate limited to 5 req/30s |
| `GITHUB_TOKEN` | _(empty)_ | GitHub token for scanning private repos |
| `GITHUB_WEBHOOK_SECRET` | _(empty)_ | HMAC secret for webhook signature verification |

### Scheduler

| Variable | Default | Description |
|----------|---------|-------------|
| `ADVISORY_POLL_HOURS` | `6` | How often to refresh CVE advisories from NVD + OSV |
| `SELF_HEALTH_INTERVAL_MIN` | `5` | How often to run self-health checks |

---

## `.env.example`

```bash
# Copy to .env and fill in values

# LLM — leave ANTHROPIC_API_KEY as placeholder to use local Ollama
ANTHROPIC_API_KEY=sk-ant-your-key-here
MODEL=claude-sonnet-4-6
USE_LOCAL_LLM=true
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:14b

# Database
DATABASE_URL=sqlite:///./darklead.db

# Optional integrations
REDIS_URL=redis://localhost:6379/0
NVD_API_KEY=
GITHUB_TOKEN=
GITHUB_WEBHOOK_SECRET=

# Tuning
MAX_REPO_SIZE_MB=200
CLONE_TIMEOUT_S=60
LLM_FIX_BATCH_SIZE=20
ADVISORY_POLL_HOURS=6
SELF_HEALTH_INTERVAL_MIN=5
```

---

## Pydantic Settings Class

```python
class Settings(BaseSettings):
    anthropic_api_key: str = "sk-ant-your-key-here"
    model: str = "claude-sonnet-4-6"
    use_local_llm: bool = False
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5-coder:14b"
    database_url: str = "sqlite:///./darklead.db"
    redis_url: str = "redis://localhost:6379/0"
    max_repo_size_mb: int = 200
    clone_timeout_s: int = 60
    llm_fix_batch_size: int = 20
    advisory_poll_hours: int = 6
    self_health_interval_min: int = 5
    nvd_api_key: str = ""
    github_token: str = ""
    github_webhook_secret: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
```

Settings are loaded once at startup and accessed via `from app.config import settings`.

---

## Feature Flags

There are no feature flags — use environment variables directly. To disable a scanner:

```python
# In orchestrator.py, comment out the scanner:
SCANNERS = [
    BanditScanner(),
    RuffScanner(),
    # LizardScanner(),  # disabled
    ...
]
```

---

## Ollama Model Selection Guide

| Model | Size | Speed | Quality | Best for |
|-------|------|-------|---------|---------|
| `qwen2.5-coder:7b` | 4.7 GB | Fast | Good | Quick scans, low RAM |
| `qwen2.5-coder:14b` | 9 GB | Medium | **Best** | Default — highest accuracy |
| `phi4:latest` | 5.6 GB | Fast | Good | Balanced option |
| `deepseek-r1:14b` | 9 GB | Slow | Excellent | Complex reasoning, architecture analysis |

Switch model without restart:
```bash
# .env
OLLAMA_MODEL=phi4:latest
```
