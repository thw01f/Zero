from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
from enum import Enum


class LanguageEnum(str, Enum):
    python = "python"
    javascript = "javascript"
    java = "java"
    auto = "auto"


class ScanRequest(BaseModel):
    repo_url: str
    language: LanguageEnum = LanguageEnum.auto
    standards_doc: Optional[str] = None
    project_id: Optional[str] = None


class ScanResponse(BaseModel):
    job_id: str
    status: str
    message: str


class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: int
    scan_time_ms: Optional[int] = None
    created_at: str
    language: Optional[str] = None


class IssueSchema(BaseModel):
    id: str
    file_path: str
    line_start: int
    line_end: Optional[int] = None
    severity: str
    category: str
    rule_id: str
    message: str
    tool: str
    owasp_category: Optional[str] = None
    cwe_id: Optional[str] = None
    llm_explanation: Optional[str] = None
    fix_diff: Optional[str] = None
    fix_accepted: int = 0


class ModuleSchema(BaseModel):
    id: str
    path: str
    loc: int
    complexity_avg: float
    complexity_max: float
    churn_score: float
    debt_score: float
    grade: str
    issue_count_critical: int
    issue_count_major: int
    issue_count_minor: int


class MisconfigSchema(BaseModel):
    id: str
    tool: str
    resource_type: str
    file_path: str
    line_start: Optional[int] = None
    check_id: str
    title: str
    severity: str
    remediation: Optional[str] = None


class DepUpdateSchema(BaseModel):
    id: str
    ecosystem: str
    package_name: str
    current_version: str
    latest_version: str
    classification: str
    cve_ids: List[str] = []