import asyncio, json
from typing import List
from .base import BaseTool, Finding

SEV = {"HIGH": "critical", "MEDIUM": "major", "LOW": "minor", "CRITICAL": "critical"}


class CheckovTool(BaseTool):
    name = "checkov"
    languages = ["all"]
    category = "misconfig"
    binary = "checkov"

    async def run(self, repo_path: str, language: str) -> List[Finding]:
        if not self._available():
            return []
        try:
            proc = await asyncio.create_subprocess_exec(
                "checkov", "-d", repo_path, "--output", "json",
                "--quiet", "--compact",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=120)
            text = stdout.decode()
            # checkov may return array or object
            data = json.loads(text) if text.strip() else {}
            if isinstance(data, list):
                data = {"results": {"failed_checks": [c for d in data for c in d.get("results", {}).get("failed_checks", [])]}}
            findings = []
            for check in data.get("results", {}).get("failed_checks", []):
                findings.append(Finding(
                    file_path=check.get("repo_file_path", check.get("file_path", "")),
                    line_start=check.get("file_line_range", [0])[0] if check.get("file_line_range") else 0,
                    severity=SEV.get(check.get("severity", "LOW"), "minor"),
                    category="misconfig",
                    rule_id=check.get("check_id"),
                    message=check.get("check_id", "") + ": " + check.get("check_type", ""),
                    tool="checkov",
                    resource_type=check.get("resource_type", "IaC"),
                    check_id=check.get("check_id"),
                ))
            return findings
        except Exception:
            return []
