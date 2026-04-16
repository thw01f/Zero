import asyncio, json
from typing import List
from .base import BaseTool, Finding

SEV_MAP = {"HIGH": "critical", "MEDIUM": "major", "LOW": "minor", "CRITICAL": "critical"}


class CheckovTool(BaseTool):
    name = "checkov"
    languages = ["all"]
    category = "misconfig"
    binary = "checkov"

    async def run(self, repo_path: str, language: str) -> List[Finding]:
        try:
            proc = await asyncio.create_subprocess_exec(
                "checkov", "-d", repo_path, "--output", "json",
                "--quiet", "--compact",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=120)
            raw = stdout.decode(errors="replace").strip()
            if not raw:
                return []
            # checkov may output multiple JSON objects; take last valid one
            data = json.loads(raw)
        except Exception:
            return []

        findings = []
        results = data if isinstance(data, list) else [data]
        for section in results:
            for check in section.get("results", {}).get("failed_checks", []):
                resource = check.get("resource", "")
                file_path = check.get("file_path", "")
                line_start = check.get("file_line_range", [0, 0])[0]
                check_id = check.get("check_id", "CKV_UNKNOWN")
                title = check.get("check_id", "") + ": " + check.get("check_result", {}).get("result", "FAILED")
                findings.append(Finding(
                    file_path=file_path,
                    line_start=line_start,
                    severity=SEV_MAP.get(check.get("severity", "MEDIUM"), "minor"),
                    category="misconfig",
                    rule_id=check_id,
                    message=check.get("check_id", ""),
                    tool="checkov",
                    resource_type=check.get("check_type", "IaC"),
                    check_id=check_id,
                ))
        return findings
