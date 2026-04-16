
"""Tests for the regex secret scanner."""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.utils.secret_scanner import scan, SecretHit

def test_detects_hardcoded_password():
    code = 'password = "supersecret123"'
    hits = scan(code)
    assert any(h.pattern == 'Hardcoded password' for h in hits)

def test_detects_api_key():
    code = 'API_KEY = "abcdefghijklmnopqrstu12345"'
    hits = scan(code)
    assert any('key' in h.pattern.lower() for h in hits)

def test_detects_aws_key():
    code = 'aws_access_key = "AKIAIOSFODNN7EXAMPLE"'
    hits = scan(code)
    assert any('AWS' in h.pattern for h in hits)

def test_detects_github_pat():
    code = 'token = "ghp_1234567890abcdefghijklmnopqrstuv1"'
    hits = scan(code)
    assert any('GitHub' in h.pattern for h in hits)

def test_clean_code_no_hits():
    code = 'x = int(input())\nprint(x * 2)'
    hits = scan(code)
    assert hits == []

def test_returns_correct_line_numbers():
    code = 'a = 1\nb = 2\npassword = "hunter2"\nd = 4'
    hits = scan(code)
    pw_hits = [h for h in hits if h.pattern == 'Hardcoded password']
    assert pw_hits and pw_hits[0].line == 3
