import asyncio, json
from typing import List
from .base import BaseTool, Finding
import os


class OsvScannerTool(BaseTool):
    name = "osv-scanner"
    languages = ["all"]
    category = "dependency"
    binary = "osv-scanner"

    async def run(self, repo_path: str, language: str) -> List[Finding]:
        if not self._available():
            return []
        try:
            proc = await asyncio.create_subprocess_exec(
                "osv-scanner", "--format", "json", "--recursive", repo_path,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=120)
            if not stdout.strip():
                return []
            data = json.loads(stdout)
            findings = []
            for result in data.get("results", []):
                for pkg in result.get("packages", []):
                    for vuln in pkg.get("vulnerabilities", []):
                        findings.append(Finding(
                            file_path=result.get("source", {}).get("path", ""),
                            line_start=0, severity="major", category="dependency",
                            rule_id=vuln.get("id", "OSV"),
                            message=f"{pkg.get('package',{}).get('name','')}: {vuln.get('summary','')[:80]}",
                            tool="osv-scanner",
                        ))
            return findings
        except Exception:
            return []
