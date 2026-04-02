import asyncio, json
from typing import List
from .base import BaseTool, Finding


class DetectSecretsTool(BaseTool):
    name = "detect-secrets"
    languages = ["all"]
    category = "secret"
    binary = "detect-secrets"

    async def run(self, repo_path: str, language: str) -> List[Finding]:
        if not self._available():
            return []
        try:
            proc = await asyncio.create_subprocess_exec(
                "detect-secrets", "scan", repo_path,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=60)
            data = json.loads(stdout)
            findings = []
            for fpath, secrets in data.get("results", {}).items():
                for s in secrets:
                    findings.append(Finding(
                        file_path=fpath, line_start=s.get("line_number", 0),
                        severity="critical", category="secret",
                        rule_id=s.get("type", "secret"),
                        message=f"Potential secret: {s.get('type','')}",
                        tool="detect-secrets",
                    ))
            return findings
        except Exception:
            return []
