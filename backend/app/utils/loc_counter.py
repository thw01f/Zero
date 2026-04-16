
"""Lines-of-code counter with language breakdown."""
import os
from pathlib import Path
from typing import TypedDict

LANG_MAP = {
    '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript',
    '.vue': 'Vue', '.java': 'Java', '.go': 'Go', '.rs': 'Rust',
    '.rb': 'Ruby', '.php': 'PHP', '.cpp': 'C++', '.c': 'C',
    '.sh': 'Bash', '.tf': 'Terraform', '.yaml': 'YAML', '.yml': 'YAML',
    '.json': 'JSON', '.dockerfile': 'Dockerfile', '.md': 'Markdown',
}

class LocResult(TypedDict):
    total: int
    code: int
    blank: int
    comment: int
    by_language: dict[str, int]

def count_directory(path: str, max_files: int=2000) -> LocResult:
    result: LocResult = {'total': 0, 'code': 0, 'blank': 0, 'comment': 0, 'by_language': {}}
    seen = 0
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules','__pycache__','.git','dist','build')]
        for f in files:
            if seen >= max_files:
                break
            fp = Path(root) / f
            ext = fp.suffix.lower()
            if ext not in LANG_MAP:
                continue
            try:
                lines = fp.read_text(errors='ignore').splitlines()
                lang = LANG_MAP[ext]
                result['by_language'][lang] = result['by_language'].get(lang, 0) + len(lines)
                for line in lines:
                    s = line.strip()
                    result['total'] += 1
                    if not s:
                        result['blank'] += 1
                    elif s.startswith(('#', '//', '/*', '*', '<!--', '--')):
                        result['comment'] += 1
                    else:
                        result['code'] += 1
                seen += 1
            except Exception:
                continue
    return result
