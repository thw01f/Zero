# DarkLead — System Architecture
**Team:** DARKLEAD! | **PS:** PS29 | **Hackathon:** TENSOR'26
**Vision:** Autonomous AI-driven code intelligence platform — scans, monitors, advises, and heals.

---

## 1. Problem Restatement (Expanded)

PS29 asks for an LLM-powered code review tool. We build that — and add the layer that makes it genuinely useful post-demo:

- **Static analysis** — smells, vulns, tech debt across Python / JS / Java
- **Dependency intelligence** — CVEs, stale packages, mandatory vs optional updates
- **Misconfiguration scanning** — Docker, K8s, Terraform, GitHub Actions, env files
- **Real-time advisory monitoring** — NVD, GitHub Advisory DB, OSV.dev, package changelogs
- **AI fix engine** — grounded, compilable fix diffs for every finding
- **Self-tracking** — the platform monitors its own health, deps, and scanner versions
- **Autonomous scheduling** — periodic re-scans, alert on new CVEs, no human trigger needed

Jury axes: accuracy vs SonarQube | fix acceptance rate | <60s on 10K LOC
Everything above those three axes is differentiation.

---

## 2. Architecture Diagram

```
╔══════════════════════════════════════════════════════════════════════╗
║                    BROWSER  (Vue 3 + Vite + TypeScript)             ║
║                                                                      ║
║  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  ║
║  │ Command  │ │  Issues  │ │ Heatmap  │ │   Fix    │ │   Dep    │  ║
║  │ Center   │ │  Table   │ │ d3 tree  │ │  Studio  │ │ Intel    │  ║
║  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  ║
║  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  ║
║  │ Misconfig│ │ Advisory │ │ Update   │ │Compliance│ │    AI    │  ║
║  │  Radar   │ │   Feed   │ │  Center  │ │Dashboard │ │Assistant │  ║
║  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  ║
║  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  ║
║  │   Git    │ │ Security │ │  Trend   │ │  Infra   │ │  Export  │  ║
║  │ Analytics│ │  Posture │ │ Analysis │ │ Posture  │ │& Reports │  ║
║  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  ║
╚══════════════════════════╤═══════════════════════════════════════════╝
                           │  REST + WebSocket + SSE
╔══════════════════════════▼═══════════════════════════════════════════╗
║                      FastAPI  (main.py)                             ║
║  /scan  /jobs  /report  /fixes  /chat  /monitor  /advisories        ║
║  /updates  /compliance  /export  /self-health  /ws  /sse/alerts     ║
╚══════╤══════════════════════════════════════╤════════════════════════╝
       │ enqueue                              │ SQLAlchemy ORM
╔══════▼══════════╗                  ╔════════▼═══════════════════════╗
║  Redis          ║                  ║  SQLite / Postgres             ║
║  • Task queue   ║                  ║  jobs, issues, modules         ║
║  • Pub/Sub WS   ║                  ║  advisories, projects          ║
║  • Result cache ║                  ║  updates, compliance, alerts   ║
╚══════╤══════════╝                  ╚════════════════════════════════╝
       │
╔══════▼══════════════════════════════════════════════════════════════╗
║                    Celery Workers  (4 concurrent)                  ║
║                                                                     ║
║  ┌─────────────────────────────────────────────────────────────┐   ║
║  │                  SCAN PIPELINE TASK                         │   ║
║  │  clone → detect → parallel scanners → triage → fix → agg   │   ║
║  └─────────────────────────────────────────────────────────────┘   ║
║  ┌─────────────────────────────────────────────────────────────┐   ║
║  │              MONITOR TASK  (scheduled, periodic)            │   ║
║  │  fetch NVD + GitHub Advisory + OSV → diff vs known →        │   ║
║  │  classify severity → push SSE alert → store in DB           │   ║
║  └─────────────────────────────────────────────────────────────┘   ║
║  ┌─────────────────────────────────────────────────────────────┐   ║
║  │              UPDATE INTELLIGENCE TASK                       │   ║
║  │  PyPI / npm / Maven latest → compare pinned →               │   ║
║  │  classify: MANDATORY / SUGGESTED / OPTIONAL                 │   ║
║  └─────────────────────────────────────────────────────────────┘   ║
║  ┌─────────────────────────────────────────────────────────────┐   ║
║  │              SELF-HEALTH TASK  (every 5 min)                │   ║
║  │  scanner versions → own deps → disk/mem → alert if stale    │   ║
║  └─────────────────────────────────────────────────────────────┘   ║
╚══════╤══════════════════════════════════════════════════════════════╝
       │
╔══════▼══════════════════════════════════════════════════════════════╗
║              MCP TOOL ORCHESTRATOR                                  ║
║                                                                     ║
║  SAST            SECRETS        DEPS           MISCONFIG            ║
║  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐        ║
║  │ Semgrep  │   │ Gitleaks │   │  Trivy   │   │ Checkov  │        ║
║  │ Bandit   │   │detect-sec│   │ OSV-Scan │   │ Hadolint │        ║
║  │ Ruff     │   └──────────┘   │ npm-audit│   │  tfsec   │        ║
║  │ ESLint   │                  │ pip-audit│   │kube-score│        ║
║  │ PMD      │   COMPLEXITY     │ OWASP-DC │   └──────────┘        ║
║  │ SpotBugs │   ┌──────────┐   └──────────┘                        ║
║  │ Vulture  │   │  Lizard  │                  INFRA                 ║
║  └──────────┘   │ Radon    │                  ┌──────────┐          ║
║                 └──────────┘                  │docker-bch│          ║
║                                               │env-check │          ║
║                                               └──────────┘          ║
╚══════╤══════════════════════════════════════════════════════════════╝
       │  raw findings (JSON)
╔══════▼══════════════════════════════════════════════════════════════╗
║              LLM REASONING LAYER  (Claude Sonnet 4.6)              ║
║                                                                     ║
║  • Triage + deduplicate findings                                    ║
║  • Fix generation (grounded on file context + standards RAG)       ║
║  • Misconfiguration remediation guidance                           ║
║  • Update impact analysis (is this update safe to apply?)          ║
║  • Compliance mapping (OWASP / CWE / NIST)                         ║
║  • Executive summary narrative                                      ║
║  • Interactive chat (RAG over repo + findings)                     ║
╚═════════════════════════════════════════════════════════════════════╝

╔═════════════════════════════════════════════════════════════════════╗
║              ADVISORY MONITORING ENGINE  (background)              ║
║                                                                     ║
║  Sources:  NVD API v2  │  GitHub Advisory DB  │  OSV.dev API       ║
║            PyPI RSS    │  npm audit advisories  │  Snyk DB (OSS)   ║
║                                                                     ║
║  Flow: fetch every 6h → match against project deps →               ║
║        classify NEW/UPDATED/RESOLVED → SSE push to browser →       ║
║        store in advisories table → badge on dashboard              ║
╚═════════════════════════════════════════════════════════════════════╝
```

