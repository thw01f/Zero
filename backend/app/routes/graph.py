"""Code dependency graph — builds a force-graph from scan results."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Issue, Module, CodeEntity

router = APIRouter(prefix="/graph", tags=["graph"])

_SEV_ORDER = {"critical": 4, "major": 3, "minor": 2, "info": 1, "clean": 0}
_SEV_RANK  = {v: k for k, v in _SEV_ORDER.items()}
_LANG_MAP  = {
    "py": "python", "js": "javascript", "ts": "typescript",
    "jsx": "javascript", "tsx": "typescript", "java": "java",
    "go": "go", "rs": "rust", "rb": "ruby", "php": "php",
    "cs": "csharp", "cpp": "cpp", "c": "c", "sh": "shell",
    "tf": "terraform", "yml": "yaml", "yaml": "yaml",
    "json": "json", "md": "markdown",
}
_SKIP_DIRS = {
    "node_modules", "venv", ".venv", "__pycache__", ".git",
    "site-packages", "dist", "build", ".tox", "vendor",
    ".pytest_cache", ".mypy_cache", "coverage", ".next",
    "target", "out", ".gradle",
}


def _guess_lang(path: str) -> str:
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    return _LANG_MAP.get(ext, "unknown")


def _should_skip(path: str) -> bool:
    return any(p in _SKIP_DIRS for p in path.replace("\\", "/").split("/"))


@router.get("/{job_id}")
def get_graph(job_id: str, db: Session = Depends(get_db), limit: int = 600):
    issues  = db.query(Issue).filter(Issue.job_id == job_id).all()
    modules = db.query(Module).filter(Module.job_id == job_id).all()

    if not issues and not modules:
        raise HTTPException(404, "No data for this job")

    module_map: dict = {m.path: m for m in modules if not _should_skip(m.path)}

    # Aggregate per-file stats (skipping vendor dirs)
    file_sev:   dict[str, str]   = {}
    file_count: dict[str, int]   = {}
    file_rules: dict[str, list]  = {}

    for iss in issues:
        fp = iss.file_path
        if _should_skip(fp):
            continue
        file_count[fp] = file_count.get(fp, 0) + 1
        file_rules.setdefault(fp, [])
        if len(file_rules[fp]) < 5:
            file_rules[fp].append({
                "severity": iss.severity,
                "rule_id":  iss.rule_id,
                "message":  (iss.message or "")[:80],
                "line":     iss.line_start,
                "cwe":      iss.cwe_id,
                "owasp":    iss.owasp_category,
            })
        curr = _SEV_ORDER.get(file_sev.get(fp, "clean"), 0)
        if _SEV_ORDER.get(iss.severity, 1) > curr:
            file_sev[fp] = iss.severity

    all_paths = set(module_map.keys()) | set(file_sev.keys())

    # Build node list with importance score
    raw_nodes = []
    for path in all_paths:
        mod  = module_map.get(path)
        parts = path.replace("\\", "/").split("/")
        ic    = file_count.get(path, 0)
        ds    = mod.debt_score if mod else 0.0
        sev   = file_sev.get(path, "clean")
        raw_nodes.append({
            "id":          path,
            "label":       parts[-1],
            "dir":         "/".join(parts[:-1]),
            "severity":    sev,
            "debt_score":  round(ds, 2),
            "grade":       mod.grade    if mod else "A",
            "loc":         mod.loc      if mod else 0,
            "issue_count": ic,
            "language":    (mod.language if mod and mod.language else _guess_lang(path)),
            "top_issues":  file_rules.get(path, []),
            "_score":      ic * 3 + ds + _SEV_ORDER.get(sev, 0) * 2,
        })

    total_raw = len(raw_nodes)
    raw_nodes.sort(key=lambda n: -n["_score"])
    nodes = raw_nodes[:limit]
    for n in nodes:
        del n["_score"]

    node_ids = {n["id"] for n in nodes}

    # Group files by directory
    dir_groups: dict[str, list[str]] = {}
    for node in nodes:
        d = node["dir"]
        if d:
            dir_groups.setdefault(d, []).append(node["id"])

    edges = []
    seen: set[tuple] = set()

    def _add_edge(a: str, b: str, etype: str):
        key = (min(a, b), max(a, b))
        if key not in seen and a in node_ids and b in node_ids:
            seen.add(key)
            edges.append({"source": a, "target": b, "type": etype})

    # Hub-and-spoke within each directory (cap fan-out at 20)
    for members in dir_groups.values():
        hub = members[0]
        for m in members[1:21]:
            _add_edge(hub, m, "sibling")

    # Cross-directory edges: dirs sharing a common parent → connect their reps
    parent_map: dict[str, list[str]] = {}
    for d in dir_groups:
        parent = "/".join(d.split("/")[:-1])
        parent_map.setdefault(parent, []).append(d)

    for siblings in parent_map.values():
        for i in range(len(siblings) - 1):
            ra = dir_groups.get(siblings[i],   [None])[0]
            rb = dir_groups.get(siblings[i+1], [None])[0]
            if ra and rb:
                _add_edge(ra, rb, "cross-dir")

    # Language-cluster edges: link critical/major files of the same language
    lang_critical: dict[str, list[str]] = {}
    for n in nodes:
        if n["severity"] in ("critical", "major"):
            lang_critical.setdefault(n["language"], []).append(n["id"])
    for members in lang_critical.values():
        for i in range(min(len(members) - 1, 8)):
            _add_edge(members[i], members[i+1], "lang-cluster")

    # Directory summary nodes (for stats / alternate dir-view)
    dir_nodes = []
    for d, members in dir_groups.items():
        worst = max((_SEV_ORDER.get(file_sev.get(m, "clean"), 0) for m in members), default=0)
        dir_nodes.append({
            "id":          f"__dir__{d}",
            "label":       d.split("/")[-1] or d,
            "full_path":   d,
            "severity":    _SEV_RANK.get(worst, "clean"),
            "is_dir":      True,
            "file_count":  len(members),
            "issue_count": sum(file_count.get(m, 0) for m in members),
            "debt_avg":    round(
                sum((module_map[m].debt_score if m in module_map else 0) for m in members)
                / max(len(members), 1), 2
            ),
        })

    return {
        "nodes":     nodes,
        "dir_nodes": dir_nodes,
        "edges":     edges,
        "truncated": total_raw > limit,
        "total_raw": total_raw,
        "stats": {
            "total_files":    len(nodes),
            "total_dirs":     len(dir_groups),
            "total_edges":    len(edges),
            "critical_files": sum(1 for n in nodes if n["severity"] == "critical"),
            "major_files":    sum(1 for n in nodes if n["severity"] == "major"),
            "clean_files":    sum(1 for n in nodes if n["severity"] == "clean"),
        },
    }

import json as _json

@router.get("/{job_id}/entities")
def get_entity_graph(job_id: str, db: Session = Depends(get_db), limit: int = 1200):
    """Function/class/module-level graph from AST analysis."""
    entities = db.query(CodeEntity).filter(CodeEntity.job_id == job_id).all()
    issues   = db.query(Issue).filter(Issue.job_id == job_id).all()

    if not entities:
        raise HTTPException(404, "No entity data — re-scan to generate AST graph")

    # Issue lookup by file
    issue_by_file: dict[str, list] = {}
    for iss in issues:
        issue_by_file.setdefault(iss.file_path, []).append(iss)

    # Score entities: those with issues first, then by loc
    def _score(e) -> float:
        file_issues = issue_by_file.get(e.file_path, [])
        n_issues = sum(1 for i in file_issues if e.line_start <= (i.line_start or 0) <= e.line_end)
        return n_issues * 10 + (e.loc or 0)

    sorted_entities = sorted(entities, key=_score, reverse=True)[:limit]

    # Build nodes
    nodes     = []
    name_to_id: dict[str, list[str]] = {}
    mod_qname_to_id: dict[str, str]  = {}   # module qualified_name → node id

    for e in sorted_entities:
        file_issues    = issue_by_file.get(e.file_path, [])
        entity_issues  = [i for i in file_issues
                          if e.line_start <= (i.line_start or 0) <= e.line_end]
        worst_sev      = "clean"
        for i in entity_issues:
            if _SEV_ORDER.get(i.severity, 0) > _SEV_ORDER.get(worst_sev, 0):
                worst_sev = i.severity

        calls_raw = _json.loads(e.calls or "[]")
        name_to_id.setdefault(e.qualified_name, []).append(e.id)
        name_to_id.setdefault(e.name, []).append(e.id)
        if e.entity_type == "module":
            mod_qname_to_id[e.qualified_name] = e.id
            # Also index by short name for cross-file matching
            short = e.qualified_name.split(".")[-1]
            mod_qname_to_id.setdefault(short, e.id)

        nodes.append({
            "id":             e.id,
            "label":          e.name,
            "qualified_name": e.qualified_name,
            "entity_type":    e.entity_type,
            "file_path":      e.file_path,
            "line_start":     e.line_start,
            "line_end":       e.line_end,
            "parent_name":    e.parent_name,
            "calls":          calls_raw,
            "loc":            e.loc,
            "issue_count":    len(entity_issues),
            "severity":       worst_sev,
            "issues":         [
                {"severity": i.severity, "rule_id": i.rule_id,
                 "message": (i.message or "")[:80], "line": i.line_start}
                for i in entity_issues[:3]
            ],
        })

    node_ids = {n["id"] for n in nodes}
    edges: list[dict] = []
    seen:  set         = set()

    def _edge(a: str, b: str, t: str):
        key = (a, b)
        if key not in seen and a in node_ids and b in node_ids and a != b:
            seen.add(key)
            edges.append({"source": a, "target": b, "type": t})

    for n in nodes:
        etype = n["entity_type"]
        calls = n.get("calls", [])

        if etype == "module":
            # Import edges: module → other module it imports
            for imp in calls:
                # Try full dotted path, last segment, and partial matches
                for key in (imp, imp.split(".")[-1], ".".join(imp.split(".")[-2:])):
                    tid = mod_qname_to_id.get(key)
                    if tid:
                        _edge(n["id"], tid, "imports")
                        break

        elif etype == "method":
            # Containment: method → parent class
            for pid in name_to_id.get(n["parent_name"], []):
                _edge(pid, n["id"], "contains")
            # Call edges
            for called in calls:
                for tid in name_to_id.get(called, [])[:3]:
                    _edge(n["id"], tid, "calls")

        elif etype in ("function", "constant"):
            # Call edges
            for called in calls:
                for tid in name_to_id.get(called, [])[:3]:
                    _edge(n["id"], tid, "calls")

        elif etype == "class":
            # Inheritance: base class edges
            for base in calls:
                for tid in name_to_id.get(base, [])[:2]:
                    _edge(n["id"], tid, "inherits")
            # Module containment: link class to its module node
            mod_path = n["file_path"].replace("/", ".").replace(".py", "").replace(".js", "").replace(".ts", "")
            for key in (mod_path, mod_path.split(".")[-1]):
                mid = mod_qname_to_id.get(key)
                if mid:
                    _edge(mid, n["id"], "contains")
                    break

    # Strip calls list before returning
    for n in nodes:
        n.pop("calls", None)

    type_counts: dict[str, int] = {}
    for n in nodes:
        type_counts[n["entity_type"]] = type_counts.get(n["entity_type"], 0) + 1

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "total_entities": len(nodes),
            "total_edges":    len(edges),
            "modules":        type_counts.get("module", 0),
            "functions":      type_counts.get("function", 0),
            "methods":        type_counts.get("method", 0),
            "classes":        type_counts.get("class", 0),
            "constants":      type_counts.get("constant", 0),
            "critical":       sum(1 for n in nodes if n["severity"] == "critical"),
            "major":          sum(1 for n in nodes if n["severity"] == "major"),
        },
    }
