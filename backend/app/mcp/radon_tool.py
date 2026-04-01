import asyncio, json
from pathlib import Path
from typing import List
from .base import BaseTool, Finding


class RadonTool(BaseTool):
    name = "radon"
    languages = ["python"]
    category = "debt"
    binary = "radon"

    async def run(self, repo_path: str, language: str) -> List[Finding]:
        findings = []
        try:
            proc = await asyncio.create_subprocess_exec(
                "radon", "mi", repo_path, "-j",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=30)
            data = json.loads(stdout)
            for file_path, mi_score in data.items():
                score = mi_score if isinstance(mi_score, (int, float)) else mi_score.get("mi", 100)
                if score < 20:
                    findings.append(Finding(
                        file_path=file_path,
                        line_start=1,
                        severity="major",
                        category="debt",
                        rule_id="MI_LOW",
                        message=f"Maintainability Index is {score:.1f} (very low — hard to maintain)",
                        tool="radon",
                    ))
        except Exception:
            pass
        return findings
