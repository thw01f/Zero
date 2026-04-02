import asyncio, json, os
from typing import List
from .base import BaseTool, Finding


class GitleaksTool(BaseTool):
    name = "gitleaks"
    languages = ["all"]
    category = "secret"
    binary = "gitleaks"

    async def run(self, repo_path: str, language: str) -> List[Finding]:
        if not self._available():
            return []
        try:
            out_file = f"/tmp/gitleaks_{os.getpid()}.json"
            proc = await asyncio.create_subprocess_exec(
                "gitleaks", "detect", "--source", repo_path,
                "--report-format", "json", "--report-path", out_file,
                "--exit-code", "0", "--no-banner",
                stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
            )
            await asyncio.wait_for(proc.communicate(), timeout=90)
            import json as _json
            try:
                data = _json.loads(open(out_file).read()) or []
            except Exception:
                data = []
            findings = []
            for r in data:
                findings.append(Finding(
                    file_path=r.get("File", ""), line_start=r.get("StartLine", 0),
                    severity="critical", category="secret",
                    rule_id=r.get("RuleID", "gitleaks"),
                    message=f"Secret detected: {r.get('Description', '')}",
                    tool="gitleaks",
                ))
            return findings
        except Exception:
            return []
