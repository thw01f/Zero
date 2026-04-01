from typing import List
from .base import BaseTool, Finding


class LizardTool(BaseTool):
    name = "lizard"
    languages = ["all"]
    category = "debt"
    binary = ""

    def _available(self) -> bool:
        try:
            import lizard
            return True
        except ImportError:
            return False

    async def run(self, repo_path: str, language: str) -> List[Finding]:
        try:
            import lizard
            results = lizard.analyze([repo_path])
        except Exception:
            return []

        findings = []
        for file_info in results:
            for func in file_info.function_list:
                ccn = func.cyclomatic_complexity
                if ccn >= 10:
                    severity = "critical" if ccn >= 15 else "major"
                    findings.append(Finding(
                        file_path=file_info.filename,
                        line_start=func.start_line,
                        line_end=func.end_line,
                        severity=severity,
                        category="debt",
                        rule_id="CCN_HIGH",
                        message=f"Function '{func.name}' has cyclomatic complexity {ccn} (threshold: 10)",
                        tool="lizard",
                    ))
        return findings
