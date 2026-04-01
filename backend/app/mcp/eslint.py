import asyncio, json, shutil
from pathlib import Path
from typing import List
from .base import BaseTool, Finding

SEV_MAP = {2: "major", 1: "minor"}


class ESLintTool(BaseTool):
    name = "eslint"
    languages = ["javascript"]
    category = "security"
    binary = "eslint"

    def _available(self) -> bool:
        return shutil.which("eslint") is not None and shutil.which("node") is not None

    async def run(self, repo_path: str, language: str) -> List[Finding]:
        try:
            proc = await asyncio.create_subprocess_exec(
                "eslint", "--format=json", "--ext", ".js,.ts,.jsx,.tsx",
                "--no-eslintrc", "--env", "browser,node,es2021",
                "--rule", '{"no-eval":2,"no-implied-eval":2}',
                repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=60)
            data = json.loads(stdout)
        except Exception:
            return []

        findings = []
        for file_result in data:
            for msg in file_result.get("messages", []):
                findings.append(Finding(
                    file_path=file_result.get("filePath", ""),
                    line_start=msg.get("line", 0),
                    line_end=msg.get("endLine"),
                    severity=SEV_MAP.get(msg.get("severity", 1), "minor"),
                    category="security",
                    rule_id=msg.get("ruleId", "eslint"),
                    message=msg.get("message", ""),
                    tool="eslint",
                ))
        return findings
