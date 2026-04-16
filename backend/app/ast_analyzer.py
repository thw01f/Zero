"""
AST-based code entity extractor.
Python: full AST — functions, methods, classes, imports, globals, decorators.
JS/TS: regex — functions, arrows, classes, methods.
"""
import ast
import json
import re
import uuid
from pathlib import Path
from typing import List, Dict

_SKIP = {"__pycache__", "venv", ".venv", "node_modules", "site-packages",
         "dist", "build", ".git", "migrations", ".tox", "target", "vendor"}


def _should_skip(path: str) -> bool:
    return any(p in _SKIP for p in Path(path).parts)


# ── Python extractor ──────────────────────────────────────────────────────────

class _PythonVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str, source_lines: list[str]):
        self.file_path   = file_path
        self.lines       = source_lines
        self.entities: List[dict] = []
        self._cls_stack: List[str] = []
        self._imports: list[str]   = []

    def _end(self, node) -> int:
        return getattr(node, "end_lineno", node.lineno)

    def _decorators(self, node) -> list[str]:
        result = []
        for d in getattr(node, "decorator_list", []):
            if isinstance(d, ast.Name):            result.append(d.id)
            elif isinstance(d, ast.Attribute):     result.append(d.attr)
            elif isinstance(d, ast.Call):
                if isinstance(d.func, ast.Name):        result.append(d.func.id)
                elif isinstance(d.func, ast.Attribute): result.append(d.func.attr)
        return result

    # ── imports ────────────────────────────────────────────────────────────────
    def visit_Import(self, node):
        for alias in node.names:
            self._imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            self._imports.append(node.module)
        self.generic_visit(node)

    # ── classes ────────────────────────────────────────────────────────────────
    def visit_ClassDef(self, node):
        self._cls_stack.append(node.name)
        bases = []
        for b in node.bases:
            if isinstance(b, ast.Name):            bases.append(b.id)
            elif isinstance(b, ast.Attribute):     bases.append(f"{b.value.id}.{b.attr}" if isinstance(b.value, ast.Name) else b.attr)
        self.entities.append({
            "id":             str(uuid.uuid4()),
            "entity_type":    "class",
            "name":           node.name,
            "qualified_name": ".".join(self._cls_stack),
            "file_path":      self.file_path,
            "line_start":     node.lineno,
            "line_end":       self._end(node),
            "parent_name":    self._cls_stack[-2] if len(self._cls_stack) > 1 else None,
            "calls":          json.dumps(bases[:10]),
            "loc":            self._end(node) - node.lineno + 1,
        })
        self.generic_visit(node)
        self._cls_stack.pop()

    # ── functions / methods ────────────────────────────────────────────────────
    def _visit_func(self, node):
        parent = self._cls_stack[-1] if self._cls_stack else None
        calls  = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):        calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute): calls.append(child.func.attr)
        calls = list(dict.fromkeys(calls))[:30]
        decs  = self._decorators(node)
        self.entities.append({
            "id":             str(uuid.uuid4()),
            "entity_type":    "method" if parent else "function",
            "name":           node.name,
            "qualified_name": f"{parent}.{node.name}" if parent else node.name,
            "file_path":      self.file_path,
            "line_start":     node.lineno,
            "line_end":       self._end(node),
            "parent_name":    parent,
            "calls":          json.dumps(calls + decs),
            "loc":            self._end(node) - node.lineno + 1,
        })
        self.generic_visit(node)

    visit_FunctionDef      = _visit_func
    visit_AsyncFunctionDef = _visit_func

    # ── module-level assignments (globals) ─────────────────────────────────────
    def visit_Assign(self, node):
        # Only top-level (not inside function/class)
        if self._cls_stack:
            self.generic_visit(node)
            return
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id.isupper():
                # Constants (ALL_CAPS) — worth tracking
                self.entities.append({
                    "id":             str(uuid.uuid4()),
                    "entity_type":    "constant",
                    "name":           target.id,
                    "qualified_name": target.id,
                    "file_path":      self.file_path,
                    "line_start":     node.lineno,
                    "line_end":       node.lineno,
                    "parent_name":    None,
                    "calls":          json.dumps([]),
                    "loc":            1,
                })
        self.generic_visit(node)


