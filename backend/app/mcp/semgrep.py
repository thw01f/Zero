import asyncio, json
from typing import List
from .base import BaseTool, Finding

SEV = {"ERROR": "critical", "WARNING": "major", "INFO": "minor"}


class SemgrepTool(BaseTool):
    name = "semgrep"
    languages = ["python", "javascript", "typescript", "java", "go", "ruby"]
    category = "security"
    binary = "semgrep"

    async def run(self, repo_path: str, language: str) -> List[Finding]:
        if language not in self.languages or not self._available():
            return []
        try:
            proc = await asyncio.create_subprocess_exec(
                "semgrep", "--config", "auto", "--json", "--quiet", repo_path,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=120)
            data = json.loads(stdout)
            return [
                Finding(
                    file_path=r.get("path", ""),
                    line_start=r.get("start", {}).get("line", 0),
                    severity=SEV.get(r.get("extra", {}).get("severity", "INFO"), "info"),
                    category="security",
                    rule_id=r.get("check_id"),
                    message=r.get("extra", {}).get("message", ""),
                    tool="semgrep",
                )
                for r in data.get("results", [])
            ]
        except Exception:
            return []
