
"""Fast regex-based secret pattern scanner (pre-LLM gate)."""
import re
from typing import NamedTuple

class SecretHit(NamedTuple):
    line: int
    pattern: str
    excerpt: str

PATTERNS = [
    (r'(?i)(api[_-]?key|apikey)\s*[:=]\s*['"\s]?([A-Za-z0-9_\-]{20,})', 'API key'),
    (r'(?i)(secret[_-]?key|secretkey)\s*[:=]\s*['"\s]?([A-Za-z0-9_\-/+]{20,})', 'Secret key'),
    (r'(?i)(password|passwd|pwd)\s*[:=]\s*['"]((?!\{)[^\s'"]{6,})['"]', 'Hardcoded password'),
    (r'(sk-[A-Za-z0-9]{40,})', 'OpenAI/Anthropic key'),
    (r'(ghp_[A-Za-z0-9]{36})', 'GitHub PAT'),
    (r'(AKIA[0-9A-Z]{16})', 'AWS Access Key'),
    (r'(?i)(private[_-]?key)\s*[:=]\s*-----BEGIN', 'PEM private key'),
    (r'(bearer\s+[A-Za-z0-9\-._~+/]+=*)', 'Bearer token'),
]
_compiled = [(re.compile(p), name) for p, name in PATTERNS]

def scan(code: str) -> list[SecretHit]:
    hits = []
    for i, line in enumerate(code.splitlines(), 1):
        for rx, name in _compiled:
            m = rx.search(line)
            if m:
                excerpt = line.strip()[:80]
                hits.append(SecretHit(line=i, pattern=name, excerpt=excerpt))
    return hits
