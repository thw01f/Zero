"""Code dependency graph — builds a force-graph from scan results."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Issue, Module

router = APIRouter(prefix="/graph", tags=["graph"])

_SEV_ORDER = {"critical": 4, "major": 3, "minor": 2, "info": 1, "clean": 0}
_LANG_MAP   = {
    "py": "python", "js": "javascript", "ts": "typescript",
    "jsx": "javascript", "tsx": "typescript", "java": "java",
    "go": "go", "rs": "rust", "rb": "ruby", "php": "php",
    "cs": "csharp", "cpp": "cpp", "c": "c", "sh": "shell",
    "tf": "terraform", "yml": "yaml", "yaml": "yaml",
    "json": "json", "md": "markdown",
}


def _guess_lang(path: str) -> str:
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    return _LANG_MAP.get(ext, "unknown")


@router.get("/{job_id}")
def get_graph(job_id: str, db: Session = Depends(get_db)):
    issues  = db.query(Issue).filter(Issue.job_id == job_id).all()
    modules = db.query(Module).filter(Module.job_id == job_id).all()

    if not issues and not modules:
        raise HTTPException(404, "No data for this job")

    module_map: dict = {m.path: m for m in modules}

    # Aggregate per-file stats
    file_sev:   dict[str, str] = {}
    file_count: dict[str, int] = {}
    file_rules: dict[str, list] = {}

    for iss in issues:
        fp = iss.file_path
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
        new  = _SEV_ORDER.get(iss.severity, 1)
        if new > curr:
            file_sev[fp] = iss.severity

    all_paths = set(module_map.keys()) | set(file_sev.keys())
    nodes = []
    for path in all_paths:
        mod   = module_map.get(path)
        parts = path.replace("\\", "/").split("/")
        nodes.append({
            "id":          path,
            "label":       parts[-1],
            "dir":         "/".join(parts[:-1]),
            "severity":    file_sev.get(path, "clean"),
            "debt_score":  round(mod.debt_score, 2) if mod else 0.0,
            "grade":       mod.grade        if mod else "A",
            "loc":         mod.loc          if mod else 0,
            "issue_count": file_count.get(path, 0),
            "language":    (mod.language if mod and mod.language else _guess_lang(path)),
            "top_issues":  file_rules.get(path, []),
        })

    # Build edges: files sharing a directory
    dir_groups: dict[str, list[str]] = {}
    for node in nodes:
        d = node["dir"]
        if d:
            dir_groups.setdefault(d, []).append(node["id"])

    edges = []
    seen:  set[tuple] = set()
    for members in dir_groups.values():
        # Limit fan-out so dense directories don't become hairballs
        hub = members[0]
        for m in members[1:min(len(members), 12)]:
            key = (min(hub, m), max(hub, m))
            if key not in seen:
                seen.add(key)
                edges.append({"source": hub, "target": m, "type": "sibling"})

    # Parent dir → child dir summary edges (virtual directory nodes)
    dir_nodes: list[dict] = []
    dir_sev:   dict[str, str] = {}
    for d, members in dir_groups.items():
        worst = max((_SEV_ORDER.get(file_sev.get(m, "clean"), 0) for m in members), default=0)
        rev   = {v: k for k, v in _SEV_ORDER.items()}
        dir_sev[d] = rev.get(worst, "clean")
        dir_nodes.append({
            "id":          f"__dir__{d}",
            "label":       d.split("/")[-1] or "/",
            "dir":         "/".join(d.split("/")[:-1]),
            "severity":    dir_sev[d],
            "is_dir":      True,
            "file_count":  len(members),
            "issue_count": sum(file_count.get(m, 0) for m in members),
        })

    crit  = sum(1 for n in nodes if n["severity"] == "critical")
    major = sum(1 for n in nodes if n["severity"] == "major")

    return {
        "nodes": nodes,
        "dir_nodes": dir_nodes,
        "edges": edges,
        "stats": {
            "total_files":    len(nodes),
            "total_dirs":     len(dir_groups),
            "total_edges":    len(edges),
            "critical_files": crit,
            "major_files":    major,
            "clean_files":    sum(1 for n in nodes if n["severity"] == "clean"),
        },
    }
