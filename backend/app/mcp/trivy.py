import asyncio, json, os, tempfile
from typing import List
from .base import BaseTool, Finding

SEV = {"CRITICAL": "critical", "HIGH": "major", "MEDIUM": "minor", "LOW": "info"}


class TrivyTool(BaseTool):
    name = "trivy"
    languages = ["all"]
    category = "dependency"
    binary = "trivy"

    async def run(self, repo_path: str, language: str) -> List[Finding]:
        if not self._available():
            return []
        try:
            out = tempfile.mktemp(suffix=".json")
            proc = await asyncio.create_subprocess_exec(
                "trivy", "fs", "--format", "json", "--output", out,
                "--quiet", "--exit-code", "0", repo_path,
                stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
            )
            await asyncio.wait_for(proc.communicate(), timeout=120)
            data = json.loads(open(out).read())
            os.unlink(out)
            findings = []
            for result in data.get("Results", []):
                for vuln in result.get("Vulnerabilities", []) or []:
                    findings.append(Finding(
                        file_path=result.get("Target", ""),
                        line_start=0,
                        severity=SEV.get(vuln.get("Severity", "LOW"), "info"),
                        category="dependency",
                        rule_id=vuln.get("VulnerabilityID", "CVE"),
                        message=f"{vuln.get('PkgName','')} {vuln.get('InstalledVersion','')}: {vuln.get('Title','')}",
                        tool="trivy",
                    ))
            return findings
        except Exception:
            return []
