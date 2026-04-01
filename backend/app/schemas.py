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
    changelog_summary: Optional[str] = None
    upgrade_command: str


class AdvisorySchema(BaseModel):
    id: str
    source: str
    advisory_id: str
    package_name: Optional[str] = None
    ecosystem: Optional[str] = None
    severity: str
    cvss_score: Optional[float] = None
    title: str
    description: Optional[str] = None
    fixed_version: Optional[str] = None
    advisory_url: Optional[str] = None
    affects_project: bool = False
    is_read: bool = False
    published_at: Optional[str] = None


class ComplianceSchema(BaseModel):
    framework: str
    control_id: str
    control_name: str
    status: str
    issue_count: int
    evidence: List[str] = []


class ReportSchema(BaseModel):
    job_id: str
    repo_url: str
    language: str
    scan_time_ms: int
    total_issues: int
    issues_by_severity: Dict[str, int]
    issues_by_category: Dict[str, int]
    overall_debt_score: float
    overall_grade: str
    issues: List[IssueSchema]
    modules: List[ModuleSchema]
    misconfigs: List[MisconfigSchema]
    dep_updates: List[DepUpdateSchema]
    compliance: List[ComplianceSchema]
    summary_narrative: str
    top_risks: List[str]
    secret_count: int
    mandatory_update_count: int


class ProjectCreate(BaseModel):
    name: str
    repo_url: str
    language: LanguageEnum = LanguageEnum.auto
    standards_doc: Optional[str] = None
    auto_rescan: bool = False
    rescan_hours: int = 24


class ProjectSchema(BaseModel):
    id: str
    name: str
    repo_url: str
    language: str
    auto_rescan: bool
    rescan_hours: int
    created_at: str
    last_scan_at: Optional[str] = None


class ChatRequest(BaseModel):
    message: str


class SelfHealthSchema(BaseModel):
    id: str
    captured_at: str
    scanner_versions: Dict[str, str]
    own_cve_count: int
    disk_free_gb: float
    redis_queue_depth: int
    last_advisory_poll: Optional[str] = None
    celery_workers: int
    status: str
