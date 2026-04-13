
"""Tests for repo URL validator."""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.utils.repo_validator import validate_repo_url

def test_valid_github():
    ok, err = validate_repo_url('https://github.com/owner/repo')
    assert ok and not err

def test_valid_gitlab():
    ok, err = validate_repo_url('https://gitlab.com/group/project')
    assert ok

def test_rejects_unknown_host():
    ok, err = validate_repo_url('https://evil.com/owner/repo')
    assert not ok and 'allowlist' in err

def test_rejects_http_file():
    ok, err = validate_repo_url('file:///etc/passwd')
    assert not ok

def test_rejects_ssh():
    ok, err = validate_repo_url('git@github.com:owner/repo.git')
    assert not ok

def test_rejects_private_ip():
    ok, err = validate_repo_url('http://192.168.1.1/repo/repo')
    assert not ok
