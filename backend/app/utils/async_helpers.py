
"""Async utility helpers."""
import asyncio
from typing import TypeVar, Callable, Awaitable

T = TypeVar('T')

async def timeout_wrap(coro: Awaitable[T], seconds: float, fallback: T) -> T:
    """Run coroutine with timeout, return fallback on timeout."""
    try:
        return await asyncio.wait_for(coro, timeout=seconds)
    except (asyncio.TimeoutError, Exception):
        return fallback

async def gather_with_errors(*coros) -> list:
    """Like asyncio.gather but catches individual errors as None."""
    async def safe(coro):
        try:
            return await coro
        except Exception:
            return None
    return list(await asyncio.gather(*[safe(c) for c in coros]))

async def run_in_thread(fn: Callable, *args) -> any:
    """Run blocking function in thread pool executor."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, fn, *args)
