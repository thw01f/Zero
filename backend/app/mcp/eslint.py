import asyncio, json, os, tempfile
from typing import List
from .base import BaseTool, Finding


class EslintTool(BaseTool):
    name = "eslint"
    languages = ["javascript", "typescript"]
    category = "quality"
    binary = "eslint"

    async def run(self, repo_path: str, language: str) -> List[Finding]:
        if language not in self.languages or not self._available():
            return []
        try:
            proc = await asyncio.create_subprocess_exec(
                "eslint", "--ext", ".js,.ts,.jsx,.tsx",
                "--format", "json", repo_path,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=60)
            data = json.loads(stdout) if stdout.strip() else []
            findings = []
            for f in data:
                for msg in f.get("messages", []):
                    findings.append(Finding(
                        file_path=f.get("filePath", ""),
                        line_start=msg.get("line", 0),
                        severity="minor" if msg.get("severity") == 1 else "major",
                        category="quality",
                        rule_id=msg.get("ruleId"),
                        message=msg.get("message", ""),
                        tool="eslint",
                    ))
            return findings
        except Exception:
            return []
