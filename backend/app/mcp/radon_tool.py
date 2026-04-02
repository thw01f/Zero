from typing import List
from .base import BaseTool, Finding


class RadonTool(BaseTool):
    name = "radon"
    languages = ["python"]
    category = "quality"

    async def run(self, repo_path: str, language: str) -> List[Finding]:
        if language not in self.languages:
            return []
        try:
            import radon.complexity as rc
            import radon.visitors
            from radon.raw import analyze
            from pathlib import Path
            findings = []
            for pyfile in Path(repo_path).rglob("*.py"):
                try:
                    src = pyfile.read_text(errors="replace")
                    blocks = rc.cc_visit(src)
                    for b in blocks:
                        if b.complexity > 10:
                            sev = "critical" if b.complexity > 20 else "major"
                            findings.append(Finding(
                                file_path=str(pyfile), line_start=b.lineno,
                                severity=sev, category="quality",
                                rule_id="radon-cc",
                                message=f"'{b.name}' cyclomatic complexity: {b.complexity}",
                                tool="radon",
                            ))
                except Exception:
                    pass
            return findings
        except Exception:
            return []
