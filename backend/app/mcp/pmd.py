import asyncio, json
from typing import List
from .base import BaseTool, Finding


class PMDTool(BaseTool):
    name = "pmd"
    languages = ["java"]
    category = "smell"
    binary = "pmd"

    async def run(self, repo_path: str, language: str) -> List[Finding]:
        try:
            proc = await asyncio.create_subprocess_exec(
                "pmd", "check", "-d", repo_path, "-f", "json",
                "-R", "rulesets/java/quickstart.xml", "--no-fail-on-violation",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=120)
            data = json.loads(stdout)
        except Exception:
            return []

        findings = []
        for file_result in data.get("files", []):
            for v in file_result.get("violations", []):
                priority = v.get("priority", 3)
                severity = "critical" if priority <= 1 else "major" if priority <= 3 else "minor"
                findings.append(Finding(
                    file_path=file_result.get("filename", ""),
                    line_start=v.get("beginline", 0),
                    line_end=v.get("endline"),
                    severity=severity,
                    category="smell",
                    rule_id=v.get("rule", "pmd"),
                    message=v.get("description", ""),
                    tool="pmd",
                ))
        return findings
