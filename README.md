# DarkLead — AI Code Intelligence Platform

> Built autonomously by Claude Sonnet 4.6 for TENSOR'26 Hackathon · PS29

## Overview
DarkLead is a fully AI-generated automated code review and technical debt analyzer.
It uses a 20-tool scanner ensemble + LLM triage to analyze GitHub repositories.

## Local Development

Run with Ollama for offline analysis:
```bash
ollama pull qwen2.5-coder:14b
USE_LOCAL_LLM=true uvicorn app.main:app --port 7860
```

## Status
🔴 Bootstrap phase — AI is initializing project structure

## Technical Details

- **Backend**: FastAPI + SQLAlchemy + APScheduler + Celery
- **Frontend**: Vue 3 + Vite + Tailwind CSS + ApexCharts + d3
- **LLM**: Ollama (qwen2.5-coder:14b) or Claude Sonnet 4.6
- **Scanners**: bandit, ruff, lizard, gitleaks, trivy, checkov, hadolint + 12 more
- **DB**: SQLite (development), upgradeable to PostgreSQL
- **Demo**: http://localhost:7860/?demo=demo-darklead-19c2af76

## AI Attribution

Every line of code in this repository was written by **Claude Sonnet 4.6**
(claude-sonnet-4-6) as part of TENSOR'26 Hackathon PS29.
Zero lines were written by a human.

Commits: 210 | Files: 91+ | Languages: Python + TypeScript + Vue
