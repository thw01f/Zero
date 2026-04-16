import asyncio, json
from typing import List
from .base import BaseTool, Finding
import os

SEV = {"critical": "critical", "high": "major", "moderate": "minor", "low": "info"}


class NpmAuditTool(BaseTool):
    name = "npm-audit"
    languages = ["javascript", "typescript"]
    category = "dependency"
    binary = "npm"

    async def run(self, repo_path: str, language: str) -> List[Finding]:
        if language not in self.languages or not self._available():
            return []
        pkg = os.path.join(repo_path, "package.json")
        if not os.path.exists(pkg):
            return []
        try:
            proc = await asyncio.create_subprocess_exec(
                "npm", "audit", "--json",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
                cwd=repo_path,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=120)
            data = json.loads(stdout)
            findings = []
            for vuln in data.get("vulnerabilities", {}).values():
                findings.append(Finding(
                    file_path="package.json", line_start=0,
                    severity=SEV.get(vuln.get("severity", "low"), "info"),
                    category="dependency",
                    rule_id=vuln.get("name", "npm-audit"),
                    message=f"{vuln.get('name','')} {vuln.get('severity','')}: {vuln.get('title','')}",
                    tool="npm-audit",
                ))
            return findings
        except Exception:
            return []