---

## 3. The 16-Panel Dashboard

| # | Panel | Key Features |
|---|-------|-------------|
| 1 | **Command Center** | Overall health score (0–100), live alert ticker (SSE), critical issue count badges, last scan time, self-health indicator, recent activity feed |
| 2 | **Issues Table** | Filterable by severity/category/tool/file; sortable; bulk accept/dismiss; OWASP/CWE tag per issue; LLM explanation inline |
| 3 | **Heatmap** | d3 treemap — nodes sized by LOC, colored by debt score; click → module issues; toggle: color by severity / debt / churn / complexity |
| 4 | **Fix Studio** | diff2html side-by-side per issue; Accept/Reject/Modify; AI chat inline ("explain this fix"); acceptance rate tracker; copy-to-clipboard |
| 5 | **Dependency Intelligence** | CVE table (CVSS score, affected versions, fix version, advisory link); dependency graph (d3 force); age/staleness sparkline per package |
| 6 | **Update Center** | All deps with current vs latest version; update classification badge (MANDATORY/SUGGESTED/OPTIONAL/INFORMATIONAL); one-click upgrade command copy; changelog diff summary (LLM) |
| 7 | **Misconfiguration Radar** | Checkov/Hadolint/tfsec findings; grouped by resource type (Docker, K8s, Terraform, GH Actions, .env); risk level; remediation snippet |
| 8 | **Advisory Feed** | Live NVD + GitHub Advisory + OSV stream; filter by ecosystem; severity pill; "affects this project" flag; link to advisory; mark-as-read |
| 9 | **Security Posture** | OWASP Top 10 coverage matrix; secrets detected (type, file, never value); hardcoded creds; insecure patterns by category |
| 10 | **Compliance Dashboard** | OWASP Top 10 heatmap (A1–A10); CWE mapping; NIST CSF alignment; pass/fail per control; exportable compliance report |
| 11 | **Git Intelligence** | Churn × complexity scatter (hotspots); commit frequency timeline; most-changed files; author risk distribution; bus factor estimate |
| 12 | **Trend Analysis** | Multi-scan comparison (debt score over time, issue count over time); regression detection (new issues since last scan); sparklines per module |
| 13 | **Infrastructure Posture** | Docker image scan (Trivy); env file checks; exposed ports in compose files; hardcoded IPs; insecure bind mounts |
| 14 | **AI Assistant** | Chat interface — RAG over repo files + findings; ask "why is this critical?", "how do I fix all XSS?", "is this dep safe to update?"; conversation history |
| 15 | **Self-Health Monitor** | DarkLead's own scanner versions vs latest; own dep CVEs; disk/memory usage; last successful monitor run; scheduler status |
| 16 | **Export & Reports** | PDF report (executive + technical); JSON full export; CSV issues list; shareable permalink; mini research paper template (Phase 5) |

---

## 4. Advisory Monitoring Engine

