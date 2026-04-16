import uuid
import asyncio
import shutil
import tempfile
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File, Form
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Job, StatusEnum
from ..schemas import ScanRequest, ScanResponse, JobStatus

router = APIRouter(prefix="/scan", tags=["scan"])


def _try_celery(job_id: str, repo_url: str, language: str, standards_doc):
    """Returns True only if a Celery worker is actually available to process the task."""
    try:
        from ..tasks import celery_app, run_scan_task
        inspect = celery_app.control.inspect(timeout=1.0)
        active = inspect.active()
        if not active:
            return False
        run_scan_task.delay(job_id, repo_url, language, standards_doc)
        return True
    except Exception:
        return False


def _run_in_background(job_id: str, repo_url: str, language: str, standards_doc):
    """Fallback: run scan pipeline via asyncio in a thread (no Celery required)."""
    from ..tasks import _scan_pipeline
    from ..database import SessionLocal

    def _run():
        import logging as _log
        _logger = _log.getLogger("app.tasks.bg")
        db = SessionLocal()
        try:
            asyncio.run(_scan_pipeline(job_id, repo_url, language, standards_doc, db))
        except Exception as _e:
            _logger.error(f"Background scan {job_id[:8]} failed: {_e}", exc_info=True)
            try:
                from ..models import StatusEnum
                _j = db.query(__import__('app.models', fromlist=['Job']).Job).filter_by(id=job_id).first()
                if _j and _j.status.value not in ('complete',):
                    _j.status = StatusEnum.failed
                    db.commit()
            except Exception:
                pass
        finally:
            db.close()

    import threading
    t = threading.Thread(target=_run, daemon=True)
    t.start()


def _normalize_repo_url(url: str) -> str:
    """Ensure GitHub/GitLab URLs are https:// and end without .git."""
    url = url.strip()
    # Handle shorthand like github.com/owner/repo or gitlab.com/owner/repo
    if url and not url.startswith(("http://", "https://", "/", ".")):
        url = "https://" + url
    # Strip trailing .git for consistency
    if url.endswith(".git"):
        url = url[:-4]
    return url


@router.post("", response_model=ScanResponse, status_code=202)
def submit_scan(req: ScanRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    repo_url = _normalize_repo_url(str(req.repo_url))
    job_id = str(uuid.uuid4())
    job = Job(
        id=job_id,
        repo_url=repo_url,
        language=req.language.value,
        standards_doc=req.standards_doc,
        project_id=req.project_id,
        status=StatusEnum.queued,
        progress=0,
    )
    db.add(job)
    db.commit()

    if not _try_celery(job_id, repo_url, req.language.value, req.standards_doc):
        background_tasks.add_task(_run_in_background, job_id, repo_url, req.language.value, req.standards_doc)

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
    from ..models import Job, Issue
    from sqlalchemy import func
    jobs = db.query(Job).order_by(Job.created_at.desc()).limit(limit).all()
    # Count issues per job in one query
    counts = dict(
        db.query(Issue.job_id, func.count(Issue.id))
        .filter(Issue.job_id.in_([j.id for j in jobs]))
        .group_by(Issue.job_id)
        .all()
    )
    return [
        {
            "job_id": j.id,
            "repo_url": j.repo_url,
            "language": j.language,
            "status": j.status.value,
            "progress": j.progress,
            "grade": j.overall_grade,
            "debt_score": j.overall_debt_score,
            "issue_count": counts.get(j.id, 0),
            "scan_time_ms": j.scan_time_ms,
            "created_at": j.created_at.isoformat(),
        }
        for j in jobs
    ]

@router.post("/upload", response_model=ScanResponse, status_code=202)
async def upload_scan(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    language: str = Form("auto"),
    project_id: str = Form(None),
):
    """Accept a zip or tar.gz archive, extract it, and run the scan pipeline."""
    suffix = Path(file.filename or "upload").suffix.lower()
    allowed = {".zip", ".gz", ".tgz", ".tar"}
    if suffix not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported file type '{suffix}'. Use .zip or .tar.gz")

    tmp_dir = Path(tempfile.mkdtemp(prefix="dl_upload_"))
    archive_path = tmp_dir / (file.filename or "upload")
    try:
        with archive_path.open("wb") as f:
            shutil.copyfileobj(file.file, f)
        # Extract
        extract_dir = tmp_dir / "src"
        extract_dir.mkdir()
        if suffix == ".zip":
            import zipfile
            with zipfile.ZipFile(archive_path) as z:
                z.extractall(extract_dir)
        else:
            import tarfile
            with tarfile.open(archive_path) as t:
                t.extractall(extract_dir)
    except Exception as e:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail=f"Failed to extract archive: {e}")

    # Use local path as repo_url; pipeline handles both URLs and paths
    repo_url = str(extract_dir)
    job_id = str(uuid.uuid4())
    job = Job(
        id=job_id,
        repo_url=f"upload://{file.filename}",
        language=language,
        project_id=project_id,
        status=StatusEnum.queued,
        progress=0,
    )
    db.add(job)
    db.commit()

    if not _try_celery(job_id, repo_url, language, None):
        background_tasks.add_task(_run_in_background, job_id, repo_url, language, None)

    return ScanResponse(job_id=job_id, status="queued", message="Upload scan enqueued")


# GET /api/scan/jobs returns list of past scans for frontend history panel.
