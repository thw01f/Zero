import asyncio, json
from pathlib import Path
from typing import List
from .base import BaseTool, Finding

SEV_MAP = {"critical": "critical", "high": "major", "moderate": "minor", "low": "info"}


class NpmAuditTool(BaseTool):
    name = "npm-audit"
    languages = ["javascript"]
    category = "dep"
    binary = "npm"

    async def run(self, repo_path: str, language: str) -> List[Finding]:
        pkg_files = [p for p in Path(repo_path).rglob("package.json")
                     if "node_modules" not in str(p)]
        if not pkg_files:
            return []

        findings = []
        for pkg_file in pkg_files[:3]:
            try:
                proc = await asyncio.create_subprocess_exec(
                    "npm", "audit", "--json",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.DEVNULL,
                    cwd=str(pkg_file.parent),
                )
                stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=60)
                data = json.loads(stdout)
                for name, vuln in data.get("vulnerabilities", {}).items():
                    findings.append(Finding(
                        file_path=str(pkg_file.relative_to(repo_path)),
                        line_start=0,
                        severity=SEV_MAP.get(vuln.get("severity", "low"), "info"),
                        category="dep",
                        rule_id=",".join(vuln.get("via", [name])[:1]) if isinstance(vuln.get("via", []), list) else name,
                        message=f"{name}: {vuln.get('title', 'vulnerability')}",
                        tool="npm-audit",
                    ))
            except Exception:
                continue
        return findings
