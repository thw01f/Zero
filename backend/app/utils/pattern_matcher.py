"""Pattern matching for code smell detection."""
import re
from typing import NamedTuple

class SmellHit(NamedTuple):
    line: int
    smell: str
    severity: str
    message: str

CODE_SMELLS = [
    (r'print\s*\(', 'debug-print', 'minor', 'Debug print statement left in code'),
    (r'TODO|FIXME|HACK|XXX', 'todo-comment', 'minor', 'TODO/FIXME comment — unfinished work'),
    (r'except\s*:\s*$|except\s+Exception\s*:', 'bare-except', 'major', 'Bare except clause swallows all errors'),
    (r'time\.sleep\s*\(\s*[0-9]+\s*\)', 'magic-sleep', 'minor', 'Magic sleep — consider event-driven approach'),
    (r'global\s+\w+', 'global-var', 'minor', 'Global variable — prefer dependency injection'),
    (r'eval\s*\(', 'eval-usage', 'critical', 'eval() — arbitrary code execution risk'),
    (r'exec\s*\(', 'exec-usage', 'critical', 'exec() — arbitrary code execution risk'),
    (r'#\s*noqa|#\s*type:\s*ignore', 'suppression', 'info', 'Linting suppression comment — investigate why'),
]

def find_smells(code: str, language: str = 'python') -> list[SmellHit]:
    if language != 'python':
        return []
    hits = []
    for i, line in enumerate(code.splitlines(), 1):
        for pattern, smell, sev, msg in CODE_SMELLS:
            if re.search(pattern, line):
                hits.append(SmellHit(line=i, smell=smell, severity=sev, message=msg))
    return hits
