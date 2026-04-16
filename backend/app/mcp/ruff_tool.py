import asyncio, json
from typing import List
from .base import BaseTool, Finding


class RuffTool(BaseTool):
    name = "ruff"
    languages = ["python"]
    category = "smell"
    binary = "ruff"

    async def run(self, repo_path: str, language: str) -> List[Finding]:
        try:
            proc = await asyncio.create_subprocess_exec(
                "ruff", "check", repo_path, "--output-format=json", "--exit-zero",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=60)
            data = json.loads(stdout)
        except Exception:
            return []

        findings = []
        for r in data:
            findings.append(Finding(
                file_path=r.get("filename", ""),
                line_start=r.get("location", {}).get("row", 0),
                severity="minor",
                category="smell",
                rule_id=r.get("code", "ruff"),
                message=r.get("message", ""),
                tool="ruff",
            ))
        return findings
