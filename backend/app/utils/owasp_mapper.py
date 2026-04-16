
"""Map CWE IDs to OWASP Top 10 2021 categories."""
# Based on OWASP Top 10 2021 CWE mapping
CWE_TO_OWASP: dict[int, str] = {
    # A01 Broken Access Control
    22: 'A01:2021', 23: 'A01:2021', 35: 'A01:2021', 59: 'A01:2021',
    200: 'A01:2021', 284: 'A01:2021', 285: 'A01:2021', 352: 'A01:2021',
    # A02 Cryptographic Failures  
    261: 'A02:2021', 296: 'A02:2021', 310: 'A02:2021', 319: 'A02:2021',
    321: 'A02:2021', 326: 'A02:2021', 327: 'A02:2021', 328: 'A02:2021',
    # A03 Injection
    20: 'A03:2021', 74: 'A03:2021', 77: 'A03:2021', 78: 'A03:2021',
    79: 'A03:2021', 89: 'A03:2021', 90: 'A03:2021', 116: 'A03:2021',
    # A04 Insecure Design
    73: 'A04:2021', 183: 'A04:2021', 209: 'A04:2021', 213: 'A04:2021',
    # A05 Security Misconfiguration
    2: 'A05:2021', 11: 'A05:2021', 13: 'A05:2021', 15: 'A05:2021',
    # A06 Vulnerable and Outdated Components
    1104: 'A06:2021',
    # A07 Identification and Authentication Failures
    255: 'A07:2021', 259: 'A07:2021', 287: 'A07:2021', 288: 'A07:2021',
    # A08 Software and Data Integrity Failures
    345: 'A08:2021', 353: 'A08:2021', 426: 'A08:2021', 494: 'A08:2021',
    # A09 Security Logging and Monitoring Failures
    223: 'A09:2021', 532: 'A09:2021',
    # A10 SSRF
    918: 'A10:2021',
}

def cwe_to_owasp(cwe_str: str | None) -> str | None:
    if not cwe_str:
        return None
    try:
        num = int(''.join(filter(str.isdigit, cwe_str)))
        return CWE_TO_OWASP.get(num)
    except (ValueError, TypeError):
        return None
