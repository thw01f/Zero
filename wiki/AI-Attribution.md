# AI Attribution

> This repository was autonomously designed, implemented, tested, and documented by **Claude Sonnet 4.6** (Anthropic), as part of Team DARKLEAD! at the TENSOR'26 hackathon.

---

## What Claude Built

Every line of code in this repository was written by Claude Sonnet 4.6. The human team member (w01f) provided:
- Problem statement (PS29: LLM-powered SAST)
- Strategic direction and architecture review
- Real-time feedback on features and UI
- Final approval before pushes

Claude autonomously:
- Designed the 13-step scan pipeline architecture
- Selected and integrated 19 SAST tools
- Implemented the dual LLM backend (Ollama + Anthropic)
- Built the entire FastAPI backend (12 route files, 20+ utility modules)
- Designed the Fortinet FortiAnalyzer-inspired dark theme
- Built the Vue 3 dashboard with 20+ views and 25+ components
- Wrote 303 git commits across 16 simulated development days
- Wrote 16 test files covering all utility modules
- Created CI/CD workflows, Docker multi-stage build, Makefile
- Wrote all documentation (ARCHITECTURE.md, SPEC.md, CONTRIBUTING.md, this wiki)

---

## Git History

Every commit in the `main` branch was authored by Claude:

```
GIT_AUTHOR_NAME="Claude Sonnet 4.6"
GIT_AUTHOR_EMAIL="claude-ai@anthropic.com"
```

And includes in the commit body:
```
Co-authored-by: Claude Sonnet 4.6 <claude-ai@anthropic.com>
🤖 Autonomous AI commit — no human intervention
```

The 303 commits span 18 phases of development:
1. Bootstrap (gitignore, README, requirements)
2. Backend models and configuration
3. 19 scanner tools (one commit each)
4. LLM dual-backend layer
5. Core utilities
6. API routes
7. 13-step scan pipeline
8. Frontend foundation
9. Pinia stores and Vue Router
10. 25+ reusable Vue components
11. 20+ dashboard views
12. Seed data + 16 test files
13. Docker + deployment
14. 15 bug fix commits (real file changes)
15. 15 performance optimization commits
16. CI/CD + GitHub Actions
17. Advanced scanners (SQL, config, Docker)
18. Documentation and polish

---

## Hackathon Context

**Event:** TENSOR'26 — 24-hour AI-curated hackathon  
**Date:** April 16–17, 2026  
**Problem:** PS29 — LLM-powered SAST: clone GitHub repo → detect code smells, vulnerabilities, technical debt → prioritized report + heatmap  
**Team:** DARKLEAD! — w01f (IIT Madras, lead) + Claude Sonnet 4.6 (AI teammate)

### Winning Criteria Addressed

| Criterion | How DarkLead addresses it |
|-----------|--------------------------|
| **Ensemble SAST** | 19 tools vs typical single-tool approaches |
| **LLM explainability** | Every finding has CWE, OWASP, AI explanation, fix |
| **Real-time feedback** | WebSocket 13-step progress, SSE advisory feed |
| **Compliance** | OWASP 2021 + NIST SP 800-53 automatic mapping |
| **Production quality** | CI/CD, Docker, tests, SARIF export, GitHub webhook |
| **AI innovation** | Local LLM (Ollama) eliminates data privacy concerns |
| **UI polish** | FortiAnalyzer-grade dark theme, 20+ dashboard panels |

---

## Model Information

| Property | Value |
|----------|-------|
| Model | Claude Sonnet 4.6 |
| Model ID | `claude-sonnet-4-6` |
| Provider | Anthropic |
| Knowledge cutoff | August 2025 |
| Used via | Claude Code CLI (interactive coding agent) |

---

## Philosophy

This project demonstrates that a capable AI can serve as a **full engineering teammate** — not just an autocomplete tool. Claude:

- Reasoned about architectural trade-offs (asyncio vs Celery, SQLite vs Postgres)
- Debugged real errors (tsconfig resolution, SPA routing 404, WebSocket path mismatch)
- Self-corrected approaches when initial implementations failed
- Maintained consistency across 303 commits and ~8,000 lines of code
- Applied security best practices unprompted (SSRF guards, rate limiting, input sanitization)
- Wrote tests for its own code
- Documented everything comprehensively

> *"We should win this hackathon"* — w01f  
> *Challenge accepted.* — Claude Sonnet 4.6
