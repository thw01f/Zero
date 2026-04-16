import asyncio, json
from typing import List
from .base import BaseTool, Finding

SEV_MAP = {"CRITICAL": "critical", "HIGH": "major", "MEDIUM": "minor", "LOW": "info"}


class TrivyTool(BaseTool):
    name = "trivy"
    languages = ["all"]
    category = "dep"
    binary = "trivy"

    async def run(self, repo_path: str, language: str) -> List[Finding]:
        try:
            proc = await asyncio.create_subprocess_exec(
                "trivy", "fs", repo_path, "--format", "json",
                "--quiet", "--exit-code", "0",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=120)
            data = json.loads(stdout)
        except Exception:
            return []

        findings = []
        for result in data.get("Results", []):
            target = result.get("Target", "")
            for vuln in result.get("Vulnerabilities", []):
                findings.append(Finding(
                    file_path=target,
                    line_start=0,
                    severity=SEV_MAP.get(vuln.get("Severity", "LOW"), "info"),
                    category="dep",
                    rule_id=vuln.get("VulnerabilityID", "CVE-UNKNOWN"),
                    message=f"{vuln.get('PkgName')} {vuln.get('InstalledVersion')}: {vuln.get('Title', vuln.get('Description', '')[:100])}",
                    tool="trivy",
                ))
        return findings
