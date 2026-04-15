"""Detect programming language from code snippet."""
import re
from typing import Optional

SIGNATURES: list[tuple[str, str]] = [
    (r'^\s*(import|from)\s+\w', 'python'),
    (r'^\s*def\s+\w+\s*\(', 'python'),
    (r'^\s*(const|let|var)\s+\w+\s*=', 'javascript'),
    (r'^\s*function\s+\w+\s*\(', 'javascript'),
    (r'=>\s*\{', 'javascript'),
    (r':\s*(string|number|boolean|void)\b', 'typescript'),
    (r'interface\s+\w+\s*\{', 'typescript'),
    (r'^\s*public\s+(static\s+)?void\s+main', 'java'),
    (r'System\.out\.println', 'java'),
    (r'^\s*func\s+\w+\(.*\)\s*(->|\{)', 'go'),
    (r'^\s*fn\s+\w+\(', 'rust'),
    (r'^\s*#!/usr/bin/(bash|sh)', 'bash'),
    (r'^\s*(FROM|RUN|COPY|CMD|EXPOSE)\s', 'dockerfile'),
    (r'^\s*resource\s+"aws_', 'terraform'),
]

def detect_language(code: str) -> Optional[str]:
    for pattern, lang in SIGNATURES:
        if re.search(pattern, code, re.MULTILINE):
            return lang
    return None
