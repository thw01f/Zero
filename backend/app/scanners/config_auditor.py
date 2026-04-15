
"""Audit configuration files for security misconfigurations."""
import os
import re
import yaml
from typing import TypedDict

class ConfigFinding(TypedDict):
    file: str
    line: int
    severity: str
    message: str
    category: str

DANGEROUS_PATTERNS = [
    (r'debug\s*[=:]\s*[Tt]rue', 'Debug mode enabled in production config', 'critical'),
    (r'secret_key\s*[=:]\s*['"](django-insecure|changeme|default)', 'Insecure Django secret key', 'critical'),
    (r'ALLOWED_HOSTS\s*=\s*\[\s*['"](\*)['"]', 'ALLOWED_HOSTS=* allows all origins', 'major'),
    (r'ssl\s*[=:]\s*false|tls\s*[=:]\s*false|verify\s*[=:]\s*false', 'TLS/SSL disabled', 'major'),
    (r'password\s*[=:]\s*['"](password|admin|123456|root)['"]', 'Weak default password', 'critical'),
]

def audit_yaml(path: str) -> list[ConfigFinding]:
    findings = []
    try:
        with open(path, errors='ignore') as f:
            content = f.read()
        for i, line in enumerate(content.splitlines(), 1):
            for pattern, msg, sev in DANGEROUS_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    findings.append(ConfigFinding(file=path, line=i, severity=sev, message=msg, category='misconfiguration'))
    except Exception:
        pass
    return findings

def audit_env_file(path: str) -> list[ConfigFinding]:
    findings = []
    try:
        with open(path, errors='ignore') as f:
            for i, line in enumerate(f, 1):
                for pattern, msg, sev in DANGEROUS_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        findings.append(ConfigFinding(file=path, line=i, severity=sev, message=msg, category='misconfiguration'))
    except Exception:
        pass
    return findings
