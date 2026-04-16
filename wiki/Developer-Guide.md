# Developer Guide

---

## Prerequisites

```bash
# Required
python3 --version     # 3.11+
node --version         # 20+
ollama --version       # any recent

# Optional
redis-server --version # for Celery task queue
docker --version       # for container builds
```

## Quick Start

```bash
git clone git@github.com:thw01f/Zero.git darklead
cd darklead

# Install everything
make install

# Pull LLM model (9GB one-time download)
ollama pull qwen2.5-coder:14b
ollama serve  # Keep running in background

# Seed demo data
make seed

# Start development stack
make dev
```

---

## Running Tests

```bash
# All tests
make test

# Backend only
cd backend && pytest tests/ -v

# Specific test file
cd backend && pytest tests/test_secret_scanner.py -v

# With coverage
cd backend && pytest tests/ --cov=app --cov-report=html

# Frontend type check
cd frontend && npx vue-tsc --noEmit
```

### Test Files

| File | Tests |
|------|-------|
| `test_config.py` | Settings contract, env var loading |
| `test_debt_score.py` | Formula edge cases (0, 100, overflow) |
| `test_compliance.py` | OWASP/NIST mapping coverage |
| `test_api.py` | analyze endpoint request/response contract |
| `test_secret_scanner.py` | 6 credential pattern types |
| `test_rate_limiter.py` | Allow/block/reset behavior |
| `test_repo_validator.py` | SSRF + allowlist edge cases |
| `test_owasp_mapper.py` | CWE→OWASP mappings |
| `test_priority_scorer.py` | Remediation ranking logic |
| `test_sql_detector.py` | SQL injection pattern detection |
| `test_loc_counter.py` | Line counting + exclusions |
| `test_diff_utils.py` | Diff stats + patch generation |
| `test_async_helpers.py` | Timeout wrap + error handling |
| `test_text_utils.py` | JSON extraction + severity normalization |
| `test_code_detector.py` | Language auto-detection |
| `test_pattern_matcher.py` | Code smell detection |

---

## Adding a Scanner

### 1. Create the scanner class

```python
# backend/app/mcp/scanners/my_scanner.py
import subprocess
import json
from typing import Any

class MyScannerTool:
    name = "my_scanner"
    languages = ["python", "javascript"]  # or ["all"]
    
    async def run(self, repo_path: str, language: str) -> list[dict[str, Any]]:
        """Run scanner and return normalized findings."""
        if language not in self.languages and "all" not in self.languages:
            return []
        
        try:
            result = subprocess.run(
                ["my-scanner", "--json", repo_path],
                capture_output=True, text=True, timeout=60
            )
            return self._parse(result.stdout)
        except Exception:
            return []
    
    def _parse(self, output: str) -> list[dict[str, Any]]:
        try:
            data = json.loads(output)
        except Exception:
            return []
        
        findings = []
        for item in data.get("results", []):
            findings.append({
                "line": item.get("line"),
                "severity": self._map_severity(item.get("severity", "LOW")),
                "category": "security",  # or quality/performance/maintainability
                "rule": item.get("rule_id", "unknown"),
                "message": item.get("message", ""),
                "file_path": item.get("filename", ""),
                "tool": self.name,
            })
        return findings
    
    @staticmethod
    def _map_severity(s: str) -> str:
        return {"HIGH": "critical", "MEDIUM": "major", "LOW": "minor"}.get(s.upper(), "info")
```

### 2. Register in orchestrator

```python
# backend/app/mcp/orchestrator.py
from .scanners.my_scanner import MyScannerTool

SCANNERS = [
    BanditScanner(),
    RuffScanner(),
    ...
    MyScannerTool(),  # Add here
]
```

### 3. Add to health check

```python
# backend/app/routes/health.py
def _check_scanner(name: str, cmd: list[str]) -> bool:
    try:
        subprocess.run(cmd, capture_output=True, timeout=5)
        return True
    except Exception:
        return False

scanners = {
    ...
    "my_scanner": _check_scanner("my_scanner", ["my-scanner", "--version"]),
}
```

### 4. Write tests

```python
# backend/tests/test_my_scanner.py
from app.mcp.scanners.my_scanner import MyScannerTool

def test_finds_known_issue():
    # Create temp file with known vulnerability
    ...
```

---

## Adding a Frontend View

### 1. Create the Vue component

```typescript
// frontend/src/views/MyView.vue
<template>
  <div class="p-6">
    <div class="ft-card">
      <h2 class="text-lg font-bold text-white mb-4">My View</h2>
      <!-- content -->
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
const data = ref<any>(null)
onMounted(async () => {
  const r = await fetch('/api/my-endpoint')
  data.value = await r.json()
})
</script>
```

### 2. Register in router

```typescript
// frontend/src/router/index.ts
import MyView from '../views/MyView.vue'

const routes = [
  ...
  { path: '/my-view', component: MyView },
]
```

### 3. Add to sidebar nav in `App.vue`

```typescript
// In the navSections array
{
  label: 'MY SECTION',
  items: [
    { label: 'My View', path: '/my-view', icon: '🔍' },
  ]
}
```

---

## Code Style

### Python
- Type hints on all functions
- Double quotes
- Compact spacing: `x=1,y=2` over `x = 1, y = 2` where readable
- No gratuitous comments — code should be self-explaining

### TypeScript/Vue
- `<script setup lang="ts">` on all components
- Single quotes in JS/TS
- Pinia for cross-component state, `ref/computed` for local state

---

## Makefile Targets

```bash
make dev          # Start backend + frontend (requires two terminals)
make backend      # Backend only (:7860)
make frontend     # Frontend dev server (:5173)
make install      # Install all deps (pip + npm)
make test         # Run pytest
make lint         # ruff + vue-tsc
make seed         # Seed demo data
make docker-build # Build Docker image
make help         # Show all targets
```

---

## Project Conventions

- **One task = one commit** (see git log for examples)
- **Conventional Commits**: `feat(component): add X`, `fix(api): handle Y`, `test(ai): validate Z`
- **Every commit** includes `Co-authored-by: Claude Sonnet 4.6 <claude-ai@anthropic.com>`
- **No secrets in commits** — `.env` is gitignored
- **No exotic dependencies** — standard library + mainstream packages only
