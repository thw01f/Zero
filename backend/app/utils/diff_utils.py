"""Unified diff utilities for fix suggestions."""
import difflib
from typing import NamedTuple

class DiffStats(NamedTuple):
    added: int
    removed: int
    unchanged: int
    similarity: float

def compute_diff_stats(original: str, fixed: str) -> DiffStats:
    orig_lines = original.splitlines()
    fixed_lines = fixed.splitlines()
    matcher = difflib.SequenceMatcher(None, orig_lines, fixed_lines)
    added = removed = unchanged = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':    unchanged += i2 - i1
        elif tag == 'insert': added += j2 - j1
        elif tag == 'delete': removed += i2 - i1
        elif tag == 'replace':
            removed += i2 - i1
            added += j2 - j1
    return DiffStats(added=added, removed=removed, unchanged=unchanged,
                     similarity=round(matcher.ratio(), 3))

def minimal_patch(original: str, fixed: str, filename: str = 'fix.py') -> str:
    return ''.join(difflib.unified_diff(
        original.splitlines(keepends=True),
        fixed.splitlines(keepends=True),
        fromfile=f'a/{filename}', tofile=f'b/{filename}', n=2
    ))
