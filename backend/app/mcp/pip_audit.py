import asyncio, json
from pathlib import Path
from typing import List
from .base import BaseTool, Finding


class PipAuditTool(BaseTool):
    name = "pip-audit"
    languages = ["python"]
    category = "dep"
    binary = "pip-audit"

    async def run(self, repo_path: str, language: str) -> List[Finding]:
        req_files = list(Path(repo_path).rglob("requirements*.txt"))
        if not req_files:
            return []

        findings = []
        for req_file in req_files[:3]:
            try:
                proc = await asyncio.create_subprocess_exec(
                    "pip-audit", "-r", str(req_file), "--format", "json", "--progress-spinner", "off",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=60)
                data = json.loads(stdout)
                for dep in data.get("dependencies", []):
                    for vuln in dep.get("vulns", []):
                        findings.append(Finding(
                            file_path=str(req_file.relative_to(repo_path)),
                            line_start=0,
                            severity="major",
                            category="dep",
                            rule_id=vuln.get("id", "pip-audit"),
                            message=f"{dep.get('name')} {dep.get('version')}: {vuln.get('description', '')[:200]}",
                            tool="pip-audit",
                        ))
            except Exception:
                continue
        return findings
