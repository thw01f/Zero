import uuid
import datetime
from sqlalchemy import Column, String, Integer, Float, Text, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
import enum
from .database import Base


class SeverityEnum(str, enum.Enum):
    critical = "critical"
    major = "major"
    minor = "minor"
    info = "info"


class StatusEnum(str, enum.Enum):
    queued = "queued"
    running = "running"
    complete = "complete"
    failed = "failed"


class UpdateClassEnum(str, enum.Enum):
    MANDATORY = "MANDATORY"
    SUGGESTED = "SUGGESTED"
    OPTIONAL = "OPTIONAL"
    INFORMATIONAL = "INFORMATIONAL"


class Project(Base):
    __tablename__ = "projects"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    repo_url = Column(String, nullable=False)
    language = Column(String, default="auto")
    standards_doc = Column(Text, nullable=True)
    auto_rescan = Column(Boolean, default=False)
    rescan_hours = Column(Integer, default=24)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_scan_at = Column(DateTime, nullable=True)
    jobs = relationship("Job", back_populates="project", cascade="all, delete-orphan")


class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=True)
    repo_url = Column(String, nullable=False)
    language = Column(String, default="auto")
    standards_doc = Column(Text, nullable=True)
    status = Column(Enum(StatusEnum), default=StatusEnum.queued)
    progress = Column(Integer, default=0)
    scan_time_ms = Column(Integer, nullable=True)
    overall_debt_score = Column(Float, nullable=True)
    overall_grade = Column(String, nullable=True)
    summary_narrative = Column(Text, nullable=True)
    top_risks = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    project = relationship("Project", back_populates="jobs")


class Issue(Base):
    __tablename__ = "issues"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    line_start = Column(Integer, default=0)
    line_end = Column(Integer, nullable=True)
    severity = Column(String, default="info")
    category = Column(String, default="quality")
    rule_id = Column(String, nullable=True)
    message = Column(Text, nullable=True)
    tool = Column(String, nullable=True)
    owasp_category = Column(String, nullable=True)
    cwe_id = Column(String, nullable=True)
    llm_explanation = Column(Text, nullable=True)
    fix_diff = Column(Text, nullable=True)
    fix_accepted = Column(Integer, default=0)  # 0=pending, 1=accepted, -1=rejected
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Module(Base):
    __tablename__ = "modules"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, nullable=False)
    path = Column(String, nullable=False)
    language = Column(String, nullable=True)
    loc = Column(Integer, default=0)
    complexity_avg = Column(Float, default=0.0)
    max_complexity = Column(Integer, default=0)
    churn_count = Column(Integer, default=0)
    debt_score = Column(Float, default=0.0)
    grade = Column(String, default="A")
    issue_counts = Column(Text, nullable=True)  # JSON


class Misconfig(Base):
    __tablename__ = "misconfigs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, nullable=False)
    tool = Column(String, nullable=False)
    resource_type = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    line_start = Column(Integer, default=0)
    check_id = Column(String, nullable=True)
    title = Column(Text, nullable=True)
    severity = Column(String, default="minor")
    remediation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class DepUpdate(Base):
    __tablename__ = "dep_updates"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, nullable=False)
    ecosystem = Column(String, nullable=False)
    package_name = Column(String, nullable=False)
    current_version = Column(String, nullable=True)
    latest_version = Column(String, nullable=True)
    classification = Column(Enum(UpdateClassEnum), default=UpdateClassEnum.OPTIONAL)
    cve_ids = Column(Text, nullable=True)  # JSON list
    changelog_summary = Column(Text, nullable=True)
    upgrade_command = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Advisory(Base):
    __tablename__ = "advisories"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source = Column(String, default="nvd")
    advisory_id = Column(String, unique=True, nullable=False)
    package_name = Column(String, nullable=True)
    ecosystem = Column(String, nullable=True)
    severity = Column(String, default="info")
    cvss_score = Column(Float, nullable=True)
    title = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    fixed_version = Column(String, nullable=True)
    advisory_url = Column(String, nullable=True)
    affects_project = Column(Boolean, default=False)
    is_read = Column(Boolean, default=False)
    published_at = Column(DateTime, nullable=True)
    fetched_at = Column(DateTime, default=datetime.datetime.utcnow)


class ComplianceResult(Base):
    __tablename__ = "compliance_results"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, nullable=False)
    standard = Column(String, nullable=False)
    control_id = Column(String, nullable=False)
    control_name = Column(String, nullable=False)
    status = Column(String, default="unknown")
    issue_count = Column(Integer, default=0)
    evidence = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class SelfHealthSnapshot(Base):
    __tablename__ = "self_health_snapshots"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(String, default="healthy")
    scanner_versions = Column(Text, nullable=True)  # JSON
    own_cves = Column(Text, nullable=True)  # JSON
    disk_free_gb = Column(Float, nullable=True)
    redis_queue_depth = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
