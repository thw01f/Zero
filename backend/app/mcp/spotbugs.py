from typing import List
from .base import BaseTool, Finding


class SpotBugsTool(BaseTool):
    name = "spotbugs"
    languages = ["java"]
    category = "security"
    binary = "spotbugs"

    def _available(self) -> bool:
        return False  # too heavy for hackathon env; stub

    async def run(self, repo_path: str, language: str) -> List[Finding]:
        return []
