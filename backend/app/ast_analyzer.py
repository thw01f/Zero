"""AST-based code entity extractor for Python (and regex fallback for JS/TS)."""
import ast
import json
import re
import uuid
from pathlib import Path
from typing import List, Dict

_SKIP = {"__pycache__", "venv", ".venv", "node_modules", "site-packages",
         "dist", "build", ".git", "migrations"}


def _should_skip(path: str) -> bool:
    return any(p in _SKIP for p in Path(path).parts)


# ── Python extractor ──────────────────────────────────────────────────────────

class _PythonVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.entities: List[dict] = []
        self._cls_stack: List[str] = []

    def _end(self, node) -> int:
        return getattr(node, "end_lineno", node.lineno)

    def visit_ClassDef(self, node):
        self._cls_stack.append(node.name)
        self.entities.append({
            "id": str(uuid.uuid4()),
            "entity_type": "class",
            "name": node.name,
            "qualified_name": ".".join(self._cls_stack),
            "file_path": self.file_path,
            "line_start": node.lineno,
            "line_end": self._end(node),
            "parent_name": self._cls_stack[-2] if len(self._cls_stack) > 1 else None,
            "calls": json.dumps([]),
            "loc": self._end(node) - node.lineno + 1,
        })
        self.generic_visit(node)
        self._cls_stack.pop()

    def _visit_func(self, node):
        parent = self._cls_stack[-1] if self._cls_stack else None
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.append(child.func.attr)
        calls = list(dict.fromkeys(calls))[:30]  # dedupe, cap

        self.entities.append({
            "id": str(uuid.uuid4()),
            "entity_type": "method" if parent else "function",
            "name": node.name,
            "qualified_name": f"{parent}.{node.name}" if parent else node.name,
            "file_path": self.file_path,
            "line_start": node.lineno,
            "line_end": self._end(node),
            "parent_name": parent,
            "calls": json.dumps(calls),
            "loc": self._end(node) - node.lineno + 1,
        })
        self.generic_visit(node)

    visit_FunctionDef = _visit_func
    visit_AsyncFunctionDef = _visit_func


def _extract_python(abs_path: str, rel_path: str) -> List[dict]:
    try:
        source = Path(abs_path).read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(source, filename=abs_path)
        v = _PythonVisitor(rel_path)
        v.visit(tree)
        return v.entities
    except Exception:
        return []


# ── JS/TS extractor (regex) ───────────────────────────────────────────────────

_JS_FUNC_RE = re.compile(
    r"(?:^|\s)(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(",
    re.MULTILINE,
)
_JS_ARROW_RE = re.compile(
    r"(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(.*?\)\s*=>",
    re.MULTILINE,
)
_JS_CLASS_RE = re.compile(r"(?:^|\s)class\s+(\w+)", re.MULTILINE)
_JS_METHOD_RE = re.compile(r"^\s+(?:async\s+)?(\w+)\s*\(", re.MULTILINE)


def _extract_js(abs_path: str, rel_path: str) -> List[dict]:
    try:
        source = Path(abs_path).read_text(encoding="utf-8", errors="ignore")
        lines = source.splitlines()
        entities = []

        for m in _JS_CLASS_RE.finditer(source):
            lineno = source[:m.start()].count("\n") + 1
            entities.append({
                "id": str(uuid.uuid4()),
                "entity_type": "class",
                "name": m.group(1),
                "qualified_name": m.group(1),
                "file_path": rel_path,
                "line_start": lineno,
                "line_end": min(lineno + 30, len(lines)),
                "parent_name": None,
                "calls": json.dumps([]),
                "loc": 1,
            })

        for m in _JS_FUNC_RE.finditer(source):
            lineno = source[:m.start()].count("\n") + 1
            entities.append({
                "id": str(uuid.uuid4()),
                "entity_type": "function",
                "name": m.group(1),
                "qualified_name": m.group(1),
                "file_path": rel_path,
                "line_start": lineno,
                "line_end": min(lineno + 20, len(lines)),
                "parent_name": None,
                "calls": json.dumps([]),
                "loc": 1,
            })

        for m in _JS_ARROW_RE.finditer(source):
            lineno = source[:m.start()].count("\n") + 1
            entities.append({
                "id": str(uuid.uuid4()),
                "entity_type": "function",
                "name": m.group(1),
                "qualified_name": m.group(1),
                "file_path": rel_path,
                "line_start": lineno,
                "line_end": min(lineno + 20, len(lines)),
                "parent_name": None,
                "calls": json.dumps([]),
                "loc": 1,
            })
        return entities
    except Exception:
        return []


# ── Public API ────────────────────────────────────────────────────────────────

_EXTRACTORS: Dict[str, any] = {
    ".py": _extract_python,
    ".js": _extract_js, ".jsx": _extract_js,
    ".ts": _extract_js, ".tsx": _extract_js,
}


def extract_entities(repo_path: str, max_files: int = 300) -> List[dict]:
    """Walk repo_path and extract code entities from source files."""
    base = Path(repo_path)
    all_entities = []
    count = 0
    for ext, extractor in _EXTRACTORS.items():
        for fpath in base.rglob(f"*{ext}"):
            if _should_skip(str(fpath)):
                continue
            rel = str(fpath.relative_to(base))
            all_entities.extend(extractor(str(fpath), rel))
            count += 1
            if count >= max_files:
                break
        if count >= max_files:
            break
    return all_entities
