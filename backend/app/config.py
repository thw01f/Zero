from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    anthropic_api_key: str = "sk-ant-changeme"
    model: str = "claude-sonnet-4-6"
    redis_url: str = "redis://localhost:6379/0"
    database_url: str = "sqlite:///./darklead.db"

    class Config:
        env_file = ".env"


settings = Settings()
