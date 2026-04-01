import asyncio, json
from typing import List
from .base import BaseTool, Finding

SEV_MAP = {"CRITICAL": "critical", "HIGH": "major", "MEDIUM": "minor", "LOW": "info"}


class TfsecTool(BaseTool):
    name = "tfsec"
    languages = ["all"]
    category = "misconfig"
    binary = "tfsec"

    async def run(self, repo_path: str, language: str) -> List[Finding]:
        try:
            proc = await asyncio.create_subprocess_exec(
                "tfsec", repo_path, "--format", "json", "--soft-fail",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=60)
            data = json.loads(stdout)
        except Exception:
            return []

        findings = []
        for result in data.get("results", []):
            loc = result.get("location", {})
            findings.append(Finding(
                file_path=loc.get("filename", ""),
                line_start=loc.get("start_line", 0),
                line_end=loc.get("end_line"),
                severity=SEV_MAP.get(result.get("severity", "MEDIUM"), "minor"),
                category="misconfig",
                rule_id=result.get("rule_id", "tfsec"),
                message=result.get("description", ""),
                tool="tfsec",
                resource_type="Terraform",
            ))
        return findings
