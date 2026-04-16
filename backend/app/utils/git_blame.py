
"""Git blame integration for issue attribution."""
import subprocess
import re
from typing import Optional

class BlameLine(dict):
    pass

def blame_line(repo_path: str, filepath: str, line: int) -> Optional[dict]:
    """Get git blame info for a specific line."""
    try:
        r = subprocess.run(
            ['git', 'blame', '-L', f'{line},{line}', '--porcelain', filepath],
            cwd=repo_path, capture_output=True, text=True, timeout=10
        )
        if r.returncode != 0:
            return None
        lines = r.stdout.splitlines()
        info = {}
        for bl in lines:
            if bl.startswith('author '):
                info['author'] = bl[7:]
            elif bl.startswith('author-time '):
                info['timestamp'] = int(bl[12:])
            elif bl.startswith('summary '):
                info['summary'] = bl[8:]
        return info if info else None
    except Exception:
        return None

def hotspot_files(repo_path: str, top_n: int=10) -> list[dict]:
    """Find files with most commits (change hotspots)."""
    try:
        r = subprocess.run(
            ['git', 'log', '--pretty=format:', '--name-only'],
            cwd=repo_path, capture_output=True, text=True, timeout=15
        )
        counts: dict[str, int] = {}
        for line in r.stdout.splitlines():
            if line.strip():
                counts[line.strip()] = counts.get(line.strip(), 0) + 1
        return [{'file': k, 'changes': v} for k, v in
                sorted(counts.items(), key=lambda x: -x[1])[:top_n]]
    except Exception:
        return []
