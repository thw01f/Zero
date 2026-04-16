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
    if settings.use_local_llm:
        return "ollama", settings.ollama_model
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


def _call(messages: list, max_tokens: int = 4096) -> str:
    provider, model = _get_backend()
    if provider == "ollama":
        return _call_ollama(messages, max_tokens, model)
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
