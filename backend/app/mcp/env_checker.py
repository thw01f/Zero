import asyncio
from typing import List
from pathlib import Path
from .base import BaseTool, Finding
import re

SECRET_PATTERNS = [
    (r'(?i)(api_key|secret|password|passwd|token|auth)\s*=\s*["'][^"']{8,}["']', "Potential hardcoded credential"),
    (r'(?i)aws_access_key_id\s*=\s*["'][A-Z0-9]{20}["']', "AWS Access Key"),
    (r'(?i)private[_-]?key\s*=\s*["'][^"']+["']', "Private key assignment"),
    (r'(?i)database_url\s*=\s*["'][^"']+:[^"']+@', "Database URL with credentials"),
]


class EnvCheckerTool(BaseTool):
    name = "env-checker"
    languages = ["all"]
    category = "secret"

    async def run(self, repo_path: str, language: str) -> List[Finding]:
        findings = []
        exts = {".py", ".js", ".ts", ".env", ".yml", ".yaml", ".json", ".sh", ".rb", ".go"}
        for path in Path(repo_path).rglob("*"):
            if path.suffix not in exts or not path.is_file() or path.stat().st_size > 500_000:
                continue
            if any(p in str(path) for p in ["node_modules", ".git", "__pycache__", "dist"]):
                continue
            try:
                content = path.read_text(errors="replace")
                for pattern, desc in SECRET_PATTERNS:
                    for m in re.finditer(pattern, content):
                        line = content[:m.start()].count('
') + 1
                        findings.append(Finding(
                            file_path=str(path.relative_to(repo_path)),
                            line_start=line, severity="major", category="secret",
                            rule_id="hardcoded-secret", message=f"{desc}: {m.group()[:60]}",
                            tool="env-checker",
                        ))
            except Exception:
                pass
        return findings

# PERF: EnvChecker now skips .pyc, .class, .jar, .png, and other binary formats.
