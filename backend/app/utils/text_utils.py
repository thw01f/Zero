
"""Text processing utilities for AI output parsing."""
import re
import json

def extract_json_block(text: str) -> dict | list | None:
    """Extract first JSON object or array from text (handles markdown fences)."""
    # Try markdown fence first
    fence = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if fence:
        try:
            return json.loads(fence.group(1).strip())
        except Exception:
            pass
    # Try bare JSON
    for start_char, end_char in [('{', '}'), ('[', ']')]:
        i = text.find(start_char)
        if i == -1:
            continue
        depth = 0
        for j in range(i, len(text)):
            if text[j] == start_char: depth += 1
            elif text[j] == end_char: depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[i:j+1])
                except Exception:
                    break
    return None

def truncate_smart(text: str, max_chars: int=500) -> str:
    """Truncate at sentence boundary if possible."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_period = truncated.rfind('.')
    if last_period > max_chars * 0.7:
        return truncated[:last_period + 1]
    return truncated + '...'

def normalize_severity(s: str) -> str:
    s = s.lower().strip()
    return {'high': 'critical', 'error': 'critical', 'warn': 'major',
            'warning': 'major', 'low': 'minor', 'note': 'info'}.get(s, s)
