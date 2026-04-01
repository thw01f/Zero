import json
import asyncio
import logging
import httpx
from pathlib import Path
from typing import List, Optional, Tuple
from ..config import settings
from .base import Finding

logger = logging.getLogger(__name__)


# ── LLM backend selection ─────────────────────────────────────────────────────

def _is_local() -> bool:
    """Use Ollama if configured or Anthropic key is a placeholder."""
    if settings.use_local_llm:
        return True
    if settings.anthropic_api_key.startswith("sk-ant-your") or settings.anthropic_api_key == "sk-ant-changeme":
        return True
    return False


def _call_anthropic(messages: list, max_tokens: int = 4096) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    resp = client.messages.create(
        model=settings.model,
        max_tokens=max_tokens,
        messages=messages,
    )
    return resp.content[0].text


def _call_ollama(messages: list, max_tokens: int = 4096) -> str:
    payload = {
        "model": settings.ollama_model,
        "messages": messages,
        "stream": False,
        "options": {"num_predict": max_tokens, "temperature": 0.1},
    }
    resp = httpx.post(
        f"{settings.ollama_url}/api/chat",
        json=payload,
        timeout=180.0,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"]


def _call(messages: list, max_tokens: int = 4096) -> str:
    if _is_local():
        return _call_ollama(messages, max_tokens)
    return _call_anthropic(messages, max_tokens)


def _extract_json(text: str):
    text = text.strip()
    if "```" in text:
        parts = text.split("```")
        for i, p in enumerate(parts):
            candidate = p.strip()
            if candidate.startswith("json"):
                candidate = candidate[4:].strip()
            if candidate.startswith("[") or candidate.startswith("{"):
                text = candidate
                break
    # Find first [ or { and last ] or }
    for start_char, end_char in [("[", "]"), ("{", "}")]:
        s = text.find(start_char)
        e = text.rfind(end_char)
        if s != -1 and e != -1 and e > s:
            try:
                return json.loads(text[s:e+1])
            except Exception:
                pass
    return json.loads(text)


# ── Core LLM functions ────────────────────────────────────────────────────────

async def triage_findings(findings: List[Finding]) -> List[Finding]:
    if not findings:
        return []
    try:
        raw = [f.__dict__ for f in findings]
        prompt = f"""You are a senior security engineer reviewing SAST output.

FINDINGS (JSON):
{json.dumps(raw, indent=2)}

Tasks:
1. Remove exact duplicates (same file_path+line_start+rule_id).
2. For near-duplicates (same file+line, different rules): keep highest severity.
3. Reassign severity: critical=RCE/SQLi/auth bypass/hardcoded secret, major=XSS/SSRF/path traversal/CCN>15, minor=smell/dead code, info=best practice.
4. Add "llm_explanation": one plain-English sentence per finding.
5. Add "owasp_category": nearest OWASP Top 10 2021 or null.
6. Add "cwe_id": nearest CWE ID string or null.

Return ONLY a valid JSON array. No text outside the array."""

        loop = asyncio.get_event_loop()
        text = await loop.run_in_executor(None, lambda: _call([{"role": "user", "content": prompt}]))
        data = _extract_json(text)
        result = []
        for item in data:
            f = Finding(**{k: item.get(k) for k in Finding.__dataclass_fields__ if k in item})
            f.llm_explanation = item.get("llm_explanation")
            f.owasp_category = item.get("owasp_category")
            f.cwe_id = item.get("cwe_id")
            result.append(f)
        return result
    except Exception as e:
        logger.warning(f"LLM triage failed: {e}")
        return findings


def _read_context(file_path: str, line_start: int, repo_path: str, window: int = 20) -> str:
    try:
        full_path = Path(repo_path) / file_path
        if not full_path.exists():
            full_path = Path(file_path)
        lines = full_path.read_text(errors="replace").splitlines()
        start = max(0, line_start - window - 1)
        end = min(len(lines), line_start + window)
        return "\n".join(lines[start:end])
    except Exception:
        return ""


async def generate_fixes(
    findings: List[Finding],
    repo_path: str,
    language: str,
    standards_doc: Optional[str],
) -> List[Tuple[Finding, Optional[str]]]:
    batch = sorted(findings, key=lambda f: {"critical": 0, "major": 1, "minor": 2, "info": 3}.get(f.severity, 4))
    batch = batch[:settings.llm_fix_batch_size]
    standards_section = f"\nCODING STANDARDS:\n{standards_doc[:2000]}" if standards_doc else ""

    async def fix_one(f: Finding) -> Tuple[Finding, Optional[str]]:
        context = _read_context(f.file_path, f.line_start, repo_path)
        if not context:
            return f, None
        try:
            prompt = f"""You are a senior engineer generating a minimal, compilable fix.

ISSUE: File={f.file_path} Line={f.line_start} Rule={f.rule_id} Severity={f.severity}
Message: {f.message}

FILE CONTEXT ({language}):
```{language}
{context}
```
{standards_section}

Produce a unified diff (--- original\\n+++ fixed) fixing ONLY this issue.
Must be syntactically valid {language}. Minimal change. Include imports if needed.
If uncertain: respond SKIP.
Return ONLY the unified diff or SKIP."""
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(None, lambda: _call([{"role": "user", "content": prompt}], 1024))
            text = text.strip()
            return f, None if text == "SKIP" else text
        except Exception as e:
            logger.warning(f"Fix gen failed for {f.rule_id}: {e}")
            return f, None

    results = await asyncio.gather(*[fix_one(f) for f in batch])
    return list(results)


async def generate_misconfig_remediation(
    misconfigs: List[Finding],
    repo_path: str,
) -> List[Tuple[Finding, str]]:
    batch = misconfigs[:settings.llm_misconfig_batch_size]

    async def remediate_one(f: Finding) -> Tuple[Finding, str]:
        context = _read_context(f.file_path, f.line_start, repo_path, window=30)
        try:
            prompt = f"""You are a DevSecOps engineer fixing a misconfiguration.

Tool={f.tool} Resource={f.resource_type} File={f.file_path}
Check={f.check_id} Issue={f.message} Severity={f.severity}

CURRENT CONFIG:
```
{context}
```

Provide the corrected configuration snippet fixing this specific issue.
Minimal change. Add a one-line comment explaining what you changed.
Return ONLY the corrected snippet."""
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(None, lambda: _call([{"role": "user", "content": prompt}], 512))
            return f, text.strip()
        except Exception as e:
            logger.warning(f"Remediation failed: {e}")
            return f, "See check documentation for remediation guidance."

    results = await asyncio.gather(*[remediate_one(f) for f in batch])
    return list(results)


async def generate_summary(repo_url: str, language: str, stats: dict, top_issues: list, top_modules: list) -> str:
    try:
        prompt = f"""You are a technical lead summarizing a code review.

Repo={repo_url} Language={language}
Total issues={stats.get('total',0)} (Critical={stats.get('critical',0)}, Major={stats.get('major',0)}, Minor={stats.get('minor',0)})
Debt Score={stats.get('debt_score',0)}/100 Grade={stats.get('grade','?')} Scan={stats.get('scan_ms',0)}ms
Misconfigs={stats.get('misconfigs',0)} Secrets={stats.get('secrets',0)} Mandatory updates={stats.get('mandatory_updates',0)}

TOP 10 ISSUES:
{json.dumps(top_issues, indent=2)}

TOP 5 MODULES:
{json.dumps(top_modules, indent=2)}

Write a 3-paragraph executive summary:
1. Overall health (2-3 sentences).
2. Top 3 priority remediation actions with one-sentence rationale each.
3. One positive observation if any exists.

Plain text, no headers or bullets. Max 200 words."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: _call([{"role": "user", "content": prompt}], 512))
    except Exception as e:
        logger.warning(f"Summary generation failed: {e}")
        return "Summary unavailable. Please review the findings manually."


async def chat_stream(
    question: str,
    job_id: str,
    history: list,
    relevant_findings: list,
    code_snippets: str,
) -> str:
    try:
        messages = []
        for turn in history[-10:]:
            messages.append({"role": turn["role"], "content": turn["content"]})

        context = f"""You are a code intelligence assistant for DarkLead.
Job: {job_id}

RELEVANT FINDINGS:
{json.dumps(relevant_findings[:5], indent=2)}

CODE CONTEXT:
{code_snippets[:2000]}"""

        messages.append({"role": "user", "content": f"{context}\n\nQuestion: {question}"})
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: _call(messages, 1024))
    except Exception as e:
        return f"Chat unavailable: {e}"


async def analyze_code_snippet(
    code: str,
    language: str,
    filename: str = "snippet",
    mode: str = "full",  # full | security | quality | improve
) -> dict:
    """
    Instant LLM analysis of a code snippet.
    Returns structured JSON with findings, improvements, and score.
    """
    mode_instructions = {
        "security": "Focus exclusively on security vulnerabilities: injection, auth bypass, secrets, insecure crypto, input validation, OWASP Top 10.",
        "quality": "Focus on code quality: complexity, dead code, naming, duplicates, SOLID violations, test coverage gaps.",
        "improve": "Focus on improvements: performance, readability, modern idioms, refactoring opportunities.",
        "full": "Cover all aspects: security vulnerabilities, code quality issues, and improvement suggestions.",
    }
    instruction = mode_instructions.get(mode, mode_instructions["full"])

    prompt = f"""You are an expert {language} code reviewer with deep knowledge of security and software engineering.

{instruction}

FILENAME: {filename}
LANGUAGE: {language}

CODE:
```{language}
{code[:8000]}
```

Analyze this code and return a JSON object with this exact structure:
{{
  "overall_score": <0-100, where 100 is perfect>,
  "overall_grade": <"A"|"B"|"C"|"D"|"F">,
  "summary": "<2-3 sentence executive summary>",
  "findings": [
    {{
      "line": <line_number>,
      "severity": <"critical"|"major"|"minor"|"info">,
      "category": <"security"|"quality"|"performance"|"style">,
      "rule": "<rule name>",
      "message": "<what is wrong>",
      "explanation": "<why this matters>",
      "cwe": "<CWE-XXX or null>",
      "owasp": "<A01:2021-... or null>"
    }}
  ],
  "improvements": [
    {{
      "priority": <1-5, 1=highest>,
      "title": "<improvement title>",
      "description": "<what and why>",
      "example": "<short code snippet showing the improvement, or null>"
    }}
  ],
  "metrics": {{
    "loc": <lines of code>,
    "complexity_estimate": <cyclomatic complexity estimate>,
    "security_issues": <count>,
    "quality_issues": <count>,
    "has_tests": <true|false>
  }}
}}

Return ONLY valid JSON. No text outside the JSON object."""

    loop = asyncio.get_event_loop()
    try:
        text = await loop.run_in_executor(None, lambda: _call([{"role": "user", "content": prompt}], 2048))
        return _extract_json(text)
    except Exception as e:
        logger.warning(f"Code analysis failed: {e}")
        return {
            "overall_score": 0,
            "overall_grade": "?",
            "summary": f"Analysis failed: {e}",
            "findings": [],
            "improvements": [],
            "metrics": {"loc": len(code.splitlines()), "complexity_estimate": 0, "security_issues": 0, "quality_issues": 0, "has_tests": False},
        }
