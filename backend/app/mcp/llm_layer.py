import json
import asyncio
import logging
from typing import List, Optional, Tuple
from ..config import settings
from .base import Finding

logger = logging.getLogger(__name__)


def _get_backend() -> tuple[str, str]:
    """Returns (provider, model) respecting runtime override → env config."""
    try:
        from ..routes.models import get_runtime_override
        ov = get_runtime_override()
        if ov.get("provider") and ov.get("model"):
            return ov["provider"], ov["model"]
    except Exception:
        pass
    # Explicit local mode → Ollama first
    if settings.use_local_llm:
        return "ollama", settings.ollama_model
    # HF token set → prefer HF
    if settings.hf_api_token and settings.hf_api_token.startswith("hf_"):
        return "huggingface", settings.hf_model
    # Gemini as fallback cloud option
    if settings.gemini_api_key and len(settings.gemini_api_key) > 10:
        return "gemini", "gemini-2.5-flash"
    if settings.anthropic_api_key.startswith("sk-ant-your") or settings.anthropic_api_key == "sk-ant-changeme":
        return "ollama", settings.ollama_model
    return "anthropic", settings.model


def _is_local() -> bool:
    provider, _ = _get_backend()
    return provider == "ollama"


def _call_anthropic(messages: list, max_tokens: int = 4096, model: str | None = None) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    resp = client.messages.create(
        model=model or settings.model, max_tokens=max_tokens, messages=messages,
    )
    return resp.content[0].text


def _call_ollama(messages: list, max_tokens: int = 4096, model: str | None = None) -> str:
    import httpx
    payload = {
        "model": model or settings.ollama_model,
        "messages": messages,
        "stream": False,
        "options": {"num_predict": max_tokens, "temperature": 0.1},
    }
    resp = httpx.post(f"{settings.ollama_url}/api/chat", json=payload, timeout=240.0)
    resp.raise_for_status()
    return resp.json()["message"]["content"]


def _call_huggingface(messages: list, max_tokens: int = 4096, model: str | None = None) -> str:
    import httpx
    m = model or settings.hf_model
    url = f"https://router.huggingface.co/hf-inference/models/{m}/v1/chat/completions"
    payload = {
        "model": m,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.1,
        "stream": False,
    }
    headers = {
        "Authorization": f"Bearer {settings.hf_api_token}",
        "Content-Type": "application/json",
    }
    resp = httpx.post(url, json=payload, headers=headers, timeout=120.0)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _call_gemini(messages: list, max_tokens: int = 4096, model: str | None = None) -> str:
    import httpx
    m = model or "gemini-2.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    payload = {
        "model": m,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.1,
    }
    headers = {
        "Authorization": f"Bearer {settings.gemini_api_key}",
        "Content-Type": "application/json",
    }
    resp = httpx.post(url, json=payload, headers=headers, timeout=120.0)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _call(messages: list, max_tokens: int = 4096) -> str:
    provider, model = _get_backend()
    if provider == "ollama":
        return _call_ollama(messages, max_tokens, model)
    if provider == "huggingface":
        return _call_huggingface(messages, max_tokens, model)
    if provider == "gemini":
        return _call_gemini(messages, max_tokens, model)
    return _call_anthropic(messages, max_tokens, model)

def _extract_json(text: str) -> dict:
    """Strip markdown fences and parse first JSON object/array found."""
    import re
    text = re.sub(r"^```[a-z]*\n?", "", text.strip(), flags=re.MULTILINE)
    text = re.sub(r"\n?```$", "", text.strip(), flags=re.MULTILINE)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]+\}", text)
        if m:
            return json.loads(m.group())
        return {}


def _call_with_retry(messages: list, max_tokens: int = 1024, retries: int = 2) -> str:
    """Call LLM with simple retry + backoff for rate limits."""
    import time
    for attempt in range(retries + 1):
        try:
            return _call(messages, max_tokens)
        except Exception as e:
            if "429" in str(e) and attempt < retries:
                time.sleep(2 ** attempt)
                continue
            raise


async def triage_findings(findings: list) -> list:
    """Enrich top-priority findings with LLM explanations, CWE IDs, OWASP categories."""
    if not findings:
        return findings
    loop = asyncio.get_event_loop()
    result = list(findings)
    sev_order = {"critical": 0, "major": 1, "minor": 2, "info": 3}
    priority = sorted(range(len(findings)), key=lambda i: sev_order.get(findings[i].severity, 4))[:20]
    batch_size = min(settings.llm_fix_batch_size, 20)
    for chunk_start in range(0, len(priority), batch_size):
        idxs = priority[chunk_start:chunk_start + batch_size]
        batch = [findings[i] for i in idxs]
        items = [{"idx": j, "rule": f.rule_id or "", "sev": f.severity,
                  "file": f.file_path, "line": f.line_start, "msg": f.message[:150]}
                 for j, f in enumerate(batch)]
        prompt = (
            "Security expert: enrich these findings with CWE ID, OWASP category, 1-sentence explanation.\n"
            'JSON array only: [{"idx":0,"cwe_id":"CWE-89","owasp":"A03:2021","explanation":"..."},...]\n\n'
            f"{json.dumps(items)}"
        )
        try:
            raw = await loop.run_in_executor(None, lambda p=prompt: _call_with_retry(
                [{"role": "user", "content": p}], 1024))
            enriched = _extract_json(raw)
            if isinstance(enriched, list):
                for e in enriched:
                    j = e.get("idx", -1)
                    if 0 <= j < len(batch):
                        if e.get("cwe_id"):      batch[j].cwe_id = e["cwe_id"]
                        if e.get("owasp"):       batch[j].owasp_category = e["owasp"]
                        if e.get("explanation"): batch[j].llm_explanation = e["explanation"]
        except Exception as ex:
            logger.warning(f"Triage batch {chunk_start} failed: {ex}")
    return result


