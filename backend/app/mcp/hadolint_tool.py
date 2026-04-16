import asyncio, json
from typing import List
from .base import BaseTool, Finding

SEV = {"error": "major", "warning": "minor", "info": "info", "style": "info"}


class HadolintTool(BaseTool):
    name = "hadolint"
    languages = ["all"]
    category = "misconfig"
    binary = "hadolint"

    async def run(self, repo_path: str, language: str) -> List[Finding]:
        if not self._available():
            return []
        import glob, os
        dockerfiles = glob.glob(f"{repo_path}/**/Dockerfile*", recursive=True)
        dockerfiles += glob.glob(f"{repo_path}/**/dockerfile*", recursive=True)
        findings = []
        for df in dockerfiles[:5]:
            try:
                proc = await asyncio.create_subprocess_exec(
                    "hadolint", "--format", "json", df,
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
                )
                stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=30)
                for r in json.loads(stdout):
                    findings.append(Finding(
                        file_path=df, line_start=r.get("line", 0),
                        severity=SEV.get(r.get("level", "info"), "info"),
                        category="misconfig",
                        rule_id=r.get("code"), message=r.get("message", ""),
                        tool="hadolint", resource_type="Dockerfile",
                    ))
            except Exception:
                pass
        return findings
