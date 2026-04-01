import asyncio, json, tempfile, os, uuid
from typing import List
from .base import BaseTool, Finding


class GitleaksTool(BaseTool):
    name = "gitleaks"
    languages = ["all"]
    category = "secret"
    binary = "gitleaks"

    async def run(self, repo_path: str, language: str) -> List[Finding]:
        out_file = f"/tmp/gl_{uuid.uuid4().hex}.json"
        try:
            proc = await asyncio.create_subprocess_exec(
                "gitleaks", "detect", "--source", repo_path,
                "--report-format", "json", "--report-path", out_file,
                "--no-git", "--exit-code", "0",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await asyncio.wait_for(proc.wait(), timeout=60)
            if not os.path.exists(out_file):
                return []
            with open(out_file) as f:
                data = json.load(f)
        except Exception:
            return []
        finally:
            try: os.unlink(out_file)
            except: pass

        if not data:
            return []
        findings = []
        for r in data:
            findings.append(Finding(
                file_path=r.get("File", ""),
                line_start=r.get("StartLine", 0),
                line_end=r.get("EndLine"),
                severity="critical",
                category="secret",
                rule_id=r.get("RuleID", "gitleaks"),
                message=f"Secret detected: {r.get('Description', 'unknown type')}",
                tool="gitleaks",
            ))
        return findings
