
"""Code diff endpoint — before/after fix view."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import difflib

router = APIRouter(prefix='/diff', tags=['diff'])

class DiffRequest(BaseModel):
    original: str
    fixed: str
    filename: str = 'file.py'
    context: int = 3

@router.post('/generate')
async def generate_diff(req: DiffRequest):
    orig_lines = req.original.splitlines(keepends=True)
    fixed_lines = req.fixed.splitlines(keepends=True)
    unified = ''.join(difflib.unified_diff(
        orig_lines, fixed_lines,
        fromfile=f'a/{req.filename}', tofile=f'b/{req.filename}',
        n=req.context
    ))
    html_lines = []
    for line in unified.splitlines():
        if line.startswith('+') and not line.startswith('+++'):
            html_lines.append(f'<span class="diff-add">{line}</span>')
        elif line.startswith('-') and not line.startswith('---'):
            html_lines.append(f'<span class="diff-del">{line}</span>')
        elif line.startswith('@@'):
            html_lines.append(f'<span class="diff-hunk">{line}</span>')
        else:
            html_lines.append(line)
    return {'unified': unified, 'html': '\n'.join(html_lines),
            'added': sum(1 for l in unified.splitlines() if l.startswith('+') and not l.startswith('+++')),
            'removed': sum(1 for l in unified.splitlines() if l.startswith('-') and not l.startswith('---'))}
