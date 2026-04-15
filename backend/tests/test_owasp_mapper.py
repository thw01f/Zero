
"""Tests for OWASP CWE mapper."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.utils.owasp_mapper import cwe_to_owasp

def test_cwe_78_maps_to_a03():
    assert cwe_to_owasp('CWE-78') == 'A03:2021'

def test_cwe_89_maps_to_a03():
    assert cwe_to_owasp('CWE-89') == 'A03:2021'

def test_cwe_79_xss():
    assert cwe_to_owasp('79') == 'A03:2021'

def test_cwe_287_auth():
    assert cwe_to_owasp('CWE-287') == 'A07:2021'

def test_cwe_918_ssrf():
    assert cwe_to_owasp('CWE-918') == 'A10:2021'

def test_unknown_cwe_returns_none():
    assert cwe_to_owasp('CWE-9999') is None

def test_none_input():
    assert cwe_to_owasp(None) is None
