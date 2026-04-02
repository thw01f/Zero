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
