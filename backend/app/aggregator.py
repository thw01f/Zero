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