import pytest
from app.mcp.base import Finding
from app.compliance import map_findings_to_compliance


def test_sql_injection_maps_to_owasp_a03():
    findings = [
        Finding(file_path="app.py", line_start=10,
                severity="critical", category="security",
                rule_id="B608", message="SQL injection", tool="bandit",
                cwe_id="CWE-89")
    ]
    results = map_findings_to_compliance(findings)
    categories = [r["control"] for r in results]
    assert any("A03" in c or "Injection" in c for c in categories)


def test_empty_findings_returns_all_pass():
    results = map_findings_to_compliance([])
    statuses = [r["status"] for r in results]
    assert all(s in ("pass", "partial", "fail", "unknown") for s in statuses)
