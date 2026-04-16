import pytest
from app.debt_score import compute_module_debt, grade_from_score


def test_zero_issues_gives_low_score():
    score, grade = compute_module_debt(
        severity_counts={"critical": 0, "major": 0, "minor": 0},
        loc=100, complexity_avg=3.0, max_complexity=5,
        churn_count=1, max_churn=10,
        dep_staleness=0.0, test_coverage_gap=0.0
    )
    assert score < 30
    assert grade in ("A", "B")


def test_many_criticals_gives_high_score():
    score, grade = compute_module_debt(
        severity_counts={"critical": 10, "major": 5, "minor": 3},
        loc=100, complexity_avg=15.0, max_complexity=30,
        churn_count=20, max_churn=20,
        dep_staleness=1.0, test_coverage_gap=1.0
    )
    assert score > 70
    assert grade in ("D", "F")


def test_grade_from_score():
    assert grade_from_score(10) == "A"
    assert grade_from_score(35) == "B"
    assert grade_from_score(55) == "C"
    assert grade_from_score(75) == "D"
    assert grade_from_score(90) == "F"
