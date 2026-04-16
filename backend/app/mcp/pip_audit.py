import asyncio, json
from typing import List
from .base import BaseTool, Finding


class PipAuditTool(BaseTool):
    name = "pip-audit"
    languages = ["python"]
    category = "dependency"
    binary = "pip-audit"

    async def run(self, repo_path: str, language: str) -> List[Finding]:
        if language not in self.languages or not self._available():
            return []
        req = f"{repo_path}/requirements.txt"
        import os
        if not os.path.exists(req):
            return []
        try:
            proc = await asyncio.create_subprocess_exec(
                "pip-audit", "-r", req, "--format", "json", "--progress-spinner", "off",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=120)
            data = json.loads(stdout)
            findings = []
            for dep in data.get("dependencies", []):
                for vuln in dep.get("vulns", []):
                    findings.append(Finding(
                        file_path="requirements.txt", line_start=0,
                        severity="major", category="dependency",
                        rule_id=vuln.get("id", "CVE"),
                        message=f"{dep.get('name','')} {dep.get('version','')}: {vuln.get('description','')[:100]}",
                        tool="pip-audit",
                    ))
            return findings
        except Exception:
            return []
