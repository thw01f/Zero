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
    resp = httpx.post(f"{settings.ollama_url}/api/chat", json=payload, timeout=240.0  # AI fix: 14b model needs longer cold-start time)
    resp.raise_for_status()
    return resp.json()["message"]["content"]


def _call(messages: list, max_tokens: int = 4096) -> str:
    if _is_local():
        return _call_ollama(messages, max_tokens)
    return _call_anthropic(messages, max_tokens)
