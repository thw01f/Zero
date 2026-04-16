import pytest
from app.config import settings


def test_settings_defaults():
    assert settings.model in ("claude-sonnet-4-6", "claude-opus-4-6")
    assert settings.max_repo_size_mb > 0
    assert settings.clone_timeout_s > 0


def test_ollama_config():
    assert settings.ollama_url.startswith("http")
    assert ":" in settings.ollama_model  # e.g. qwen2.5-coder:14b
