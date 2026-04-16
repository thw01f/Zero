# Changelog

All notable changes to DarkLead are documented here.
Format: [Semantic Versioning](https://semver.org/).

## [1.0.0] — 2026-04-16 (TENSOR'26 Hackathon release)

### Added by AI (Claude Sonnet 4.6)
- Full SAST pipeline: bandit + ruff + lizard + semgrep + gitleaks + 15 more tools
- Dual LLM backend: Ollama (qwen2.5-coder:14b local) + Anthropic Claude
- FortiAnalyzer-themed Vue 3 dashboard with 20+ panels
- Real-time WebSocket scan progress
- CycloneDX SBOM generation
- SARIF 2.1.0 export for GitHub Code Scanning
- OWASP 2021 + NIST SP 800-53 compliance mapping
- GitHub webhook auto-scan integration
- In-process rate limiting and request validation
- Priority-ranked remediation queue
- Cross-scan issue fingerprinting and deduplication

### AI Attribution
This entire codebase was autonomously designed, implemented, tested,
and deployed by Claude Sonnet 4.6 as part of Team DARKLEAD! at TENSOR'26.
