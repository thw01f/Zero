import asyncio, json, tempfile, os
from typing import List
from .base import BaseTool, Finding

SEV_MAP = {"ERROR": "critical", "WARNING": "major", "INFO": "minor"}


class SemgrepTool(BaseTool):
    name = "semgrep"
    languages = ["all"]
    category = "security"
    binary = "semgrep"

    async def run(self, repo_path: str, language: str) -> List[Finding]:
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            out_file = f.name
        try:
            proc = await asyncio.create_subprocess_exec(
                "semgrep", "--json", "--config=auto",
                "--timeout", "30", "--output", out_file, repo_path,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await asyncio.wait_for(proc.wait(), timeout=60)
            with open(out_file) as f:
                data = json.load(f)
        except Exception:
            return []
        finally:
            try: os.unlink(out_file)
            except: pass

        findings = []
        for r in data.get("results", []):
            findings.append(Finding(
                file_path=r.get("path", ""),
                line_start=r.get("start", {}).get("line", 0),
                line_end=r.get("end", {}).get("line"),
                severity=SEV_MAP.get(r.get("extra", {}).get("severity", "INFO"), "minor"),
                category="security",
                rule_id=r.get("check_id", "semgrep"),
                message=r.get("extra", {}).get("message", ""),
                tool="semgrep",
            ))
        return findings