def _extract_python(abs_path: str, rel_path: str) -> List[dict]:
    try:
        source = Path(abs_path).read_text(encoding="utf-8", errors="ignore")
        lines  = source.splitlines()
        tree   = ast.parse(source, filename=abs_path)
        v      = _PythonVisitor(rel_path, lines)
        v.visit(tree)

        # Prepend a "module" entity capturing the file's import list
        imports = list(dict.fromkeys(v._imports))[:50]
        module_entity = {
            "id":             str(uuid.uuid4()),
            "entity_type":    "module",
            "name":           Path(rel_path).stem,
            "qualified_name": rel_path.replace("/", ".").replace(".py", ""),
            "file_path":      rel_path,
            "line_start":     1,
            "line_end":       len(lines),
            "parent_name":    None,
            "calls":          json.dumps(imports),   # re-purposed: imported modules
            "loc":            sum(1 for l in lines if l.strip() and not l.strip().startswith("#")),
        }
        return [module_entity] + v.entities
    except Exception:
        return []


# ── JS/TS extractor ───────────────────────────────────────────────────────────

_JS_CLASS_RE  = re.compile(r"(?:^|\s)class\s+(\w+)(?:\s+extends\s+(\w+))?", re.MULTILINE)
_JS_FUNC_RE   = re.compile(r"(?:^|\s)(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(", re.MULTILINE)
_JS_ARROW_RE  = re.compile(r"(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(.*?\)\s*=>", re.MULTILINE)
_JS_METHOD_RE = re.compile(r"^\s{2,}(?:async\s+)?(?:static\s+)?(?:get\s+|set\s+)?(\w+)\s*\([^)]*\)\s*\{", re.MULTILINE)
_JS_IMPORT_RE = re.compile(r"(?:import\s+.*?from\s+['\"]([^'\"]+)['\"]|require\s*\(\s*['\"]([^'\"]+)['\"]\s*\))", re.MULTILINE)


def _extract_js(abs_path: str, rel_path: str) -> List[dict]:
    try:
        source = Path(abs_path).read_text(encoding="utf-8", errors="ignore")
        lines  = source.splitlines()
        entities = []

        def lineno(m):
            return source[:m.start()].count("\n") + 1

        # Module-level import node
        imports = []
        for m in _JS_IMPORT_RE.finditer(source):
            mod = m.group(1) or m.group(2)
            if mod and not mod.startswith("."):
                imports.append(mod.split("/")[0])
        entities.append({
            "id":             str(uuid.uuid4()),
            "entity_type":    "module",
            "name":           Path(rel_path).stem,
            "qualified_name": rel_path.replace("/", ".").rsplit(".", 1)[0],
            "file_path":      rel_path,
            "line_start":     1,
            "line_end":       len(lines),
            "parent_name":    None,
            "calls":          json.dumps(list(dict.fromkeys(imports))[:30]),
            "loc":            sum(1 for l in lines if l.strip() and not l.strip().startswith("//")),
        })

        # Classes
        for m in _JS_CLASS_RE.finditer(source):
            ln = lineno(m)
            bases = [m.group(2)] if m.group(2) else []
            entities.append({
                "id":             str(uuid.uuid4()),
                "entity_type":    "class",
                "name":           m.group(1),
                "qualified_name": m.group(1),
                "file_path":      rel_path,
                "line_start":     ln,
                "line_end":       min(ln + 60, len(lines)),
                "parent_name":    None,
                "calls":          json.dumps(bases),
                "loc":            1,
            })

        # Named functions
        for m in _JS_FUNC_RE.finditer(source):
            ln = lineno(m)
            entities.append({
                "id":             str(uuid.uuid4()),
                "entity_type":    "function",
                "name":           m.group(1),
                "qualified_name": m.group(1),
                "file_path":      rel_path,
                "line_start":     ln,
                "line_end":       min(ln + 30, len(lines)),
                "parent_name":    None,
                "calls":          json.dumps([]),
                "loc":            1,
            })

        # Arrow functions
        for m in _JS_ARROW_RE.finditer(source):
            ln = lineno(m)
            entities.append({
                "id":             str(uuid.uuid4()),
                "entity_type":    "function",
                "name":           m.group(1),
                "qualified_name": m.group(1),
                "file_path":      rel_path,
                "line_start":     ln,
                "line_end":       min(ln + 20, len(lines)),
                "parent_name":    None,
                "calls":          json.dumps([]),
                "loc":            1,
            })

        return entities
    except Exception:
        return []


# ── Public API ────────────────────────────────────────────────────────────────

_EXTRACTORS: Dict[str, any] = {
    ".py":  _extract_python,
    ".js":  _extract_js, ".jsx": _extract_js,
    ".ts":  _extract_js, ".tsx": _extract_js,
}


def extract_entities(repo_path: str, max_files: int = 800) -> List[dict]:
    """Walk repo_path and extract code entities from all source files."""
    base        = Path(repo_path)
    all_entities: List[dict] = []
    count       = 0
    for ext, extractor in _EXTRACTORS.items():
        for fpath in sorted(base.rglob(f"*{ext}")):
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
