
# DarkLead — AI-Powered Code Review & Technical Debt Analyzer

---
title: DarkLead
emoji: 🔍
colorFrom: violet
colorTo: orange
sdk: docker
app_port: 7860
---

> **TENSOR'26 Hackathon — PS29** | Team DARKLEAD! | Built by Claude Sonnet 4.6 + w01f

[![Build](https://img.shields.io/badge/build-passing-brightgreen)](#)
[![Grade](https://img.shields.io/badge/self--scan-Grade%20A-brightgreen)](#)
[![LLM](https://img.shields.io/badge/LLM-Ollama%20%7C%20Anthropic-orange)](#)
[![Commits](https://img.shields.io/badge/commits-303-blue)](#)
[![AI](https://img.shields.io/badge/built%20by-Claude%20Sonnet%204.6-blueviolet)](#)

DarkLead is a production-grade SAST platform combining **19 static analysis tools** + **local LLM analysis** (Ollama `qwen2.5-coder:14b`) with a professional FortiAnalyzer-themed dashboard.

---

## Documentation

| Page | Description |
|------|-------------|
| [Architecture](wiki/Architecture.md) | System design, 13-step pipeline, component map |
| [API Reference](wiki/API-Reference.md) | All REST/WS endpoints with schemas |
| [Scanner Catalog](wiki/Scanner-Catalog.md) | All 19 scanners and what they detect |
| [LLM Integration](wiki/LLM-Integration.md) | Ollama + Anthropic routing, prompts |
| [Frontend Guide](wiki/Frontend-Guide.md) | Vue 3 dashboard, 20+ views, component library |
| [Database Schema](wiki/Database-Schema.md) | SQLAlchemy models, relationships |
| [Deployment Guide](wiki/Deployment-Guide.md) | Local dev, Docker, Hugging Face Spaces |
| [Configuration](wiki/Configuration.md) | All environment variables |
| [Scoring Formula](wiki/Scoring-Formula.md) | Debt score algorithm, grade thresholds |
| [Compliance Mapping](wiki/Compliance-Mapping.md) | OWASP 2021 + NIST SP 800-53 |
| [Developer Guide](wiki/Developer-Guide.md) | Adding scanners, tests, contributing |
| [AI Attribution](wiki/AI-Attribution.md) | How Claude built this autonomously |

---

## Quick Start

```bash
# Install
make install
ollama pull qwen2.5-coder:14b

# Start
make dev          # backend :7860 + frontend :5173

# Demo
open http://localhost:5173/?demo=demo-darklead-19c2af76
```

---

## Features

| Feature | Detail |
|---------|--------|
| **19 SAST Tools** | bandit, ruff, lizard, semgrep, gitleaks, trivy, pip-audit, npm-audit, checkov, hadolint, radon, vulture, osv-scanner, tfsec, eslint, pmd, spotbugs, env-checker, detect-secrets |
| **Local LLM** | Ollama `qwen2.5-coder:14b` — air-gapped analysis, no data leaves your machine |
| **13-step Pipeline** | clone → detect → LOC → scan → triage → fixes → misconfig → modules → compliance → updates → summary → persist → WebSocket |
| **Debt Score** | 0–100 composite → A/B/C/D/F grade |
| **SARIF Export** | GitHub Code Scanning compatible |
| **OWASP/NIST** | Automatic CWE → OWASP 2021 → NIST SP 800-53 mapping |
| **AI Chat** | Ask the LLM questions about any scan result |
| **Real-time** | WebSocket progress + SSE advisory feed |
| **GitHub Webhook** | Auto-trigger scan on push |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, SQLAlchemy (SQLite), APScheduler |
| Frontend | Vue 3, Vite, Tailwind, Pinia, ApexCharts, d3 |
| LLM | Ollama (qwen2.5-coder:14b) / Anthropic Claude |
| CI/CD | GitHub Actions (test + build + bandit) |
| Container | Docker multi-stage (node-builder / py-builder / runtime) |

---

*TENSOR'26 Hackathon — PS29 — Team DARKLEAD!*