### Sources
| Source | API | Data | Poll Interval |
|--------|-----|------|--------------|
| NVD v2 | `services.nvd.nist.gov/rest/json/cves/2.0` | CVEs by CPE | 6h |
| GitHub Advisory DB | `api.github.com/graphql` | Ecosystem advisories | 6h |
| OSV.dev | `api.osv.dev/v1/query` | OSS vulns by package | 6h |
| PyPI RSS | `pypi.org/rss/updates.xml` | New package releases | 1h |
| npm registry | `registry.npmjs.org/{pkg}` | Latest versions | 1h |
| Maven Central | `search.maven.org/solrsearch` | Java artifact updates | 6h |

### Update Classification Logic
```
MANDATORY  → CVSS ≥ 7.0  OR  "auth bypass" / "RCE" / "hardcoded" in advisory text
SUGGESTED  → CVSS 4.0–6.9  OR  security patch (semver patch with CVE fix)
OPTIONAL   → Minor/patch with no CVE  OR  new features only
INFORMATIONAL → Major version bump (breaking changes expected, human review needed)
```

---

## 5. Misconfiguration Scanner Coverage

| Tool | Targets | Example Findings |
|------|---------|-----------------|
| Checkov | Terraform, K8s YAML, Docker, GH Actions, CloudFormation | IAM wildcard perms, unencrypted S3, privileged containers |
| Hadolint | Dockerfile | RUN apt without pinned versions, ADD instead of COPY, root USER |
| tfsec | Terraform | Open security groups, unencrypted EBS, public S3 buckets |
| kube-score | Kubernetes manifests | No resource limits, no liveness probes, latest image tag |
| docker-bench | docker-compose.yml | Exposed secrets in env, insecure port bindings, missing healthchecks |
| env-checker | .env, config files | Exposed API keys, weak passwords, debug flags in production |

---

## 6. Self-Health Monitoring

The platform monitors itself autonomously every 5 minutes:
- Scanner binary versions vs latest GitHub releases
- Own Python/npm dependency CVEs (pip-audit on its own requirements.txt)
- Disk space on clone temp dir
- Redis queue depth (alert if >10 pending)
- Last successful advisory poll timestamp
- Celery worker heartbeat

Self-health data is exposed on `/self-health` endpoint and rendered in Panel 15.

---

## 7. Technical Debt Score Formula

```
DebtScore(module) =
    0.35 × severity_weighted_issues    # Critical=10, Major=5, Minor=1; per KLOC
  + 0.20 × complexity_avg              # Lizard CCN; normalized to max in repo
  + 0.20 × churn_complexity_product    # (churn/max_churn) × (complexity/max_complexity)
  + 0.15 × dep_staleness               # fraction of deps with known CVE or >2 majors behind
  + 0.10 × test_coverage_gap           # 1 − (test_files / src_files)

Score: 0–100. Grade: A(<20) B(<40) C(<60) D(<80) F(≥80)
```

---

## 8. LLM Calls Per Scan (Claude Sonnet 4.6)

| Call | Input | Output | When |
|------|-------|--------|------|
| Triage | Raw findings JSON | Deduplicated + severity-normalized + llm_explanation | After all scanners |
| Fix generation | Per-issue: file context + rule + standards RAG | Unified diff or SKIP | Top 20 by severity |
| Misconfig remediation | Checkov/Hadolint finding + resource YAML/HCL | Corrected config snippet | Top 10 misconfigs |
| Update analysis | Package + old ver + new ver + changelog | Impact summary + safe? | Per update |
| Compliance mapping | Issue list | OWASP/CWE/NIST mapping table | Post-triage |
| Summary | Stats + top issues + modules | 3-paragraph executive narrative | Final |
| Chat (RAG) | User question + repo context + findings | Conversational answer | On demand |

---

## 9. Deployment — HF Spaces Docker

Single Docker Space. Image budget: <4 GB.
- Multi-stage build: strip JRE with jlink, install only needed scanner binaries
- supervisord: uvicorn (port 7860) + celery worker -c 4 + redis-server
- APScheduler inside the FastAPI process for periodic monitoring tasks
- SQLite on persistent HF Spaces volume
- Frontend: pre-built `dist/` served by FastAPI StaticFiles

---

## 10. Non-Goals

- DAST / pentesting of the analyzed application (outside PS29 scope)
- Multi-user authentication / tenancy
- Real-time collaborative editing
- CI/CD pipeline integration hooks (future work)
- Cloud provider API integrations (AWS Inspector, etc.)

---

## 11. Risk Register

| Risk | Mitigation |
|------|-----------|
| NVD/GitHub API rate limits | Cache responses 6h; use ETags; fallback to OSV only |
| HF Spaces image >4 GB | jlink JRE; multi-stage; drop SpotBugs if needed |
| LLM hallucinated fix | Ground with 40-line context; label "AI-suggested, verify before apply" |
| Scanner binary unavailable in env | Graceful skip — `_available()` check; pipeline never blocks |
| Advisory feed empty / stale | Store last-known-good; show timestamp; never show empty as "no vulns" |
| Phase 1 time overrun | Tasks 1–14 are MVP (backend complete); Tasks 15–20 are frontend — jury sees API at 3:15 PM |
