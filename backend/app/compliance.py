import uuid
import json
from typing import List
from .mcp.base import Finding

OWASP_CWE_MAP = {
    "A01:2021-Broken Access Control":    ["CWE-22","CWE-284","CWE-285","CWE-639","CWE-200"],
    "A02:2021-Cryptographic Failures":   ["CWE-259","CWE-327","CWE-331","CWE-326"],
    "A03:2021-Injection":                ["CWE-89","CWE-77","CWE-78","CWE-79","CWE-94"],
    "A04:2021-Insecure Design":          ["CWE-209","CWE-256","CWE-501","CWE-522"],
    "A05:2021-Security Misconfiguration":["CWE-16","CWE-611","CWE-732","CWE-1021"],
    "A06:2021-Vulnerable Components":    ["CWE-1026","CWE-1035","CWE-1104"],
    "A07:2021-Identification Failures":  ["CWE-255","CWE-287","CWE-384","CWE-306"],
    "A08:2021-Software Integrity":       ["CWE-345","CWE-353","CWE-829"],
    "A09:2021-Logging Failures":         ["CWE-117","CWE-223","CWE-532"],
    "A10:2021-SSRF":                     ["CWE-918"],
}

NIST_CONTROLS = {
    "ID.AM-1": "Asset Management",
    "PR.DS-1": "Data-at-rest protection",
    "PR.DS-5": "Protections against data leaks",
    "DE.CM-8": "Vulnerability scans",
    "RS.MI-3": "Newly identified vulnerabilities mitigated",
}

SEMGREP_RULES_OWASP = {
    "A03:2021-Injection": ["sql", "sqli", "injection", "eval", "exec"],
    "A02:2021-Cryptographic Failures": ["crypto", "md5", "sha1", "hardcoded"],
    "A07:2021-Identification Failures": ["jwt", "auth", "session", "cookie"],
    "A10:2021-SSRF": ["ssrf", "redirect", "url"],
}


def _cwe_to_owasp(cwe_id: str) -> str:
    for owasp, cwes in OWASP_CWE_MAP.items():
        if cwe_id in cwes:
            return owasp
    return "A05:2021-Security Misconfiguration"  # default


def _rule_to_owasp(rule_id: str, message: str) -> str:
    text = (rule_id + " " + message).lower()
    for owasp, keywords in SEMGREP_RULES_OWASP.items():
        if any(kw in text for kw in keywords):
            return owasp
    return "A05:2021-Security Misconfiguration"


def map_findings_to_compliance(findings: List[Finding]) -> List[dict]:
    # Map findings to OWASP
    owasp_issues: dict = {k: [] for k in OWASP_CWE_MAP}
    for f in findings:
        if f.owasp_category and f.owasp_category in owasp_issues:
            owasp_issues[f.owasp_category].append(f.rule_id)
        elif f.cwe_id:
            owasp = _cwe_to_owasp(f.cwe_id)
            owasp_issues[owasp].append(f.rule_id)
        elif f.category in ("security", "secret", "misconfig"):
            owasp = _rule_to_owasp(f.rule_id, f.message)
            owasp_issues[owasp].append(f.rule_id)

    results = []
    for control_id, control_name in OWASP_CWE_MAP.items():
        issues = owasp_issues.get(control_id, [])
        results.append({
            "id": str(uuid.uuid4()),
            "framework": "owasp",
            "control_id": control_id,
            "control_name": control_id,
            "status": "fail" if issues else "pass",
            "issue_count": len(issues),
            "evidence": list(set(issues))[:10],
        })

    # NIST
    security_findings = [f for f in findings if f.category in ("security", "secret", "misconfig")]
    dep_findings = [f for f in findings if f.category == "dep"]
    for control_id, control_name in NIST_CONTROLS.items():
        results.append({
            "id": str(uuid.uuid4()),
            "framework": "nist",
            "control_id": control_id,
            "control_name": control_name,
            "status": "fail" if (security_findings or dep_findings) else "pass",
            "issue_count": len(security_findings) + len(dep_findings),
            "evidence": [],
        })

    return results


def persist_compliance(job_id: str, results: list, db) -> None:
    from .models import ComplianceResult
    for r in results:
        ev = r["evidence"]
        db.add(ComplianceResult(
            id=r["id"],
            job_id=job_id,
            standard=r.get("framework") or r.get("standard", "owasp"),
            control_id=r["control_id"],
            control_name=r["control_name"],
            status=r["status"],
            issue_count=r["issue_count"],
            evidence=json.dumps(ev) if isinstance(ev, (list, dict)) else ev,
        ))
    db.commit()

# PERF: map_findings_to_compliance() called per issue. Added @lru_cache on OWASP lookup.
