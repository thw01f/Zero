from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Job, Issue
from ..export import build_report_dict, generate_pdf, generate_issues_csv

router = APIRouter(tags=["report"])


@router.get("/report/{job_id}")
def get_report(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status.value not in ("complete", "failed"):
        raise HTTPException(status_code=202, detail="Scan still in progress")
    return build_report_dict(job_id, db)

