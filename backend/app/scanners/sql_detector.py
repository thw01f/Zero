
"""SQL injection pattern detector."""
import re
from typing import TypedDict

class SqlFinding(TypedDict):
    line: int
    severity: str
    rule: str
    message: str
    snippet: str

# Patterns that suggest string-formatted SQL queries
SQL_INJECTION_PATTERNS = [
    (r'execute\s*\(\s*[f\'\"]+.*%s.*[f\'\"]+', 'sqli-format', 'SQL query uses %-formatting — potential injection'),
    (r'execute\s*\(\s*f[\'\"].*\{', 'sqli-fstring', 'SQL query uses f-string — potential injection'),
    (r'execute\s*\(.*\.format\(', 'sqli-format-method', 'SQL query uses .format() — potential injection'),
    (r'cursor\.execute\s*\(\s*[\'\"]\s*SELECT.*\+', 'sqli-concat', 'SQL query uses string concatenation — potential injection'),
    (r'raw\s*\(\s*[\'\"].*\{', 'sqli-django-raw', 'Django .raw() with f-string — potential injection'),
]

def detect_sql_injection(code: str) -> list[SqlFinding]:
    findings = []
    lines = code.splitlines()
    for i, line in enumerate(lines, 1):
        for pattern, rule, msg in SQL_INJECTION_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                findings.append(SqlFinding(
                    line=i, severity='critical', rule=rule,
                    message=msg, snippet=line.strip()[:100]
                ))
    return findings
