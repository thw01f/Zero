from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Optional, List
import shutil


@dataclass
class Finding:
    file_path: str
    line_start: int
    severity: str           # critical|major|minor|info
    category: str           # security|smell|debt|secret|dep|misconfig
    rule_id: str
    message: str
    tool: str
    line_end: Optional[int] = None
    resource_type: Optional[str] = None
    check_id: Optional[str] = None
    owasp_category: Optional[str] = None
    cwe_id: Optional[str] = None
    llm_explanation: Optional[str] = None


class BaseTool(ABC):
    name: str = "base"
    languages: List[str] = ["all"]
    category: str = "security"
    binary: str = ""

    def is_applicable(self, language: str) -> bool:
        return "all" in self.languages or language in self.languages

    def _available(self) -> bool:
        if not self.binary:
            return True
        return shutil.which(self.binary) is not None

    @abstractmethod
    async def run(self, repo_path: str, language: str) -> List[Finding]:
        ...
