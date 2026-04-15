"""Tests for diff utilities."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.utils.diff_utils import compute_diff_stats, minimal_patch

def test_identical_code_zero_diff():
    code = "def hello():\n    print('hi')\n"
    stats = compute_diff_stats(code, code)
    assert stats.added == 0 and stats.removed == 0
    assert stats.similarity == 1.0

def test_added_lines_counted():
    original = "a = 1\n"
    fixed = "a = 1\nb = 2\n"
    stats = compute_diff_stats(original, fixed)
    assert stats.added == 1 and stats.removed == 0

def test_minimal_patch_non_empty():
    original = "password = 'admin123'\n"
    fixed = "import os\npassword = os.environ['DB_PASSWORD']\n"
    patch = minimal_patch(original, fixed, 'config.py')
    assert '-' in patch and '+' in patch
