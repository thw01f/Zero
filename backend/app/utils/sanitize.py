
"""Input sanitization helpers."""
import re
import html

def sanitize_filename(name: str, max_len: int=64) -> str:
    """Safe filename — removes path separators and limit length."""
    name = re.sub(r'[^A-Za-z0-9_\-\.]', '_', name)
    return name[:max_len]

def sanitize_code_snippet(code: str, max_bytes: int=100_000) -> str:
    """Trim code to max size and ensure it's valid UTF-8."""
    if isinstance(code, bytes):
        code = code.decode('utf-8', errors='replace')
    return code[:max_bytes]

def sanitize_repo_name(name: str) -> str:
    """Keep only alphanumeric, dash, underscore, dot — no path traversal."""
    return re.sub(r'[^A-Za-z0-9_\-\.]', '', name)[:128]

def escape_for_html(text: str) -> str:
    return html.escape(text)
