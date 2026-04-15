
"""Tests for the priority scoring system."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.utils.priority_scorer import priority_score, Finding

def test_critical_security_with_owasp_maxes():
    f = Finding(severity='critical', category='security', owasp='A01:2021', cwe='CWE-22', has_fix=True)
    score = priority_score(f)
    assert score > 90

def test_info_quality_is_low():
    f = Finding(severity='info', category='quality', owasp=None, cwe=None, has_fix=False)
    score = priority_score(f)
    assert score < 20

def test_fix_available_boosts_score():
    base = Finding(severity='major', category='security', owasp=None, cwe=None, has_fix=False)
    with_fix = Finding(severity='major', category='security', owasp=None, cwe=None, has_fix=True)
    assert priority_score(with_fix) > priority_score(base)

def test_score_capped_at_100():
    f = Finding(severity='critical', category='security', owasp='A03:2021', cwe='CWE-89', has_fix=True)
    assert priority_score(f) <= 100
