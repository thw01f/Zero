# LLM Integration

DarkLead uses a **dual-backend LLM layer** that automatically routes to Ollama (local) or Anthropic (cloud) based on configuration.

---

## Backend Selection

```python
def _is_local() -> bool:
    """Return True if we should use Ollama instead of Anthropic."""
    return (
        settings.use_local_llm or
        settings.anthropic_api_key.startswith("sk-ant-your") or
        settings.anthropic_api_key == "sk-ant-changeme"
    )
```

| Condition | Backend used |
|-----------|-------------|
| `USE_LOCAL_LLM=true` in `.env` | Ollama |
| `ANTHROPIC_API_KEY` is placeholder | Ollama |
| Real Anthropic API key set | Anthropic Claude |

---

## Ollama Setup

### Installed Models

| Model | Size | Best for |
|-------|------|---------|
| `qwen2.5-coder:14b` | 9 GB | **Active default** — code analysis, fix generation |
| `phi4:latest` | 5.6 GB | Fallback — faster, less context |
| `dolphin3` | 4.9 GB | Uncensored variant |
| `deepseek-r1:14b` | 9 GB | Reasoning-heavy tasks |

### Ollama API Call

```python
async def _call_ollama(prompt: str, system: str = "", max_tokens: int = 2048) -> str:
    payload = {
        "model": settings.ollama_model,  # qwen2.5-coder:14b
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "options": {
            "num_predict": max_tokens,
            "temperature": 0.1   # Low temp for consistent structured output
        }
    }
    async with httpx.AsyncClient(timeout=240) as client:
        r = await client.post(f"{settings.ollama_url}/api/chat", json=payload)
    return r.json()["message"]["content"]
```

**Timeout:** 240 seconds (large models can be slow on first inference)  
**Temperature:** 0.1 — deterministic structured JSON output  
**Retry:** Exponential backoff, 3 attempts via `retry_async` decorator

---

## Anthropic Setup

```python
async def _call_anthropic(prompt: str, system: str = "", max_tokens: int = 2048) -> str:
    import anthropic
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    message = await client.messages.create(
        model=settings.model,  # claude-sonnet-4-6
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text
```

Set in `.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-api03-...
MODEL=claude-sonnet-4-6
USE_LOCAL_LLM=false
```

---

## LLM Tasks

### 1. Finding Triage

**When:** After all 19 scanners run (step 5 of pipeline)  
**Input:** List of raw scanner findings  
**Output:** Each finding enriched with CWE, OWASP, explanation

**System prompt:**
```
You are a senior application security engineer. You will receive a list of static
analysis findings from multiple tools. For each finding, provide:
- CWE identifier (e.g., CWE-78)
- OWASP 2021 category (e.g., A03:2021)
- A clear explanation of the security impact (2-3 sentences)
- Corrected severity if the scanner got it wrong

Return ONLY a JSON array. No markdown.
```

### 2. Fix Generation

**When:** Step 6, in batches of 20  
**Input:** Individual finding + surrounding code context  
**Output:** Diff-ready code fix with explanation

**System prompt:**
```
You are an expert code reviewer generating concrete fixes.
Given the vulnerable code and finding, produce:
1. The fixed code snippet
2. A one-line explanation of what changed and why

Return JSON: {"fixed_code": "...", "explanation": "..."}
```

### 3. Code Snippet Analysis (`/api/analyze/code`)

**Input:** Raw code paste, language, analysis mode  
**Output:** Score (0–100), grade, findings list, improvements

**System prompt (full mode):**
```
You are DarkLead's AI code reviewer. Analyze the provided {language} code for:
- Security vulnerabilities (injection, auth, crypto, secrets, SSRF…)
- Code quality issues (complexity, dead code, error handling…)
- Performance anti-patterns
- Maintainability concerns

Return ONLY valid JSON matching this schema:
{
  "overall_score": <0-100>,
  "overall_grade": "<A|B|C|D|F>",
  "summary": "<2-3 sentence executive summary>",
  "findings": [...],
  "improvements": [...]
}
```

### 4. Executive Summary

**When:** Step 11, after all findings collected  
**Input:** Aggregated finding counts, severity distribution, module breakdown  
**Output:** 3-paragraph executive summary + remediation roadmap

### 5. AI Chat

**When:** User asks question about a scan in the AIAssistant view  
**Context:** Full report JSON injected as system context  
**Output:** Conversational response referencing specific findings

---

## JSON Extraction

LLMs sometimes wrap JSON in markdown or add explanatory text. DarkLead's robust extractor handles this:

```python
def _extract_json(text: str) -> dict | list | None:
    # 1. Try markdown fence: ```json ... ```
    fence = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if fence:
        try: return json.loads(fence.group(1).strip())
        except: pass
    
    # 2. Try bare JSON object/array
    for start, end in [('{', '}'), ('[', ']')]:
        i = text.find(start)
        if i == -1: continue
        depth = 0
        for j in range(i, len(text)):
            if text[j] == start: depth += 1
            elif text[j] == end: depth -= 1
            if depth == 0:
                try: return json.loads(text[i:j+1])
                except: break
    
    return None
```

---

## Performance

| Operation | Ollama (qwen2.5-coder:14b) | Anthropic (claude-sonnet-4-6) |
|-----------|---------------------------|-------------------------------|
| Finding triage (20 findings) | 45–120s | 8–15s |
| Fix generation (1 finding) | 8–20s | 2–5s |
| Code snippet analysis | 15–40s | 3–8s |
| Executive summary | 20–60s | 5–10s |

**Tip:** First Ollama call loads the model (~20s). Subsequent calls are faster. Keep Ollama running.

---

## TTL Cache

Identical requests are cached in-process:

```python
from app.utils.cache import get, put

cache_key = {"code": code, "language": language, "mode": mode}
cached = get(cache_key, ttl=300)  # 5-minute TTL
if cached:
    return cached

result = await analyze_code_snippet(...)
put(cache_key, result)
return result
```
