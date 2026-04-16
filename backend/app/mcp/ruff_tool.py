import asyncio, json
from typing import List
from .base import BaseTool, Finding


class RuffTool(BaseTool):
    name = "ruff"
    languages = ["python"]
    category = "quality"
    binary = "ruff"

    async def run(self, repo_path: str, language: str) -> List[Finding]:
        if language not in self.languages or not self._available():
            return []
        try:
            proc = await asyncio.create_subprocess_exec(
                "ruff", "check", "--output-format", "json", repo_path,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=60)
            data = json.loads(stdout) if stdout.strip() else []
        except Exception:
            return []
        return [
            Finding(
                file_path=r.get("filename", ""),
                line_start=r.get("location", {}).get("row", 0),
                severity="minor",
                category="quality",
                rule_id=r.get("code"),
                message=r.get("message", ""),
                tool="ruff",
            )
            for r in data
        ]
