
"""Code quality metrics aggregation."""
from typing import TypedDict, Optional

class QualityMetrics(TypedDict):
    loc: int
    cyclomatic_complexity_avg: float
    cyclomatic_complexity_max: int
    maintainability_index: Optional[float]
    comment_ratio: float
    test_coverage_est: float
    duplication_ratio: float

def compute_metrics(findings: list, loc: int, comment_lines: int=0) -> QualityMetrics:
    cc_values = [f.get('complexity', 1) for f in findings if 'complexity' in f]
    cc_avg = sum(cc_values) / len(cc_values) if cc_values else 1.0
    cc_max = max(cc_values, default=1)
    # Maintainability index approximation (0-100)
    import math
    mi = max(0, 100 - (cc_avg * 2) - (loc / 100))
    comment_ratio = comment_lines / max(loc, 1)
    # Estimate test coverage from test file presence in findings metadata
    test_est = 0.0  # placeholder
    return QualityMetrics(
        loc=loc, cyclomatic_complexity_avg=round(cc_avg, 2),
        cyclomatic_complexity_max=cc_max,
        maintainability_index=round(mi, 1),
        comment_ratio=round(comment_ratio, 3),
        test_coverage_est=test_est,
        duplication_ratio=0.0
    )
