
"""Simple TTL cache for LLM responses and compliance lookups."""
import time
import hashlib
import json
from typing import Any, Optional

_store: dict[str, tuple[float, Any]] = {}

def _key(data: Any) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

def get(data: Any, ttl: int=300) -> Optional[Any]:
    k = _key(data)
    if k in _store:
        ts, val = _store[k]
        if time.time() - ts < ttl:
            return val
        del _store[k]
    return None

def put(data: Any, value: Any) -> None:
    _store[_key(data)] = (time.time(), value)

def invalidate_all() -> int:
    n = len(_store)
    _store.clear()
    return n

def stats() -> dict:
    now = time.time()
    return {"entries": len(_store), "oldest_age_s": max((now - ts for ts, _ in _store.values()), default=0)}
