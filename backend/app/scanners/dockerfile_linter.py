
"""Dockerfile security linter (complements hadolint)."""
import re
from typing import TypedDict

class DockerFinding(TypedDict):
    line: int
    severity: str
    rule: str
    message: str

CHECKS = [
    (r'^FROM\s+\S+:latest\s*$', 'DL3007', 'minor', 'Use specific base image tag instead of :latest'),
    (r'^RUN\s+.*apt-get install(?!.*-y)', 'DL3015', 'minor', 'apt-get install without -y may fail in non-interactive mode'),
    (r'^USER\s+root\s*$', 'DL3002', 'major', 'Last USER should not be root'),
    (r'^ADD\s+https?://', 'DL3020', 'minor', 'Use COPY instead of ADD for local files; use curl/wget for URLs'),
    (r'^RUN\s+.*curl.*\|\s*sh', 'DL4006', 'critical', 'Pipe curl to sh: remote code execution risk'),
    (r'^ENV\s+(PASSWORD|SECRET|KEY|TOKEN)=', 'DL3025', 'critical', 'Secret in ENV instruction: visible in image history'),
    (r'^RUN\s+.*chmod\s+777', 'DL3047', 'major', 'chmod 777 grants excessive permissions'),
]

def lint_dockerfile(content: str) -> list[DockerFinding]:
    findings = []
    for i, line in enumerate(content.splitlines(), 1):
        for pattern, rule, sev, msg in CHECKS:
            if re.search(pattern, line.strip(), re.IGNORECASE):
                findings.append(DockerFinding(line=i, severity=sev, rule=rule, message=msg))
    return findings
