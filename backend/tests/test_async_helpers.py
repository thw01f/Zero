"""Tests for async helpers."""
import sys, os, asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.utils.async_helpers import timeout_wrap, gather_with_errors

async def slow():
    await asyncio.sleep(10)
    return 'done'

async def failing():
    raise ValueError('boom')

async def ok():
    return 42

def test_timeout_returns_fallback():
    result = asyncio.run(timeout_wrap(slow(), seconds=0.1, fallback='timeout'))
    assert result == 'timeout'

def test_gather_with_errors_handles_failure():
    results = asyncio.run(gather_with_errors(ok(), failing(), ok()))
    assert results[0] == 42
    assert results[1] is None
    assert results[2] == 42
