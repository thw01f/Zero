
"""Map OWASP categories to NIST SP 800-53 controls."""
OWASP_TO_NIST: dict[str, list[str]] = {
    'A01:2021': ['AC-1','AC-2','AC-3','AC-6','AC-17'],     # Broken Access Control
    'A02:2021': ['SC-8','SC-13','SC-28','IA-5'],            # Crypto Failures  
    'A03:2021': ['SI-10','SI-15','SA-11'],                  # Injection
    'A04:2021': ['SA-8','SA-11','SA-15'],                   # Insecure Design
    'A05:2021': ['CM-2','CM-6','CM-7','SI-2'],              # Security Misconfig
    'A06:2021': ['SI-2','SA-22','SR-3'],                    # Vulnerable Components
    'A07:2021': ['IA-2','IA-5','IA-8','IA-11'],             # Auth Failures
    'A08:2021': ['SA-9','SA-12','SR-4','SR-6'],             # Data Integrity
    'A09:2021': ['AU-2','AU-3','AU-6','AU-12'],             # Logging Failures
    'A10:2021': ['SC-7','SC-8','SI-10'],                    # SSRF
}

def owasp_to_nist(owasp: str | None) -> list[str]:
    if not owasp:
        return []
    return OWASP_TO_NIST.get(owasp, [])
