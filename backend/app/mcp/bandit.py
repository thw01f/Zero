import asyncio, json
from typing import List
from .base import BaseTool, Finding

SEV_MAP = {"HIGH": "critical", "MEDIUM": "major", "LOW": "minor"}


class BanditTool(BaseTool):
    name = "bandit"
    languages = ["python"]
    category = "security"
    binary = "bandit"

    async def run(self, repo_path: str, language: str) -> List[Finding]:
        if language not in self.languages or not self._available():
            return []
        try:
            proc = await asyncio.create_subprocess_exec(
                "bandit", "-r", repo_path, "-f", "json", "-q", "--exit-zero",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=60)
            data = json.loads(stdout)
        except Exception:
            return []
        findings = []
        for r in data.get("results", []):
            findings.append(Finding(
                file_path=r.get("filename", ""),
                line_start=r.get("line_number", 0),
                severity=SEV_MAP.get(r.get("issue_severity", "LOW"), "minor"),
                category="security",
                rule_id=r.get("test_id", "bandit"),
                message=r.get("issue_text", ""),
                tool="bandit",
                cwe_id=str(r.get("issue_cwe", {}).get("id")) if isinstance(r.get("issue_cwe"), dict) else None,
            ))
        return findings
