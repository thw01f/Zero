"""Runtime settings management — API keys and config (session-level, not persisted)."""
from fastapi import APIRouter
from ..config import settings

router = APIRouter(prefix="/settings", tags=["settings"])

# Runtime key overrides (cleared on restart)
_runtime_keys: dict = {}


def _mask(key: str) -> str:
    if not key or len(key) < 8:
        return ""
    return key[:6] + "…" + key[-4:]


@router.get("")
async def get_settings():
    """Return current config state (keys masked)."""
    ant_key = _runtime_keys.get("anthropic_api_key") or settings.anthropic_api_key
    hf_key  = _runtime_keys.get("hf_api_token")      or settings.hf_api_token
    gem_key = _runtime_keys.get("gemini_api_key")     or settings.gemini_api_key

    has_ant = bool(ant_key and not ant_key.startswith("sk-ant-your") and ant_key != "sk-ant-changeme")
    has_hf  = bool(hf_key and hf_key.startswith("hf_"))
    has_gem = bool(gem_key and len(gem_key) > 10)

    return {
        "keys": {
            "anthropic": {"set": has_ant, "masked": _mask(ant_key) if has_ant else ""},
            "huggingface": {"set": has_hf, "masked": _mask(hf_key) if has_hf else ""},
            "gemini": {"set": has_gem, "masked": _mask(gem_key) if has_gem else ""},
        },
        "scanner": {
            "max_repo_size_mb": settings.max_repo_size_mb,
            "clone_timeout_s": settings.clone_timeout_s,
            "llm_fix_batch_size": settings.llm_fix_batch_size,
            "advisory_poll_hours": settings.advisory_poll_hours,
        },
        "llm": {
            "ollama_url": settings.ollama_url,
            "ollama_model": settings.ollama_model,
            "use_local_llm": settings.use_local_llm,
        },
    }


@router.post("/keys")
async def set_keys(payload: dict):
    """Apply API keys at runtime (session-only, restart clears them).
    Accepted keys: anthropic_api_key, hf_api_token, gemini_api_key
    """
    updated = []
    for field in ("anthropic_api_key", "hf_api_token", "gemini_api_key"):
        val = payload.get(field, "").strip()
        if val:
            _runtime_keys[field] = val
            # Also patch settings object so llm_layer picks it up immediately
            setattr(settings, field, val)
            updated.append(field)
    return {"ok": True, "updated": updated}
