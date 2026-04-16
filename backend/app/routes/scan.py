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
        finally:
            db.close()

    import threading
    t = threading.Thread(target=_run, daemon=True)
    t.start()


@router.post("", response_model=ScanResponse, status_code=202)
def submit_scan(req: ScanRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    job_id = str(uuid.uuid4())
    job = Job(
        id=job_id,
        repo_url=str(req.repo_url),
        language=req.language.value,
        standards_doc=req.standards_doc,
        project_id=req.project_id,
        status=StatusEnum.queued,
        progress=0,
    )
    db.add(job)
    db.commit()

    if not _try_celery(job_id, str(req.repo_url), req.language.value, req.standards_doc):
        # Celery not available — run directly in background thread
        background_tasks.add_task(_run_in_background, job_id, str(req.repo_url), req.language.value, req.standards_doc)

    return ScanResponse(job_id=job_id, status="queued", message="Scan enqueued")


@router.get("/jobs/{job_id}", response_model=JobStatus)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatus(
        job_id=job.id,
        status=job.status.value,
        progress=job.progress,
        scan_time_ms=job.scan_time_ms,
        created_at=job.created_at.isoformat(),
        language=job.language,
    )


@router.get("/jobs")
def list_jobs(limit: int = 20, db: Session = Depends(get_db)):
    from ..models import Job
    jobs = db.query(Job).order_by(Job.created_at.desc()).limit(limit).all()
    return [
        {
            "job_id": j.id,
            "repo_url": j.repo_url,
            "language": j.language,
            "status": j.status.value,
            "progress": j.progress,
            "grade": j.overall_grade,
            "debt_score": j.overall_debt_score,
            "scan_time_ms": j.scan_time_ms,
            "created_at": j.created_at.isoformat(),
        }
        for j in jobs
    ]
