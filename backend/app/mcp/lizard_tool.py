from typing import List
from .base import BaseTool, Finding


class LizardTool(BaseTool):
    name = "lizard"
    languages = ["python", "javascript", "typescript", "java", "go", "c", "cpp"]
    category = "quality"

    async def run(self, repo_path: str, language: str) -> List[Finding]:
        if language not in self.languages:
            return []
        try:
            import lizard
            result = lizard.analyze([repo_path])
            findings = []
            for f in result:
                for fn in f.function_list:
                    if fn.cyclomatic_complexity > 10:
                        sev = "critical" if fn.cyclomatic_complexity > 25 else "major" if fn.cyclomatic_complexity > 15 else "minor"
                        findings.append(Finding(
                            file_path=f.filename, line_start=fn.start_line,
                            severity=sev, category="quality",
                            rule_id="high-ccn",
                            message=f"Function '{fn.name}' has cyclomatic complexity {fn.cyclomatic_complexity}",
                            tool="lizard",
                        ))
            return findings
        except Exception:
            return []

# Lizard and Radon given longer 120s timeout; env-checker capped at 30s.
