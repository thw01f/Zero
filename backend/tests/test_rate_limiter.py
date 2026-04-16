
"""Tests for the in-memory rate limiter."""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.utils.rate_limiter import check_rate, reset

def test_allows_within_limit():
    key = 'test-allow'
    reset(key)
    for _ in range(5):
        assert check_rate(key, limit=5, window=60)

def test_blocks_over_limit():
    key = 'test-block'
    reset(key)
    for _ in range(5):
        check_rate(key, limit=5, window=60)
    assert not check_rate(key, limit=5, window=60)

def test_reset_clears_bucket():
    key = 'test-reset'
    reset(key)
    for _ in range(5):
        check_rate(key, limit=5, window=60)
    reset(key)
    assert check_rate(key, limit=5, window=60)
