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
