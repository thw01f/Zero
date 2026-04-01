import asyncio
from typing import List
from .base import BaseTool, Finding


class VultureTool(BaseTool):
    name = "vulture"
    languages = ["python"]
    category = "debt"
    binary = "vulture"

    async def run(self, repo_path: str, language: str) -> List[Finding]:
        try:
            proc = await asyncio.create_subprocess_exec(
                "vulture", repo_path, "--min-confidence", "80",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=30)
            lines = stdout.decode(errors="replace").splitlines()
        except Exception:
            return []

        findings = []
        for line in lines:
            # format: path:line: message (confidence X%)
            try:
                parts = line.split(":", 2)
                if len(parts) < 3:
                    continue
                file_path = parts[0]
                line_no = int(parts[1])
                msg = parts[2].strip()
                findings.append(Finding(
                    file_path=file_path,
                    line_start=line_no,
                    severity="minor",
                    category="debt",
                    rule_id="dead-code",
                    message=msg,
                    tool="vulture",
                ))
            except Exception:
                continue
        return findings
