
"""Tests for SQL injection detector."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.scanners.sql_detector import detect_sql_injection

SAFE_CODE = '''
def get_user(user_id: int):
    return db.execute('SELECT * FROM users WHERE id = ?', (user_id,))
'''

UNSAFE_CODE = '''
def get_user(name):
    return db.execute("SELECT * FROM users WHERE name = '%s'" % name)
'''

FSTRING_CODE = '''
def query(table):
    cursor.execute(f"SELECT * FROM {table}")
'''

def test_clean_code_no_findings():
    assert detect_sql_injection(SAFE_CODE) == []

def test_detects_percent_formatting():
    findings = detect_sql_injection(UNSAFE_CODE)
    assert any(f['rule'] == 'sqli-format' for f in findings)

def test_detects_fstring():
    findings = detect_sql_injection(FSTRING_CODE)
    assert any('fstring' in f['rule'] for f in findings)

def test_all_findings_critical():
    findings = detect_sql_injection(UNSAFE_CODE + FSTRING_CODE)
    assert all(f['severity'] == 'critical' for f in findings)
