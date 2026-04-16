import asyncio
from typing import List
from .base import BaseTool, Finding


class SpotbugsTool(BaseTool):
    name = "spotbugs"
    languages = ["java"]
    category = "security"
    binary = "spotbugs"

    async def run(self, repo_path: str, language: str) -> List[Finding]:
        if language not in self.languages or not self._available():
            return []
        # SpotBugs requires compiled .class files; return empty if not built
        return []
