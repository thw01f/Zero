import re
from pathlib import Path
from typing import List
from .base import BaseTool, Finding

WEAK_PATTERNS = [
    (r'DEBUG\s*=\s*(True|1|true)', "DEBUG mode enabled — disable in production"),
    (r'SECRET_KEY\s*=\s*["\']?(your-secret|changeme|default|django-insecure)', "Weak or default SECRET_KEY"),
    (r'PASSWORD\s*=\s*["\']?\s*["\']', "Empty password in config"),
    (r'(DB_PASS|DATABASE_PASSWORD|MYSQL_PASSWORD)\s*=\s*["\']?(password|123|admin|root)', "Weak database password"),
    (r'ALLOWED_HOSTS\s*=\s*\[?\s*["\']?\*', "Wildcard ALLOWED_HOSTS is insecure"),
    (r'(AWS_SECRET|AWS_ACCESS|API_KEY|PRIVATE_KEY)\s*=\s*["\'][A-Za-z0-9+/]{20,}', "Possible hardcoded API key"),
]

ENV_PATTERNS = ["*.env", ".env", ".env.*", "*.env.*"]


class EnvCheckerTool(BaseTool):
    name = "env-checker"
    languages = ["all"]
    category = "misconfig"
    binary = ""

    def _available(self) -> bool:
        return True

    async def run(self, repo_path: str, language: str) -> List[Finding]:
        findings = []
        repo = Path(repo_path)

        # Find env files
        env_files = []
        for pattern in ["**/.env", "**/.env.*", "**/config.ini", "**/settings.py"]:
            env_files.extend(repo.glob(pattern))

        # Check if .env is in .gitignore
        gitignore = repo / ".gitignore"
        gitignore_content = ""
        if gitignore.exists():
            gitignore_content = gitignore.read_text(errors="replace")

        for env_file in env_files:
            try:
                rel_path = str(env_file.relative_to(repo))
                content = env_file.read_text(errors="replace")

                # .env file not gitignored
                if ".env" in env_file.name and ".env" not in gitignore_content:
                    findings.append(Finding(
                        file_path=rel_path,
                        line_start=1,
                        severity="critical",
                        category="misconfig",
                        rule_id="ENV_NOT_GITIGNORED",
                        message=f"{env_file.name} is not in .gitignore — secrets may be committed",
                        tool="env-checker",
                        resource_type="EnvFile",
                    ))

                for i, line in enumerate(content.splitlines(), 1):
                    for pattern, message in WEAK_PATTERNS:
                        if re.search(pattern, line, re.IGNORECASE):
                            findings.append(Finding(
                                file_path=rel_path,
                                line_start=i,
                                severity="major",
                                category="misconfig",
                                rule_id="WEAK_CONFIG",
                                message=message,
                                tool="env-checker",
                                resource_type="EnvFile",
                            ))
                            break
            except Exception:
                continue
        return findings
