---
title: DarkLead — AI Code Intelligence Platform
emoji: 🔐
colorFrom: violet
colorTo: blue
sdk: docker
pinned: false
license: mit
app_port: 7860
---

# DarkLead

**AI-Powered Automated Code Review & Technical Debt Analyzer**

Built for TENSOR'26 Hackathon · PS29

## Features

- 20-tool scanner ensemble (SAST, SCA, Secrets, IaC, Container)
- LLM-powered triage, fix generation & remediation (Claude Sonnet 4.6)
- Real-time Technical Debt Score (A–F grade) with heatmap
- OWASP Top 10 + CWE Top 25 + NIST CSF compliance mapping
- Dependency update intelligence (MANDATORY / SUGGESTED / OPTIONAL)
- Advisory monitoring: NVD, GitHub Advisory DB, OSV.dev
- Self-health monitoring for the platform itself
- 16-panel dashboard with AI assistant chat

## Quick Start (Demo)

Visit the app and click **Load Demo** or open `/?demo=<job_id>` to explore a pre-seeded scan result with 19 findings, 10 modules, 6 misconfigs, and 12 compliance results.

## Local Dev

```bash
cd backend
pip install -r requirements.txt
python seed_demo.py          # seed demo data
uvicorn app.main:app --port 7860
```

```bash
cd frontend
npm install --legacy-peer-deps
npm run dev
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | Claude API key for LLM features |
| `REDIS_URL` | No | Redis for Celery (default: localhost) |
| `NVD_API_KEY` | No | NVD API key (5x rate limit) |
| `GITHUB_TOKEN` | No | GitHub token for Advisory DB |
