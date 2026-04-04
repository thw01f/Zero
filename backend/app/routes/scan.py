import uuid
import asyncio
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Job, StatusEnum
from ..schemas import ScanRequest, ScanResponse, JobStatus

router = APIRouter(prefix="/scan", tags=["scan"])


def _try_celery(job_id: str, repo_url: str, language: str, standards_doc):
    """Returns True if Celery task was enqueued, False if Celery/Redis unavailable."""
    try:
        from ..tasks import run_scan_task
        run_scan_task.delay(job_id, repo_url, language, standards_doc)
        return True
    except Exception:
        return False


def _run_in_background(job_id: str, repo_url: str, language: str, standards_doc):
    """Fallback: run scan pipeline via asyncio in a thread (no Celery required)."""
    from ..tasks import _scan_pipeline
    from ..database import SessionLocal

    def _run():
        db = SessionLocal()
        try:
            asyncio.run(_scan_pipeline(job_id, repo_url, language, standards_doc, db))
        except Exception:
            pass