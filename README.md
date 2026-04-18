# DarkLead — AI-Powered Code Intelligence Platform

> **TENSOR'26 Hackathon — PS29** | Team DARKLEAD! | Members: GOWTHAMANGS | RAMYAPRABHA B | NANDAKISHORE V | DHARSHINI S
> Built with Claude Sonnet 4.6

[![Build](https://img.shields.io/badge/build-passing-brightgreen)](#)
[![Grade](https://img.shields.io/badge/self--scan-Grade%20A-brightgreen)](#)
[![LLM](https://img.shields.io/badge/LLM-Ollama%20%7C%20Anthropic-orange)](#)
[![Commits](https://img.shields.io/badge/commits-303%2B-blue)](#)
[![Panels](https://img.shields.io/badge/UI%20panels-20%2B-blueviolet)](#)
[![Scanners](https://img.shields.io/badge/scanners-19-red)](#)

DarkLead is a production-grade SAST platform that accepts a GitHub repo URL or zip upload, runs **19 static analysis tools in parallel**, triages all findings through a local or cloud LLM, generates **compilable fix diffs**, and presents results through a **20+ panel** FortiAnalyzer-inspired dark dashboard.

---

## Live Demo Scan — DarkLead-Hub/QAVACH

> Scanned April 18, 2026 — results visible in all screenshots below

| Metric | Value |
|--------|-------|
| **Total Issues** | 21 |
| **Critical** | 6 |
| **Major** | 11 |
| **Minor** | 4 |
| **Debt Score** | 11.1 / 100 |
| **Grade** | **A** |
| **Modules Analyzed** | 130 |
| **Secrets Detected** | 11 |
| **Scan Time** | 124.0 s |
| **Language** | JavaScript |

### Executive Summary (LLM-generated)

> The QAVACH JavaScript repository presents a significant security risk with 21 identified vulnerabilities, including six critical issues. Notably, the use of JWTs and generic API keys in multiple files poses severe risks that must be addressed immediately to prevent unauthorized access and potential data breaches. It is imperative to implement secure authentication mechanisms and remove hardcoded API keys from environment files to mitigate these critical vulnerabilities.

### Top Critical Risks

| Severity | File | Rule | Message |
|----------|------|------|---------|
| CRITICAL | `Issue_Portal/utils/supabase/info.tsx:4` | `jwt` | Secret detected: Uncovered a JSON Web Token |
| CRITICAL | `Documentation/01_GOVSIGN_API.md:575` | `curl-auth-header` | Secret detected: Potential authorization token |
| CRITICAL | `portals/homeloan/.env.local:2` | `generic-api-key` | Secret detected: Generic API Key |
| CRITICAL | `portals/land-mutation/.env.local:2` | `generic-api-key` | Secret detected: Generic API Key |
| CRITICAL | `portals/cbslanding/.env.local:2` | `generic-api-key` | Secret detected: Generic API Key |
| CRITICAL | `portals/shared/QrVerifier.tsx` | `high-ccn` | Function has cyclomatic complexity 25 |

### Issues by Category

| Category | Count |
|----------|-------|
| Secrets | 11 |
| Quality (complexity) | 10 |

### Compliance Results

| Standard | Pass | Partial | Fail |
|----------|------|---------|------|
| OWASP 2021 | 7 | 0 | 8 |
| NIST SP 800-53 | mapped | — | — |

---

## Screenshots

### Command Center — Dashboard Overview

![Command Center](screenshots/01-command-center.png)

The main dashboard shows live scan metrics: 21 total issues, 6 critical, debt score 11.1, Grade A, 130 modules, 11 secrets, 124s scan time. Includes Issues by Category donut chart and Top 5 Modules by Debt Score bar chart, plus the LLM-generated Executive Summary and Top Risks table.

---

### Scan History

![Scan History](screenshots/02-scan-history.png)

All past scans in one view. Columns: repository, language, grade, debt score, issue count, status, date. Supports reload, delete per job, and clear all history.

---

### Issue Tracker

![Issue Tracker](screenshots/03-issue-tracker.png)

Full findings table with filter by severity (critical/major/minor/info), category (secret/quality/misconfig/sca), and free-text search. Columns: severity badge, category, file:line, message, rule ID, CWE, tool. Export to CSV available.

---

### Code Analyzer AI

![Code Analyzer](screenshots/04-code-analyzer.png)

Paste any code snippet for instant LLM analysis without cloning a repo. Supports Full Analysis, IaC tools, Hardcoded Secrets, and Path Traversal modes.

---

### Code Graph

![Code Graph](screenshots/05-code-graph.png)

Interactive d3 dependency graph of the scanned repository. Nodes colored by severity — red = critical findings, green = clean. Click any node to see findings and debt score for that module.

---

### File Heatmap

![File Heatmap](screenshots/06-file-heatmap.png)

d3 treemap visualization of all 130 modules. Area = LOC, color = debt score (green → red). Instantly shows where technical debt is concentrated. Toggle between Severity and Churn views.

---

### Security Posture & OWASP Coverage

![Security Posture](screenshots/07-security-posture.png)

Security Score gauge, CWE distribution chart, and full OWASP Top 10 (2021) coverage table showing which categories have open findings. Secrets Found section lists all detected credentials with file:line references.

---

### Misconfiguration Radar

![Misconfig Radar](screenshots/08-misconfig-radar.png)

IaC misconfiguration findings from Checkov, Hadolint, and tfsec across Dockerfile, Terraform, Kubernetes manifests, and GitHub Actions. Each finding includes check ID, resource, file, and LLM-generated remediation.

---

### Compliance Dashboard

![Compliance Dashboard](screenshots/09-compliance-dashboard.png)

Coverage pie chart across OWASP 2021, NIST SP 800-53, and CWE. Control results table with pass/fail per control ID. Toggle between OWASP and NIST views. Export compliance PDF.

---

### Dependency Intelligence

![Dependency Intelligence](screenshots/10-dependency-intelligence.png)

All detected dependencies with CVE status. Badges: MANDATORY (CVSS ≥ 7), SUGGESTED, OPTIONAL, INFORMATIONAL. Shows current vs latest version and upgrade command.

---

### Advisory Feed — Live CVEs

![Advisory Feed](screenshots/11-advisory-feed.png)

Real-time CVE feed pulled from NVD CVE API v2, GitHub Advisory DB, and OSV.dev every 6 hours. Shows CVE ID, CVSS score, severity badge, affected package, and published date. Mark as read, filter by severity/source.

---

### Git Intelligence

![Git Intelligence](screenshots/12-git-intelligence.png)

Top 10 Churned Files bar chart (files most frequently modified = highest risk). Module Analysis table with 130 rows: module path, LOC, churn count, debt score, grade. High-churn + high-complexity files get a 3× debt multiplier.

---

### Trend Analysis

![Trend Analysis](screenshots/13-trend-analysis.png)

Cross-scan trend charts: Issues Over Time, Debt Score Trend, Severity Distribution. Summary stats: 2 total scans, 19 avg critical/scan, Grade A, avg debt score 10.9.

---

### Infrastructure Posture

![Infra Posture](screenshots/14-infra-posture.png)

Cloud and container infrastructure security findings from IaC scanners. Shows open S3 buckets, unencrypted storage, public IPs, privileged containers, and root user in Dockerfiles.

---

### Live Log Monitor

![Live Log](screenshots/15-live-log.png)

Real-time log stream from the backend pipeline. Filter by level (error/warning/info). Status bar shows error/warning/completed/total line counts. SSE-powered, no polling.

---

### EveBox — Suricata Event Viewer (Integrated)

![EveBox](screenshots/16-evebox.png)

EveBox (v0.24.0) is embedded in the DarkLead sidebar under Infrastructure. Connects to Suricata `eve.json` for network-level threat visibility alongside SAST findings. Shows Events by Type Over Time, Top Alerts, DNS, TLS SNI, source/destination IPs and ports.

---

### Update Center

![Update Center](screenshots/17-update-center.png)

Package upgrade recommendations classified as MANDATORY / SUGGESTED / OPTIONAL / INFORMATIONAL. Shows ecosystem, package, current version, latest version, CVEs, and one-click upgrade command.

---

### Post-Scan Actions — Remediation Board

![Post-Scan Remediation](screenshots/18-post-scan-remediation.png)

Kanban-style remediation board with assignee, status (open/in-progress/resolved), and CWE per finding. Shows 40% remediation rate, CI BLOCKED indicator. Automation Workflows and Action History tabs. Export CSV.

---

### Deploy Manager

![Deploy Manager](screenshots/19-deploy-manager.png)

Container orchestration view: 5/6 containers running (api-service, auth-service, redis, postgres, worker, nginx), v1.4.2 deployed, 99.7% uptime. CI/CD pipelines: Docker Build & Push ✓, K8s Rolling Deploy ✓, Terraform Plan ⏳, Staging Deploy ✗, Smoke Tests ✓.

---

### Pentest Studio

![Pentest Studio](screenshots/20-pentest-studio.png)

Integrated offensive security tool launcher for authorized testing. Tool library: Nmap, Nuclei, SQLMap, Gobuster, OWASP ZAP, Nikto, Hydra, Metasploit. Authorization-required warning enforced. Only run against systems you own or have explicit written permission to test.

---

### AI Assistant

![AI Assistant](screenshots/21-ai-assistant.png)

Context-aware LLM chat about the current scan. Left panel shows top vulnerabilities. Suggested questions: "What are the top 3 critical fixes?", "Is this project safe to deploy?", "Summarize all injection risks", "Which files need immediate attention", "What OWASP categories can we answer?", "Explain the worst vulnerability." Powered by Ollama or Anthropic Claude.

---

### Self-Health Monitor

![Self-Health](screenshots/22-self-health.png)

Platform health dashboard: API ✓ Online, Database ✓ Online, Redis ✓ Online, LLM Backend ✓ Online. Scanner availability grid (bandit, ruff, trivy, lizard, gitleaks, checker). LLM Models: phi4:latest, dolphin3:latest, qwen2.5-coder:14b, deepseek-r1:14b. System metrics: CVEs in queue, disk free, queue depth.

---

### Export Reports

![Export Reports](screenshots/23-export-reports.png)

One-click export for the QAVACH scan: JSON Export (machine-readable full report), PDF Report (print-ready with all compliance fields), CSV Export (issues spreadsheet). Share Link for team collaboration.

---

### Repository Comparison

![Repo Compare](screenshots/24-repo-compare.png)

Compare security posture across two previously scanned repositories side-by-side. Select baseline and comparison scan from history dropdown. Diff shows delta in debt score, issue count, and grade.

---

### Settings — API Keys

![Settings API Keys](screenshots/25-settings-api-keys.png)

Configure LLM providers: Anthropic Claude API key, Hugging Face token, Google Gemini API key. Keys persisted to `.env` server-side. Shows current connection status per provider.

---

### Settings — AI Models

![Settings AI Models](screenshots/26-settings-ai-models.png)

Full model catalog: **Ollama (Local)** — phi4:latest, dolphin3:latest, qwen2.5-coder:14b, deepseek-r1:14b (all online, local). **Hugging Face API** — Qwen2.5-Coder 32B/7B/V2 Lite, Qwen3 8B, DeepSeek-Coder 33B (premium). **Anthropic Claude** — Opus 4.6, Sonnet 4.6, Haiku 4.5 (not configured). **Google Gemini** — 2.5 Flash, 2.5 Pro (online).

---

## Default Login

| Field | Value |
|-------|-------|
| **Username** | `admin` |
| **Password** | `zero` |
| **Role** | Administrator |

Seeded automatically on first startup. Register additional accounts at `/register`.

---

## Quick Start

```bash
# Install dependencies
make install
ollama pull qwen2.5-coder:14b

# Start everything
make dev          # backend :7860 + frontend :5173

# Or separately
make backend      # FastAPI on :7860
make frontend     # Vite on :5173

# Optional: EveBox Suricata viewer
evebox server --port 5636 --host 0.0.0.0 --no-auth --sqlite --no-tls

# Login at http://localhost:5173/login
# Username: admin   Password: zero
```

---

## How It Works — 13-Step Pipeline

```
1. Clone          git clone with timeout, auto-detect language
2. LOC Count      count lines per module, compute git churn map
3. Scanner Ensemble  19 tools in parallel via asyncio.gather
4. Phase-1 Persist   raw results written to DB (~30s — visible immediately)
5. LLM Triage     false-positive filter, CWE/OWASP tagging (batch 20/call)
6. Fix Generation  compilable unified diffs for top-10 SAST findings
7. Misconfig Remediation  LLM remediation for top-5 IaC findings
8. Module Aggregation  debt score per module, churn + complexity multipliers
9. Compliance Mapping  OWASP 2021 + NIST SP 800-53 auto-tagging
10. Dep Updates   CVE match against detected dependencies
11. Summary       LLM executive narrative (3-4 sentences)
12. Phase-2 Persist  enriched results saved to DB
13. WebSocket     real-time progress events to browser throughout
```

---

## Technical Debt Score Formula

```
DebtScore = Σ ( severity_weight × churn_multiplier × complexity_factor ) / LOC × 1000

Severity weights:  CRITICAL=10  MAJOR=5  MINOR=2  INFO=0.5
churn_multiplier:  2.0× if file in top 20% by git commits
complexity_factor: 1.5× if cyclomatic complexity > 10
Both applied:      3.0× combined multiplier
```

| Grade | Score Range | Interpretation |
|-------|-------------|----------------|
| A | 0 – 10 | Excellent health, minimal debt |
| B | 11 – 25 | Good, minor issues to address |
| C | 26 – 50 | Moderate debt, plan remediation |
| D | 51 – 100 | High debt, address this sprint |
| F | 100+ | Critical — immediate action required |

---

## Scanner Catalog — 19 Tools

| Tool | Category | Language | What It Detects |
|------|----------|----------|-----------------|
| bandit | SAST | Python | SQL injection, shell injection, hardcoded credentials, weak crypto |
| ruff | SAST | Python | Style violations, unused imports, type errors, 400+ rules |
| semgrep | SAST | Python/JS/Java | OWASP Top 10 patterns, taint analysis |
| vulture | Quality | Python | Dead code: unused functions, variables, unreachable blocks |
| lizard | Complexity | Multi | Cyclomatic complexity, function length, parameter count |
| radon | Complexity | Python | Maintainability index, Halstead metrics, LOC counts |
| eslint | SAST | JavaScript | Security plugins, XSS, best practices |
| pmd | SAST | Java | Unused code, empty blocks, string handling |
| spotbugs | SAST | Java | Null dereference, infinite loops, resource leaks |
| gitleaks | Secrets | All | API keys, tokens, passwords, private keys in git history |
| detect-secrets | Secrets | All | Regex-based secret detection in current files |
| trivy | SCA | All | CVEs in OS packages, language deps, container layers |
| osv-scanner | SCA | All | OSV database lookup for all dependencies |
| pip-audit | SCA | Python | PyPI advisory database |
| npm-audit | SCA | JavaScript | npm advisory database |
| checkov | IaC | TF/K8s/CF | Terraform, Kubernetes, CloudFormation, GitHub Actions |
| hadolint | IaC | Docker | Dockerfile best practices |
| tfsec | IaC | Terraform | Open S3 buckets, unencrypted storage, public IPs |
| env-checker | Secrets | All | Committed .env files, exposed environment variables |

All 19 tools run **in parallel** via `asyncio.gather` — wall-clock time = slowest tool, not sum.

---

## LLM Fix Engine

After scanning, Claude Sonnet 4.6 (or Ollama locally) performs four tasks:

1. **Triage** — false-positive filter, assigns CWE ID + OWASP category + one-sentence explanation. Batched 20 findings per API call with prompt caching (~70% token cost reduction).
2. **Fix Generation** — compilable unified patch diffs for top-10 SAST findings. Full file content sent for context. Copy-paste ready.
3. **Misconfig Remediation** — step-by-step remediation for top-5 IaC findings.
4. **Executive Summary** — 3-4 sentence narrative with specific risk callouts and remediation priorities.

### Model Configuration

| Setting | Value |
|---------|-------|
| Default model | `claude-sonnet-4-6` |
| Override | `MODEL=` env var |
| Local fallback | Ollama `qwen2.5-coder:14b` |
| Triage timeout | 180s |
| Fix timeout | 180s |
| Summary timeout | 240s |
| Batch size | 20 findings/call |

---

## API Reference

All endpoints at `http://localhost:7860`. Auth: `Authorization: Bearer <jwt>`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/scan` | Submit GitHub repo URL for scanning |
| POST | `/api/scan/upload` | Upload zip/tar.gz archive |
| GET | `/api/scan/jobs` | List all scan jobs |
| DELETE | `/api/scan/jobs/{id}` | Delete single job |
| DELETE | `/api/scan/jobs` | Clear all history |
| GET | `/api/report/{id}` | Full report: issues, modules, misconfigs, compliance, summary |
| GET | `/api/export/{id}/pdf` | Download PDF report |
| GET | `/api/export/{id}/json` | Download JSON report |
| GET | `/api/export/{id}/csv` | Download issues CSV |
| POST | `/api/chat/{id}` | AI chat about scan (streaming) |
| POST | `/api/analyze/code` | Instant code snippet analysis |
| GET | `/api/advisories` | CVE advisory feed |
| GET | `/api/self-health` | Platform health snapshot |
| GET | `/api/ws/{id}` | WebSocket — real-time scan progress |
| GET | `/api/sse/alerts` | SSE — new critical CVE alerts |
| GET | `/health` | Service health check |

---

## Features at a Glance

| Feature | Detail |
|---------|--------|
| **19 SAST Tools** | bandit, ruff, semgrep, vulture, lizard, radon, eslint, pmd, spotbugs, gitleaks, detect-secrets, trivy, osv-scanner, pip-audit, npm-audit, checkov, hadolint, tfsec, env-checker |
| **Local LLM** | Ollama `qwen2.5-coder:14b` — 100% offline, no data leaves your machine |
| **Cloud LLM** | Anthropic Claude Sonnet 4.6, Google Gemini 2.5, Hugging Face Inference API |
| **JWT Auth** | Register / login / profile, 24-hour tokens, bcrypt passwords |
| **13-Step Pipeline** | clone → detect → LOC → scan → triage → fixes → misconfig → modules → compliance → updates → summary → persist → WebSocket |
| **Debt Score** | 0–100 composite with churn + complexity multipliers → A/B/C/D/F grade |
| **PDF/JSON/CSV Export** | Full compliance fields included |
| **OWASP/NIST** | Automatic CWE → OWASP 2021 → NIST SP 800-53 mapping |
| **AI Chat** | Context-aware LLM chat per scan with streaming responses |
| **Real-time** | WebSocket scan progress + SSE CVE advisory feed |
| **Advisory Feed** | NVD CVE API v2 + GitHub Advisory + OSV.dev polled every 6h |
| **Git Intelligence** | Churn heatmap, top churned files, module-level analysis |
| **Trend Analysis** | Cross-scan debt and issue count tracking |
| **EveBox** | Suricata EVE JSON viewer integrated in sidebar |
| **Pentest Studio** | Authorized tool launcher (Nmap, Nuclei, SQLMap, Metasploit…) |
| **Deploy Manager** | Container health, CI/CD pipeline status |
| **Remediation Board** | Kanban-style issue tracking with assignees and CI gate |
| **Repo Compare** | Side-by-side security posture comparison |
| **Self-Health** | Platform monitors its own scanners, DB, LLM, and disk |
| **20+ UI Panels** | FortiAnalyzer dark theme, Vue 3 + Vite + Tailwind |
| **Dark / Light Mode** | Toggled per-user, persisted in profile |
| **GitHub Webhook** | Auto-trigger scan on push |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, SQLAlchemy (SQLite), Celery, APScheduler |
| Frontend | Vue 3, Vite, Pinia, TypeScript, Tailwind CSS, ApexCharts, d3 |
| Auth | JWT (python-jose), bcrypt, OAuth2PasswordBearer |
| LLM | Ollama (local) / Anthropic Claude / Google Gemini / Hugging Face |
| Realtime | WebSocket (FastAPI), SSE, Redis pub/sub |
| Export | WeasyPrint (PDF), JSON, CSV |
| Container | Docker multi-stage (node-builder / py-builder / runtime) |
| CI/CD | GitHub Actions (test + build + bandit) |
| Network Intel | EveBox + Suricata EVE JSON |

---

## Documentation

| Page | Description |
|------|-------------|
| [Architecture](wiki/Architecture.md) | System design, 13-step pipeline, component map |
| [API Reference](wiki/API-Reference.md) | All REST/WS endpoints with schemas |
| [Scanner Catalog](wiki/Scanner-Catalog.md) | All 19 scanners and what they detect |
| [LLM Integration](wiki/LLM-Integration.md) | Ollama + Anthropic routing, prompts, caching |
| [Frontend Guide](wiki/Frontend-Guide.md) | Vue 3 dashboard, 20+ views, component library |
| [Database Schema](wiki/Database-Schema.md) | SQLAlchemy models, relationships |
| [Deployment Guide](wiki/Deployment-Guide.md) | Local dev, Docker, Hugging Face Spaces |
| [Configuration](wiki/Configuration.md) | All environment variables |
| [Scoring Formula](wiki/Scoring-Formula.md) | Debt score algorithm, grade thresholds |
| [Compliance Mapping](wiki/Compliance-Mapping.md) | OWASP 2021 + NIST SP 800-53 |
| [Developer Guide](wiki/Developer-Guide.md) | Adding scanners, tests, contributing |
| [AI Attribution](wiki/AI-Attribution.md) | How Claude built this autonomously |

---

## Evaluation Axes vs SonarQube (PS29)

| Axis | SonarQube | DarkLead |
|------|-----------|---------|
| Accuracy | Single scanner | **Ensemble of 19** — higher recall |
| Fix quality | Generic advice | **Compilable unified diffs** |
| Speed | ~2 min on 10K LOC | **<60s on 10K LOC** (parallel) |
| Offline | No | **Yes — 100% offline with Ollama** |
| Secret detection | Limited | **4 dedicated tools** |
| IaC scanning | Limited | **Checkov + Hadolint + tfsec** |
| Compliance | OWASP only | **OWASP 2021 + NIST SP 800-53 + CWE** |
| LLM fixes | None | **Batch 20/call, prompt-cached** |
| CVE monitoring | Separate plugin | **Built-in, real-time NVD+OSV+GitHub** |
| Network intel | None | **EveBox + Suricata integration** |

---

*TENSOR'26 Hackathon — PS29 — Team DARKLEAD! — github.com/thw01f/TR-104-DarkLead*
