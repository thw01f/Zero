import asyncio, json
from typing import List
from .base import BaseTool, Finding


class OSVScannerTool(BaseTool):
    name = "osv-scanner"
    languages = ["all"]
    category = "dep"
    binary = "osv-scanner"

    async def run(self, repo_path: str, language: str) -> List[Finding]:
        try:
            proc = await asyncio.create_subprocess_exec(
                "osv-scanner", "--format", "json", repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=60)
            data = json.loads(stdout)
        except Exception:
            return []

        findings = []
        for result in data.get("results", []):
            source = result.get("source", {}).get("path", "")
            for pkg in result.get("packages", []):
                for vuln in pkg.get("vulnerabilities", []):
                    findings.append(Finding(
                        file_path=source,
                        line_start=0,
                        severity="major",
                        category="dep",
                        rule_id=vuln.get("id", "OSV-UNKNOWN"),
                        message=f"{pkg.get('package', {}).get('name', '')}: {vuln.get('summary', '')}",
                        tool="osv-scanner",
                    ))
        return findings