async def generate_fixes(findings: list, repo_path: str, language: str, standards_doc) -> list:
    """Generate fix diffs for top findings. Returns list of (Finding, diff_str) tuples."""
    if not findings:
        return []
    from pathlib import Path
    loop = asyncio.get_event_loop()
    sev_order = {"critical": 0, "major": 1, "minor": 2, "info": 3}
    to_fix = sorted(findings, key=lambda f: sev_order.get(f.severity, 4))[:10]
    fix_ids = {id(f) for f in to_fix}
    to_skip = [f for f in findings if id(f) not in fix_ids]
    results: list = [(f, "") for f in to_skip]
    batch_size = min(settings.llm_fix_batch_size, 5)
    for i in range(0, len(to_fix), batch_size):
        batch = to_fix[i:i + batch_size]
        snippets = []
        for f in batch:
            try:
                fp = Path(repo_path) / f.file_path
                lines = fp.read_text(errors="replace").splitlines()
                start = max(0, f.line_start - 3)
                end = min(len(lines), (f.line_end or f.line_start) + 3)
                snippet = "\n".join(lines[start:end])
            except Exception:
                snippet = ""
            snippets.append({"rule": f.rule_id or f.message[:60], "file": f.file_path,
                              "line": f.line_start, "snippet": snippet[:300]})
        prompt = (
            f"Fix these {language} security issues. Minimal unified diff per item.\n"
            'JSON array: [{"idx":0,"diff":"--- a/f\\n+++ b/f\\n@@...@@\\n-old\\n+new"},...]\n\n'
            f"{json.dumps(snippets)}"
        )
        try:
            raw = await loop.run_in_executor(None, lambda p=prompt: _call_with_retry(
                [{"role": "user", "content": p}], 2048))
            fixes = _extract_json(raw)
            fix_map = {}
            if isinstance(fixes, list):
                fix_map = {item.get("idx", -1): item.get("diff", "") for item in fixes}
            for j, f in enumerate(batch):
                results.append((f, fix_map.get(j, "")))
        except Exception as ex:
            logger.warning(f"Fix batch {i} failed: {ex}")
            results.extend((f, "") for f in batch)
    return results


async def generate_misconfig_remediation(findings: list, repo_path: str) -> list:
    """Generate remediation advice for misconfig findings. Returns (Finding, advice) tuples."""
    if not findings:
        return []
    loop = asyncio.get_event_loop()
    results = []
    to_process = findings[:20]
    results.extend((f, "Review and apply security best practices for this configuration.")
                   for f in findings[20:])
    for f in to_process:
        prompt = (
            f"Infrastructure misconfig:\nFile: {f.file_path}\nIssue: {f.message}\n"
            "2-sentence remediation. Plain text only."
        )
        try:
            advice = await loop.run_in_executor(None, lambda p=prompt: _call_with_retry(
                [{"role": "user", "content": p}], 256))
            results.append((f, advice.strip()))
        except Exception:
            results.append((f, "Review and apply security best practices for this configuration."))
    return results


async def generate_summary(repo_url: str, language: str, stats: dict,
                           top_issues: list, top_mods: list) -> str:
    """Generate executive summary narrative for the scan report."""
    prompt = (
        f"Write a 3-4 sentence executive security summary for a {language} repo: {repo_url}\n"
        f"Stats: {json.dumps(stats)}\n"
        f"Top issues: {json.dumps(top_issues[:5])}\n"
        f"Riskiest modules: {json.dumps(top_mods)}\n"
        "Be specific, actionable, professional. Plain text."
    )
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, lambda: _call(
            [{"role": "user", "content": prompt}], 512))
    except Exception:
        c = stats.get("critical", 0)
        return (f"Analysis of {repo_url} found {stats.get('total', 0)} issues "
                f"({c} critical). Immediate remediation recommended for critical findings.")


async def analyze_code_snippet(code: str, language: str, filename: str, mode: str) -> dict:
    prompt = (
        f"Analyze this {language} code snippet for security vulnerabilities, bugs, and code smells.\n"
        f"File: {filename}\nMode: {mode}\n\n```{language}\n{code}\n```\n\n"
        "Return JSON: {\"summary\": str, \"severity\": \"critical|major|minor|info\", "
        "\"findings\": [{\"line\": int, \"rule\": str, \"severity\": str, \"message\": str, \"fix\": str}], "
        "\"debt_score\": float 0-10, \"grade\": \"A-F\"}"
    )
    messages = [{"role": "user", "content": prompt}]
    loop = asyncio.get_event_loop()
    raw = await loop.run_in_executor(None, lambda: _call(messages, 2048))
    result = _extract_json(raw)
    if not result:
        result = {"summary": raw[:500], "severity": "info", "findings": [], "debt_score": 0.0, "grade": "A"}
    return result


async def chat_stream(message: str, job_id: str, history: list, context: list, _: str) -> str:
    sys_prompt = (
        "You are DarkLead's AI assistant. Answer questions about the scan results concisely. "
        "Use the provided context findings to give precise, actionable answers."
    )
    ctx_text = json.dumps(context, indent=2) if context else "No specific findings matched."
    messages = [{"role": "system", "content": f"{sys_prompt}\n\nRelevant findings:\n{ctx_text}"}]
    messages.extend(history[-8:])
    messages.append({"role": "user", "content": message})
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: _call(messages, 1024))
