# CLAUDE.md — Project Context

You are the engineering agent for Team DARKLEAD! at the TENSOR'26 hackathon,
building PS29: an automated code review and technical-debt analyzer.

## Source of truth

Before any non-trivial task, re-read these:
- `ARCHITECTURE.md` — system design, rationale, eval strategy
- `SPEC.md` — data models, APIs, MCP tool catalog, LLM prompts, debt formula
- `PHASE1_PROMPTS.md` — the ordered task sequence this session is executing

When these conflict with your intuitions, the docs win.

## Working agreement

1. You write all code. The human reviews and approves commits. They do not type code.
2. After every task, run the specified tests. Only commit if they pass.
3. Commit messages follow Conventional Commits (feat/fix/chore/docs/test/refactor/ci).
   Subject line under 60 chars.
4. One task = one commit. Do not batch unrelated changes.
5. If a task is ambiguous, re-read SPEC.md. If still blocked, propose the most
   reasonable interpretation and proceed — do not stall for clarification
   unless the build would break.
6. Prefer standard library and mainstream packages. No exotic dependencies.
7. Python >= 3.11, Node >= 20. Pin versions. Use `pip install --break-system-packages` on Kali.
8. Every Python module has type hints. Every Vue component uses `<script setup lang="ts">`.
9. Never commit secrets or `.env` files.

## Model pin for generated code

The LLM calls in the generated backend use `MODEL=claude-sonnet-4-6` by default,
overridable via env var.

## Code style (generated Python/JS only — not YAML/JSON/docs)

- Compact spacing around operators/commas where it reads clearly.
  Example: `x=1,y=2` over `x = 1, y = 2`. Don't be dogmatic — readability first.
- Double quotes in Python, single quotes in JS.
- No gratuitous comments — self-explaining code.

## Team

w01f (IIT Madras, team lead). Repo on GitHub Classroom.
