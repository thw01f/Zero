"""Tests for code smell pattern matcher."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.utils.pattern_matcher import find_smells

def test_detects_eval():
    hits = find_smells("result = eval(user_input)")
    assert any(h.smell == 'eval-usage' for h in hits)
    assert any(h.severity == 'critical' for h in hits)

def test_detects_bare_except():
    hits = find_smells("try:\n    pass\nexcept:\n    pass")
    assert any(h.smell == 'bare-except' for h in hits)

def test_detects_todo_comment():
    hits = find_smells("# TODO: fix this later")
    assert any(h.smell == 'todo-comment' for h in hits)

def test_clean_code_no_smells():
    code = "def add(a: int, b: int) -> int:\n    return a + b\n"
    assert find_smells(code) == []
