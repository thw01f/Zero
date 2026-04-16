# Compliance Mapping

DarkLead automatically maps every finding to OWASP 2021 Top 10 and NIST SP 800-53 Rev 5 controls.

---

## CWE → OWASP 2021 Mapping

| OWASP Category | Description | CWEs Covered |
|----------------|-------------|-------------|
| **A01:2021** | Broken Access Control | CWE-22, 23, 35, 59, 200, 284, 285, 352 |
| **A02:2021** | Cryptographic Failures | CWE-261, 296, 310, 319, 321, 326, 327, 328 |
| **A03:2021** | Injection | CWE-20, 74, 77, 78, 79, 89, 90, 116 |
| **A04:2021** | Insecure Design | CWE-73, 183, 209, 213 |
| **A05:2021** | Security Misconfiguration | CWE-2, 11, 13, 15 |
| **A06:2021** | Vulnerable and Outdated Components | CWE-1104 |
| **A07:2021** | Identification and Authentication Failures | CWE-255, 259, 287, 288 |
| **A08:2021** | Software and Data Integrity Failures | CWE-345, 353, 426, 494 |
| **A09:2021** | Security Logging and Monitoring Failures | CWE-223, 532 |
| **A10:2021** | Server-Side Request Forgery (SSRF) | CWE-918 |

---

## OWASP → NIST SP 800-53 Mapping

| OWASP | NIST Controls |
|-------|-------------|
| A01 Broken Access Control | AC-1, AC-2, AC-3, AC-6, AC-17 |
| A02 Cryptographic Failures | SC-8, SC-13, SC-28, IA-5 |
| A03 Injection | SI-10, SI-15, SA-11 |
| A04 Insecure Design | SA-8, SA-11, SA-15 |
| A05 Security Misconfiguration | CM-2, CM-6, CM-7, SI-2 |
| A06 Vulnerable Components | SI-2, SA-22, SR-3 |
| A07 Authentication Failures | IA-2, IA-5, IA-8, IA-11 |
| A08 Data Integrity Failures | SA-9, SA-12, SR-4, SR-6 |
| A09 Logging Failures | AU-2, AU-3, AU-6, AU-12 |
| A10 SSRF | SC-7, SC-8, SI-10 |

### NIST Control Families Referenced

| Family | Description |
|--------|-------------|
| AC | Access Control |
| AU | Audit and Accountability |
| CM | Configuration Management |
| IA | Identification and Authentication |
| SA | System and Services Acquisition |
| SC | System and Communications Protection |
| SI | System and Information Integrity |
| SR | Supply Chain Risk Management |

---

## Compliance Dashboard

The **Compliance Dashboard** view shows:

1. **OWASP Coverage Table** — which Top 10 categories have findings vs none
2. **NIST Control Status** — pass/fail per control family
3. **Finding Count** per OWASP category
4. **Remediation Priority** — which OWASP categories to fix first

### Coverage Calculation

```python
covered_categories = set(
    issue.owasp for issue in scan_issues
    if issue.owasp is not None
)
coverage_pct = len(covered_categories) / 10 * 100
```

"Covered" means findings were detected in that category.
A scan with **zero covered categories** = no known vulnerabilities in any OWASP Top 10 category.

---

## Automatic Mapping Pipeline

```
Scanner finding
    │
    ▼
bandit rule B602
    │
    ▼
LLM triage → CWE-78
    │
    ▼
cwe_to_owasp("CWE-78") → "A03:2021"
    │
    ▼
owasp_to_nist("A03:2021") → ["SI-10", "SI-15", "SA-11"]
    │
    ▼
Stored in issues table (cwe="CWE-78", owasp="A03:2021")
Stored in compliance_results table (category="A03:2021", status="fail")
```

---

## Export

The compliance data can be exported via `GET /api/export/{jobId}/json` which includes:

```json
{
  "compliance": {
    "owasp_2021": {
      "A01:2021": {"status": "pass", "finding_count": 0},
      "A03:2021": {"status": "fail", "finding_count": 5},
      ...
    },
    "nist_sp800_53": {
      "SI-10": {"status": "fail", "finding_count": 5},
      "AC-1":  {"status": "pass", "finding_count": 0},
      ...
    }
  }
}
```
