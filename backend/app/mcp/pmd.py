import asyncio
from typing import List
from pathlib import Path
from .base import BaseTool, Finding


class PmdTool(BaseTool):
    name = "pmd"
    languages = ["java"]
    category = "quality"
    binary = "pmd"

    async def run(self, repo_path: str, language: str) -> List[Finding]:
        if language not in self.languages or not self._available():
            return []
        try:
            proc = await asyncio.create_subprocess_exec(
                "pmd", "check", "-d", repo_path, "-R", "category/java/bestpractices.xml",
                "-f", "json", "--no-fail-on-violation",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
            )
            import json
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=120)
            data = json.loads(stdout)
            findings = []
            for file_result in data.get("files", []):
                for v in file_result.get("violations", []):
                    findings.append(Finding(
                        file_path=file_result.get("filename", ""),
                        line_start=v.get("beginline", 0),
                        severity="minor", category="quality",
                        rule_id=v.get("rule"), message=v.get("description", ""),
                        tool="pmd",
                    ))
            return findings
        except Exception:
            return []
