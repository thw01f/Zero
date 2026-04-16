# API Reference

Base URL: `http://localhost:7860`

All endpoints under `/api/*`. The root `/` and `/*` serve the Vue SPA.

---

## Health

### `GET /health`
Returns platform health status including scanner availability and LLM backend.

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "llm_backend": "ollama",
  "llm_model": "qwen2.5-coder:14b",
  "scanners": {
    "bandit": true,
    "ruff": true,
    "lizard": true,
    "semgrep": false
  },
  "db": "ok",
  "uptime_s": 3621
}
```

---

## Scan

### `POST /api/scan`
Submit a GitHub repository for full SAST analysis.

**Request:**
```json
{
  "repo_url": "https://github.com/owner/repo",
  "branch": "main"
}
```

**Response:**
```json
{
  "job_id": "abc123-def456",
  "status": "queued",
  "message": "Scan queued. Connect to WS /api/ws/abc123-def456 for live updates."
}
```

**Errors:**
- `400` — Invalid repo URL or SSRF attempt
- `429` — Rate limit exceeded (10 scans/60s per IP)

---

### `GET /api/scan/jobs`
List all past scans.

**Response:**
```json
{
  "jobs": [
    {
      "job_id": "abc123",
      "repo_url": "https://github.com/owner/repo",
      "grade": "C",
      "debt_score": 58,
      "issue_count": 19,
      "status": "completed",
      "created_at": "2026-04-16T10:30:00"
    }
  ]
}
```

---

## Report

### `GET /api/report/{jobId}`
Fetch the full scan report.

**Response:**
```json
{
  "job_id": "abc123",
  "repo_url": "https://github.com/owner/repo",
  "grade": "C",
  "debt_score": 58,
  "issue_count": 19,
  "summary": "The repository has 19 issues...",
  "issues": [
    {
      "id": 1,
      "severity": "critical",
      "category": "security",
      "rule": "B602",
      "message": "subprocess call with shell=True",
      "file_path": "app/utils.py",
      "line_number": 42,
      "explanation": "Using shell=True with user input allows command injection...",
      "cwe": "CWE-78",
      "owasp": "A03:2021",
      "fix_suggestion": "subprocess.run(['cmd', arg], shell=False)",
      "tool": "bandit",
      "fingerprint": "a1b2c3d4"
    }
  ],
  "modules": [...],
  "misconfigurations": [...],
  "compliance": {...},
  "created_at": "2026-04-16T10:35:22"
}
```

---

## Code Analysis

### `POST /api/analyze/code`
Analyze a code snippet directly — no repo needed.

**Request:**
```json
{
  "code": "import subprocess\nsubprocess.run(cmd, shell=True)",
  "language": "python",
  "filename": "utils.py",
  "mode": "full"
}
```

`mode` options: `full` | `security` | `quality` | `improve`

**Response:**
```json
{
  "overall_score": 20,
  "overall_grade": "F",
  "summary": "Critical security vulnerabilities found...",
  "findings": [
    {
      "line": 2,
      "severity": "critical",
      "category": "security",
      "rule": "B602",
      "message": "subprocess call with shell=True",
      "explanation": "Allows OS command injection if cmd contains user input.",
      "cwe": "CWE-78",
      "owasp": "A03:2021",
      "tool": "bandit"
    }
  ],
  "improvements": [
    {
      "priority": "high",
      "title": "Use shell=False with argument list",
      "description": "Pass command as a list instead of string",
      "example": "subprocess.run(['cmd', arg], shell=False)"
    }
  ],
  "metrics": {
    "loc": 2,
    "complexity_estimate": "low",
    "security_issues": 1,
    "quality_issues": 0,
    "has_tests": false
  },
  "static_tools_run": ["bandit", "ruff", "lizard"],
  "language": "python",
  "filename": "utils.py",
  "loc": 2
}
```

---

### `GET /api/analyze/models`
List available LLM backends and currently active model.

**Response:**
```json
{
  "active_backend": "ollama",
  "active_model": "qwen2.5-coder:14b",
  "models": [
    {"name": "qwen2.5-coder:14b", "backend": "ollama", "size": 9000000000},
    {"name": "phi4:latest", "backend": "ollama", "size": 5600000000}
  ]
}
```

---

## AI Chat

### `POST /api/chat/{jobId}`
Ask the LLM questions about a scan result.

**Request:**
```json
{
  "message": "What is the most critical vulnerability and how do I fix it?"
}
```

**Response:**
```json
{
  "response": "The most critical finding is CWE-78 (OS Command Injection) on line 42 of app/utils.py...",
  "job_id": "abc123"
}
```

---

## Monitor / Advisories

### `GET /api/advisories`
Returns recent CVE advisories (polled from NVD + OSV.dev every 6h).

**Response:**
```json
{
  "advisories": [
    {
      "cve_id": "CVE-2024-1234",
      "severity": "critical",
      "cvss_score": 9.8,
      "description": "Remote code execution in libXyz...",
      "published": "2026-04-15T00:00:00Z"
    }
  ],
  "last_updated": "2026-04-16T06:00:00Z"
}
```

---

## WebSocket

### `WS /api/ws/{jobId}`
Real-time scan progress updates.

Connect immediately after `POST /api/scan`. Messages:

```json
{"type": "progress", "step": "scan", "progress": 30, "message": "Running 19 scanners..."}
{"type": "progress", "step": "triage", "progress": 55, "message": "LLM triaging 19 findings..."}
{"type": "complete", "job_id": "abc123", "grade": "C", "debt_score": 58}
{"type": "error", "message": "Clone failed: repository not found"}
```

---

## Export

### `GET /api/export/{jobId}/json`
Download full report as JSON.

### `GET /api/export/{jobId}/sarif`
Download SARIF 2.1.0 report (compatible with GitHub Code Scanning).

### `GET /api/export/{jobId}/html`
Download HTML report for sharing with stakeholders.

---

## Diff

### `POST /api/diff/generate`
Generate unified diff between original and fixed code.

**Request:**
```json
{
  "original": "password = 'admin123'",
  "fixed": "import os\npassword = os.environ['DB_PASSWORD']",
  "filename": "config.py",
  "context": 3
}
```

**Response:**
```json
{
  "unified": "--- a/config.py\n+++ b/config.py\n...",
  "html": "<span class='diff-del'>-password = 'admin123'</span>...",
  "added": 2,
  "removed": 1
}
```

---

## Search

### `GET /api/search/findings?q={query}&severity={sev}`
Full-text search across all scan findings.

**Parameters:**
- `q` (required, min 2 chars) — search query against message + rule
- `severity` (optional) — filter by `critical|major|minor|info`

---

## Stats

### `GET /api/stats/overview`
Aggregate statistics across all scans.

**Response:**
```json
{
  "total_scans": 12,
  "total_issues": 143,
  "grade_distribution": {"A": 2, "B": 4, "C": 3, "D": 2, "F": 1},
  "avg_debt_score": 65.3,
  "critical_issues": 18
}
```

### `GET /api/stats/trends`
Time-series debt scores for trend chart.

---

## Webhook

### `POST /api/webhook/github`
Receives GitHub push webhooks. Auto-triggers scan on push to default branch.

Configure in your repo: `Settings → Webhooks → Payload URL: https://your-host/api/webhook/github`

Set `GITHUB_WEBHOOK_SECRET` env var for HMAC-SHA256 verification.
