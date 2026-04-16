from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    anthropic_api_key: str = "sk-ant-changeme"
    model: str = "claude-sonnet-4-6"
    # Local LLM via Ollama
    use_local_llm: bool = False
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5-coder:14b"
    # Hugging Face Inference API
    hf_api_token: str = ""
    hf_model: str = "Qwen/Qwen2.5-Coder-32B-Instruct"
    # Google Gemini API
    gemini_api_key: str = ""
    # Infrastructure
    redis_url: str = "redis://localhost:6379/0"
    database_url: str = "sqlite:///./darklead.db"
    max_repo_size_mb: int = 200
    clone_timeout_s: int = 60
    llm_fix_batch_size: int = 20
    llm_misconfig_batch_size: int = 10
    advisory_poll_hours: int = 6
    self_health_interval_min: int = 5
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:7860"]
    github_token: Optional[str] = None
    nvd_api_key: Optional[str] = None
    debug: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
