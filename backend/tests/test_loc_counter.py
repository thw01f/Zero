
"""Tests for LOC counter."""
import sys, os, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.utils.loc_counter import count_directory

def test_counts_python_file():
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, 'a.py'), 'w') as f:
            f.write('# comment\nprint("hello")\n\n')
        r = count_directory(d)
        assert r['total'] == 3
        assert r['comment'] == 1
        assert r['blank'] == 1
        assert r['code'] == 1
        assert r['by_language'].get('Python', 0) == 3

def test_skips_node_modules():
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, 'node_modules'))
        with open(os.path.join(d, 'node_modules', 'pkg.js'), 'w') as f:
            f.write('module.exports = {}\n')
        with open(os.path.join(d, 'app.js'), 'w') as f:
            f.write('const x = 1\n')
        r = count_directory(d)
        assert r['by_language'].get('JavaScript', 0) == 1
