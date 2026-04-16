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