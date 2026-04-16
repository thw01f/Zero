"""LLM model management — list available backends + runtime selection."""
from fastapi import APIRouter
import httpx
from ..config import settings

router = APIRouter(prefix="/models", tags=["models"])

ANTHROPIC_MODELS = [
    {"id": "claude-opus-4-6",           "name": "Claude Opus 4.6",   "provider": "anthropic", "context": "200K", "tier": "premium"},
    {"id": "claude-sonnet-4-6",         "name": "Claude Sonnet 4.6", "provider": "anthropic", "context": "200K", "tier": "balanced"},
    {"id": "claude-haiku-4-5-20251001", "name": "Claude Haiku 4.5",  "provider": "anthropic", "context": "200K", "tier": "fast"},
]

# Curated HF models best suited for code security analysis
HF_MODELS = [
    {
        "id":      "Qwen/Qwen2.5-Coder-32B-Instruct",
        "name":    "Qwen2.5-Coder 32B",
        "provider":"huggingface",
        "context": "128K",
        "tier":    "premium",
        "note":    "Best open code model · 2K ★",
    },
    {
        "id":      "Qwen/Qwen2.5-Coder-7B-Instruct",
        "name":    "Qwen2.5-Coder 7B",
        "provider":"huggingface",
        "context": "128K",
        "tier":    "fast",
        "note":    "Fast, 1.9M downloads",
    },
    {
        "id":      "deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct",
        "name":    "DeepSeek-Coder V2 Lite",
        "provider":"huggingface",
        "context": "128K",
        "tier":    "balanced",
        "note":    "16B MoE · 581 ★",
    },
    {
        "id":      "Qwen/Qwen3-8B",
        "name":    "Qwen3 8B (thinking)",
        "provider":"huggingface",
        "context": "128K",
        "tier":    "balanced",
        "note":    "Thinking mode · 8.6M downloads",
    },
    {
        "id":      "deepseek-ai/deepseek-coder-33b-instruct",
        "name":    "DeepSeek-Coder 33B",
        "provider":"huggingface",
        "context": "16K",
        "tier":    "premium",
        "note":    "Strong security analysis",
    },
    {
        "id":      "Qwen/Qwen2.5-32B-Instruct",
        "name":    "Qwen2.5 32B (general)",
        "provider":"huggingface",
        "context": "128K",
        "tier":    "premium",
        "note":    "General reasoning + code",
    },
]

# Ollama pull commands for upgrade suggestions
OLLAMA_UPGRADES = [
    {"tag": "qwen2.5-coder:32b",      "name": "Qwen2.5-Coder 32B",      "size": "~20 GB", "note": "Best local code model"},
    {"tag": "deepseek-coder-v2:16b",  "name": "DeepSeek-Coder V2 16B",  "size": "~10 GB", "note": "MoE, very accurate"},
    {"tag": "qwen2.5-coder:14b",      "name": "Qwen2.5-Coder 14B",      "size": "~9 GB",  "note": "Current default"},
    {"tag": "codellama:34b",          "name": "CodeLlama 34B",           "size": "~19 GB", "note": "Meta's code specialist"},
    {"tag": "qwen2.5-coder:7b",       "name": "Qwen2.5-Coder 7B",       "size": "~4.7 GB","note": "Fast, low VRAM"},
]

# Runtime override (reset on restart)
_override: dict = {"provider": None, "model": None}


@router.get("")
async def list_models():
    result: dict = {"current": _get_current(), "providers": {}}

    # Ollama — live model list from local daemon
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
        result["providers"]["ollama"] = {
            "name": "Ollama (Local)", "online": True, "models": ollama_models,
            "upgrades": OLLAMA_UPGRADES,
        }
    except Exception:
        result["providers"]["ollama"] = {
            "name": "Ollama (Local)", "online": False, "models": [],
            "upgrades": OLLAMA_UPGRADES,
        }

    # Hugging Face Inference API
    has_hf = bool(settings.hf_api_token and settings.hf_api_token.startswith("hf_"))
    result["providers"]["huggingface"] = {
        "name": "Hugging Face API", "online": has_hf, "models": HF_MODELS,
    }

    # Anthropic
    has_ant = bool(
        settings.anthropic_api_key
        and not settings.anthropic_api_key.startswith("sk-ant-your")
        and settings.anthropic_api_key != "sk-ant-changeme"
    )
    result["providers"]["anthropic"] = {
        "name": "Anthropic Claude", "online": has_ant, "models": ANTHROPIC_MODELS,
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
