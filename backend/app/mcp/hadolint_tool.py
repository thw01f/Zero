import asyncio, json
from pathlib import Path
from typing import List
from .base import BaseTool, Finding

SEV_MAP = {"error": "major", "warning": "minor", "info": "info", "style": "info"}


class HadolintTool(BaseTool):
    name = "hadolint"
    languages = ["all"]
    category = "misconfig"
    binary = "hadolint"

    async def run(self, repo_path: str, language: str) -> List[Finding]:
        dockerfiles = list(Path(repo_path).rglob("Dockerfile*"))
        if not dockerfiles:
            return []

        findings = []
        for df in dockerfiles:
            try:
                proc = await asyncio.create_subprocess_exec(
                    "hadolint", "--format", "json", str(df),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=30)
                data = json.loads(stdout)
                for item in data:
                    findings.append(Finding(
                        file_path=str(df.relative_to(repo_path)),
                        line_start=item.get("line", 0),
                        severity=SEV_MAP.get(item.get("level", "warning"), "minor"),
                        category="misconfig",
                        rule_id=item.get("code", "hadolint"),
                        message=item.get("message", ""),
                        tool="hadolint",
                        resource_type="Dockerfile",
                    ))
            except Exception:
                continue
        return findings
