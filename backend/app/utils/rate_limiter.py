
"""Simple in-memory rate limiter — no Redis needed."""
import time
from collections import defaultdict
from threading import Lock

_lock = Lock()
_buckets: dict[str, list[float]] = defaultdict(list)

def check_rate(key: str, limit: int=10, window: int=60) -> bool:
    """Return True if request is allowed."""
    now = time.time()
    with _lock:
        bucket = _buckets[key]
        bucket[:] = [t for t in bucket if now - t < window]
        if len(bucket) >= limit:
            return False
        bucket.append(now)
        return True

def reset(key: str) -> None:
    with _lock:
        _buckets.pop(key, None)
