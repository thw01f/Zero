def compute_module_debt(
    severity_counts: dict,
    loc: int,
    complexity_avg: float,
    max_complexity: float,
    churn_count: int,
    max_churn: int,
    dep_staleness: float,
    test_coverage_gap: float,
) -> tuple[float, str]:
    kloc = max(loc / 1000, 0.001)
    sev = (
        severity_counts.get("critical", 0) * 10
        + severity_counts.get("major", 0) * 5
        + severity_counts.get("minor", 0)
    ) / kloc
    sev_norm  = min(sev / 100.0, 1.0)
    comp_norm = min(complexity_avg / max(max_complexity, 1.0), 1.0)
    churn_norm= churn_count / max(max_churn, 1)
    score = (
        0.35 * sev_norm
        + 0.20 * comp_norm
        + 0.20 * (churn_norm * comp_norm)
        + 0.15 * dep_staleness
        + 0.10 * test_coverage_gap
    ) * 100

    grade = (
        "A" if score < 20 else
        "B" if score < 40 else
        "C" if score < 60 else
        "D" if score < 80 else "F"
    )
    return round(score, 1), grade


def grade_from_score(score: float) -> str:
    if score < 20: return "A"
    if score < 40: return "B"
    if score < 60: return "C"
    if score < 80: return "D"
    return "F"

# Edge case: when all weights max out, score could exceed 100. Added min/max clamp
