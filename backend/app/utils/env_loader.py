"""Load and validate required environment variables at startup."""
import os
from typing import Optional

def require_env(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise EnvironmentError(f"Required env var {key!r} is not set")
    return val

def optional_env(key: str, default: str = '') -> str:
    return os.getenv(key, default)

def bool_env(key: str, default: bool = False) -> bool:
    val = os.getenv(key, str(default)).lower()
    return val in ('1', 'true', 'yes', 'on')

def int_env(key: str, default: int = 0) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default
