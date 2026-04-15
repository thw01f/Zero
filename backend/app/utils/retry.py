"""Retry decorator for flaky operations."""
import asyncio
import functools
import time
from typing import Callable, TypeVar

T = TypeVar('T')

def retry_sync(max_attempts: int = 3, delay: float = 1.0, exceptions=(Exception,)):
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            last_err = None
            for attempt in range(max_attempts):
                try:
                    return fn(*args, **kwargs)
                except exceptions as e:
                    last_err = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay * (2 ** attempt))  # exponential backoff
            raise last_err
        return wrapper
    return decorator

def retry_async(max_attempts: int = 3, delay: float = 1.0, exceptions=(Exception,)):
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            last_err = None
            for attempt in range(max_attempts):
                try:
                    return await fn(*args, **kwargs)
                except exceptions as e:
                    last_err = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (2 ** attempt))
            raise last_err
        return wrapper
    return decorator
