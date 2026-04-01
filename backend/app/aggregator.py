import uuid
from collections import defaultdict
from pathlib import Path
from typing import List, Dict
from .mcp.base import Finding
from .debt_score import compute_module_debt


def aggregate_modules(
    findings: List[Finding],
    loc_map: Dict[str, int],
    churn_map: Dict[str, int],
    repo_path: str,
) -> List[dict]:
    # Group findings by file
    file_findings: Dict[str, List[Finding]] = defaultdict(list)
    for f in findings:
        if f.file_path:
            # normalize path
            rel = f.file_path.replace(repo_path, "").lstrip("/\\")
            file_findings[rel].append(f)

    # Get complexity per file via lizard if available
    complexity_map: Dict[str, float] = {}
    try:
        import lizard
        results = lizard.analyze([repo_path])
        for file_info in results:
            rel = file_info.filename.replace(repo_path, "").lstrip("/\\")
            if file_info.function_list:
                avg = sum(f.cyclomatic_complexity for f in file_info.function_list) / len(file_info.function_list)
                complexity_map[rel] = avg
    except Exception:
        pass

    max_complexity = max(complexity_map.values(), default=1.0)
    max_churn = max(churn_map.values(), default=1)

    # All unique files
    all_files = set(loc_map.keys()) | set(file_findings.keys())

    # Count test files
    src_files = [f for f in all_files if "test" not in f.lower()]
    test_files = [f for f in all_files if "test" in f.lower()]
    total_src = max(len(src_files), 1)
    test_gap = 1.0 - min(len(test_files) / total_src, 1.0)

    # Dep staleness: files with dep findings
    dep_files = {f.file_path for f in findings if f.category == "dep"}

    modules = []
    for file_path in all_files:
        if "test" in file_path.lower():
            continue
        file_fs = file_findings.get(file_path, [])
        sev = defaultdict(int)
        for f in file_fs:
            sev[f.severity] += 1

        loc = loc_map.get(file_path, 0)
        complexity = complexity_map.get(file_path, 0.0)
        churn = churn_map.get(file_path, 0)
        dep_stale = 1.0 if file_path in dep_files else 0.0

        score, grade = compute_module_debt(
            dict(sev), loc, complexity, max_complexity,
            churn, max_churn, dep_stale, test_gap,
        )

        modules.append({
            "id": str(uuid.uuid4()),
            "path": file_path,
            "loc": loc,
            "complexity_avg": round(complexity, 2),
            "complexity_max": round(complexity_map.get(file_path, 0), 2),
            "churn_score": round(churn / max(max_churn, 1), 3),
            "debt_score": score,
            "grade": grade,
            "issue_count_critical": sev["critical"],
            "issue_count_major": sev["major"],
            "issue_count_minor": sev["minor"],
        })

    return sorted(modules, key=lambda m: m["debt_score"], reverse=True)


def weighted_avg_debt(modules: List[dict]) -> float:
    total_loc = sum(m["loc"] for m in modules) or 1
    return round(sum(m["debt_score"] * m["loc"] / total_loc for m in modules), 1)
