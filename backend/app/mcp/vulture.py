import asyncio, re
from typing import List
from .base import BaseTool, Finding


class VultureTool(BaseTool):
    name = "vulture"
    languages = ["python"]
    category = "quality"
    binary = "vulture"

    async def run(self, repo_path: str, language: str) -> List[Finding]:
        if language not in self.languages or not self._available():
            return []
        try:
            proc = await asyncio.create_subprocess_exec(
                "vulture", repo_path, "--min-confidence", "80",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=60)
            findings = []
            for line in stdout.decode().splitlines():
                m = re.match(r"(.+):(\d+): (.+) \((.+)\)", line)
                if m:
                    findings.append(Finding(
                        file_path=m.group(1), line_start=int(m.group(2)),
                        severity="info", category="quality",
                        rule_id="dead-code", message=m.group(3), tool="vulture",
                    ))
            return findings
        except Exception:
            return []
