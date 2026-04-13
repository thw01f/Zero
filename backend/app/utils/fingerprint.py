
"""Issue fingerprinting for deduplication across scans."""
import hashlib

def fingerprint(repo_url: str, filepath: str, line: int, rule: str) -> str:
    """Generate stable ID for an issue regardless of surrounding code changes."""
    key = f"{repo_url}:{filepath}:{rule}:{line}"
    return hashlib.sha1(key.encode()).hexdigest()[:16]

def fingerprint_snippet(code: str, rule: str) -> str:
    """Fingerprint based on code content (line-number independent)."""
    normalized = ' '.join(code.split())  # collapse whitespace
    key = f"{rule}:{normalized}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]
