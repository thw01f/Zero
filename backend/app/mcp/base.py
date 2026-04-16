from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class Finding:
    file_path: str = ""
    line_start: int = 0
    line_end: Optional[int] = None
    severity: str = "info"
    category: str = "quality"
    rule_id: Optional[str] = None
    message: str = ""
    tool: str = ""
    resource_type: Optional[str] = None
    check_id: Optional[str] = None
    owasp_category: Optional[str] = None
    cwe_id: Optional[str] = None
    llm_explanation: Optional[str] = None


class BaseTool:
    name: str = ""
    languages: List[str] = []
    category: str = "quality"
    binary: Optional[str] = None

    def _available(self) -> bool:
        import shutil
        if self.binary:
            return shutil.which(self.binary) is not None
        return True

    async def run(self, repo_path: str, language: str) -> List[Finding]:
        raise NotImplementedError
