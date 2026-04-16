import json
import asyncio
import logging
from typing import List, Optional, Tuple
from ..config import settings
from .base import Finding

logger = logging.getLogger(__name__)


def _is_local() -> bool:
    if settings.use_local_llm:
        return True
    if settings.anthropic_api_key.startswith("sk-ant-your") or settings.anthropic_api_key == "sk-ant-changeme":
        return True
    return False


def _call_anthropic(messages: list, max_tokens: int = 4096) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    resp = client.messages.create(
        model=settings.model, max_tokens=max_tokens, messages=messages,
    )
    return resp.content[0].text


def _call_ollama(messages: list, max_tokens: int = 4096) -> str:
    import httpx
    payload = {
        "model": settings.ollama_model,
        "messages": messages,
        "stream": False,
        "options": {"num_predict": max_tokens, "temperature": 0.1},
    }
    resp = httpx.post(f"{settings.ollama_url}/api/chat", json=payload, timeout=240.0)
    resp.raise_for_status()
    return resp.json()["message"]["content"]


def _call(messages: list, max_tokens: int = 4096) -> str:
    if _is_local():
        return _call_ollama(messages, max_tokens)
    return _call_anthropic(messages, max_tokens)

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
