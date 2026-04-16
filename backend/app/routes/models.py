"""LLM model management — list available backends + runtime selection."""
from fastapi import APIRouter
import httpx
from ..config import settings

router = APIRouter(prefix="/models", tags=["models"])

ANTHROPIC_MODELS = [
    {"id": "claude-opus-4-6",           "name": "Claude Opus 4.6",    "provider": "anthropic", "context": "200K", "tier": "premium"},
    {"id": "claude-sonnet-4-6",         "name": "Claude Sonnet 4.6",  "provider": "anthropic", "context": "200K", "tier": "balanced"},
    {"id": "claude-haiku-4-5-20251001", "name": "Claude Haiku 4.5",   "provider": "anthropic", "context": "200K", "tier": "fast"},
]

# Runtime override (reset on restart)
_override: dict = {"provider": None, "model": None}


@router.get("")
async def list_models():
    result: dict = {"current": _get_current(), "providers": {}}

    # Ollama
    try:
        r = httpx.get(f"{settings.ollama_url}/api/tags", timeout=3.0)
        raw = r.json().get("models", [])
        ollama_models = [
            {
                "id":      m["name"],
                "name":    m["name"],
                "provider":"ollama",
                "size":    f"{m.get('size', 0) / 1_073_741_824:.1f} GB",
                "context": "128K",
                "tier":    "local",
            }
            for m in raw
        ]
        result["providers"]["ollama"] = {"name": "Ollama (Local)", "online": True,  "models": ollama_models}
    except Exception:
        result["providers"]["ollama"] = {"name": "Ollama (Local)", "online": False, "models": []}

    # Anthropic
    has_key = bool(
        settings.anthropic_api_key
        and not settings.anthropic_api_key.startswith("sk-ant-your")
        and settings.anthropic_api_key != "sk-ant-changeme"
    )
    result["providers"]["anthropic"] = {
        "name": "Anthropic Claude", "online": has_key, "models": ANTHROPIC_MODELS
    }

    return result


@router.post("/select")
async def select_model(payload: dict):
    provider = payload.get("provider", "")
    model    = payload.get("model", "")
    _override["provider"] = provider or None
    _override["model"]    = model    or None
    return {"ok": True, "provider": provider, "model": model}


@router.get("/current")
async def current_model():
    return _get_current()


def _get_current() -> dict:
    if _override.get("provider"):
        return {"provider": _override["provider"], "model": _override["model"]}
    if settings.use_local_llm or settings.anthropic_api_key.startswith("sk-ant"):
        return {"provider": "ollama", "model": settings.ollama_model}
    return {"provider": "anthropic", "model": settings.model}


def get_runtime_override() -> dict:
    """Called by llm_layer to respect the runtime selection."""
    return _override
