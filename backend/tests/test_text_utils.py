"""Tests for text utilities."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.utils.text_utils import extract_json_block, truncate_smart, normalize_severity

def test_extract_json_from_markdown_fence():
    text = 'Some text\n```json\n{"key": "value"}\n```'
    result = extract_json_block(text)
    assert result == {"key": "value"}

def test_extract_bare_json():
    text = 'Analysis result: {"score": 42, "grade": "B"} done'
    result = extract_json_block(text)
    assert result['score'] == 42

def test_extract_returns_none_on_failure():
    assert extract_json_block("no json here") is None

def test_truncate_at_sentence():
    text = "This is sentence one. This is sentence two that is very long and should be cut."
    result = truncate_smart(text, max_chars=40)
    assert result.endswith('.')

def test_normalize_severity():
    assert normalize_severity('HIGH') == 'critical'
    assert normalize_severity('WARN') == 'major'
    assert normalize_severity('note') == 'info'
