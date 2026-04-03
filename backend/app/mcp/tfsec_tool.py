import asyncio, json
from typing import List
from .base import BaseTool, Finding
import os

SEV = {"CRITICAL": "critical", "HIGH": "major", "MEDIUM": "minor", "LOW": "info"}


class TfsecTool(BaseTool):
    name = "tfsec"
    languages = ["all"]
    category = "misconfig"
    binary = "tfsec"

    async def run(self, repo_path: str, language: str) -> List[Finding]:
        if not self._available():
            return []
        tf_files = list(__import__('pathlib').Path(repo_path).rglob("*.tf"))
        if not tf_files:
            return []
        try:
            proc = await asyncio.create_subprocess_exec(
                "tfsec", repo_path, "--format", "json", "--no-colour",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=60)
            data = json.loads(stdout)
            return [
                Finding(
                    file_path=r.get("location", {}).get("filename", ""),
                    line_start=r.get("location", {}).get("start_line", 0),
                    severity=SEV.get(r.get("severity", "LOW"), "info"),
                    category="misconfig", rule_id=r.get("rule_id"),
                    message=r.get("description", ""), tool="tfsec",
                    resource_type="Terraform", check_id=r.get("rule_id"),
                )
                for r in data.get("results", [])
            ]
        except Exception:
            return []
