import enum
import datetime
import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, Enum, Boolean, JSON
from sqlalchemy.orm import relationship
from .database import Base


def _uuid(): return str(uuid.uuid4())


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
    mandatory = "MANDATORY"
    suggested = "SUGGESTED"
    optional = "OPTIONAL"
    informational = "INFORMATIONAL"


class Project(Base):
    __tablename__ = "projects"
    id            = Column(String(36), primary_key=True, default=_uuid)
    name          = Column(String(256))
    repo_url      = Column(String(512), unique=True)
    language      = Column(String(32), default="auto")
    standards_doc = Column(Text, nullable=True)
    auto_rescan   = Column(Boolean, default=False)
    rescan_hours  = Column(Integer, default=24)
    created_at    = Column(DateTime, default=datetime.datetime.utcnow)
    last_scan_at  = Column(DateTime, nullable=True)
    jobs          = relationship("Job", back_populates="project", cascade="all, delete")
    advisories    = relationship("Advisory", back_populates="project", cascade="all, delete")


class Job(Base):
    __tablename__ = "jobs"
    id                = Column(String(36), primary_key=True, default=_uuid)
    project_id        = Column(String(36), ForeignKey("projects.id"), nullable=True)
    repo_url          = Column(String(512))
    language          = Column(String(32))
    standards_doc     = Column(Text, nullable=True)
    status            = Column(Enum(StatusEnum), default=StatusEnum.queued)
    progress          = Column(Integer, default=0)
    scan_time_ms      = Column(Integer, nullable=True)
    summary_narrative = Column(Text, nullable=True)
    overall_debt_score= Column(Float, nullable=True)
    overall_grade     = Column(String(1), nullable=True)
    created_at        = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at      = Column(DateTime, nullable=True)
    project           = relationship("Project", back_populates="jobs")
    issues            = relationship("Issue", back_populates="job", cascade="all, delete")
    modules           = relationship("Module", back_populates="job", cascade="all, delete")
    dep_updates       = relationship("DepUpdate", back_populates="job", cascade="all, delete")
    misconfigs        = relationship("Misconfig", back_populates="job", cascade="all, delete")
    compliance_results= relationship("ComplianceResult", back_populates="job", cascade="all, delete")


class Issue(Base):
    __tablename__ = "issues"
    id              = Column(String(36), primary_key=True, default=_uuid)
    job_id          = Column(String(36), ForeignKey("jobs.id"))
    file_path       = Column(String(512))
    line_start      = Column(Integer)
    line_end        = Column(Integer, nullable=True)
    severity        = Column(Enum(SeverityEnum))
    category        = Column(String(64))
    rule_id         = Column(String(128))
    message         = Column(Text)
    tool            = Column(String(32))
    owasp_category  = Column(String(64), nullable=True)
    cwe_id          = Column(String(32), nullable=True)
    llm_explanation = Column(Text, nullable=True)
    fix_diff        = Column(Text, nullable=True)
    fix_accepted    = Column(Integer, default=0)
    job             = relationship("Job", back_populates="issues")


class Module(Base):
    __tablename__ = "modules"
    id                   = Column(String(36), primary_key=True, default=_uuid)
    job_id               = Column(String(36), ForeignKey("jobs.id"))
    path                 = Column(String(512))
    loc                  = Column(Integer, default=0)
    complexity_avg       = Column(Float, default=0.0)
    complexity_max       = Column(Float, default=0.0)
    churn_score          = Column(Float, default=0.0)
    debt_score           = Column(Float, default=0.0)
    grade                = Column(String(1), default="A")
    issue_count_critical = Column(Integer, default=0)
    issue_count_major    = Column(Integer, default=0)
    issue_count_minor    = Column(Integer, default=0)
    job                  = relationship("Job", back_populates="modules")


class DepUpdate(Base):
    __tablename__ = "dep_updates"
    id               = Column(String(36), primary_key=True, default=_uuid)
    job_id           = Column(String(36), ForeignKey("jobs.id"))
    ecosystem        = Column(String(32))
    package_name     = Column(String(256))
    current_version  = Column(String(64))
    latest_version   = Column(String(64))
    classification   = Column(Enum(UpdateClassEnum))
    cve_ids          = Column(JSON, default=list)
    changelog_summary= Column(Text, nullable=True)
    upgrade_command  = Column(String(256))
    created_at       = Column(DateTime, default=datetime.datetime.utcnow)
    job              = relationship("Job", back_populates="dep_updates")


class Advisory(Base):
    __tablename__ = "advisories"
    id               = Column(String(36), primary_key=True, default=_uuid)
    project_id       = Column(String(36), ForeignKey("projects.id"), nullable=True)
    source           = Column(String(32))
    advisory_id      = Column(String(128), unique=True)
    package_name     = Column(String(256), nullable=True)
    ecosystem        = Column(String(32), nullable=True)
    severity         = Column(Enum(SeverityEnum))
    cvss_score       = Column(Float, nullable=True)
    title            = Column(Text)
    description      = Column(Text, nullable=True)
    affected_versions= Column(Text, nullable=True)
    fixed_version    = Column(String(64), nullable=True)
    advisory_url     = Column(String(512), nullable=True)
    affects_project  = Column(Boolean, default=False)
    is_read          = Column(Boolean, default=False)
    published_at     = Column(DateTime, nullable=True)
    fetched_at       = Column(DateTime, default=datetime.datetime.utcnow)
    project          = relationship("Project", back_populates="advisories")


class Misconfig(Base):
    __tablename__ = "misconfigs"
    id            = Column(String(36), primary_key=True, default=_uuid)
    job_id        = Column(String(36), ForeignKey("jobs.id"))
    tool          = Column(String(32))
    resource_type = Column(String(64))
    file_path     = Column(String(512))
    line_start    = Column(Integer, nullable=True)
    check_id      = Column(String(128))
    title         = Column(Text)
    severity      = Column(Enum(SeverityEnum))
    remediation   = Column(Text, nullable=True)
    job           = relationship("Job", back_populates="misconfigs")


class ComplianceResult(Base):
    __tablename__ = "compliance_results"
    id           = Column(String(36), primary_key=True, default=_uuid)
    job_id       = Column(String(36), ForeignKey("jobs.id"))
    framework    = Column(String(32))
    control_id   = Column(String(64))
    control_name = Column(Text)
    status       = Column(String(16))
    issue_count  = Column(Integer, default=0)
    evidence     = Column(JSON, default=list)
    job          = relationship("Job", back_populates="compliance_results")


class SelfHealthSnapshot(Base):
    __tablename__ = "self_health"
    id                = Column(String(36), primary_key=True, default=_uuid)
    captured_at       = Column(DateTime, default=datetime.datetime.utcnow)
    scanner_versions  = Column(JSON)
    own_cve_count     = Column(Integer, default=0)
    disk_free_gb      = Column(Float)
    redis_queue_depth = Column(Integer)
    last_advisory_poll= Column(DateTime, nullable=True)
    celery_workers    = Column(Integer, default=0)
    status            = Column(String(16), default="healthy")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id         = Column(String(36), primary_key=True, default=_uuid)
    job_id     = Column(String(36), ForeignKey("jobs.id"))
    role       = Column(String(16))
    content    = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
