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
    if job.status.value == "queued":
        raise HTTPException(status_code=202, detail="Scan still in progress")
    return build_report_dict(job_id, db)


@router.post("/fixes/{issue_id}/accept")
def accept_fix(issue_id: str, body: dict, db: Session = Depends(get_db)):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    issue.fix_accepted = 1 if body.get("accepted") else -1
    db.commit()
    return {"ok": True}


@router.get("/export/{job_id}/json")
def export_json(job_id: str, db: Session = Depends(get_db)):
    report = build_report_dict(job_id, db)
    if not report:
        raise HTTPException(status_code=404)
    import json
    return Response(content=json.dumps(report, indent=2),
                    media_type="application/json",
                    headers={"Content-Disposition": f"attachment; filename=darklead_{job_id}.json"})


@router.get("/export/{job_id}/pdf")
def export_pdf(job_id: str, db: Session = Depends(get_db)):
    report = build_report_dict(job_id, db)
    if not report:
        raise HTTPException(status_code=404)
    pdf = generate_pdf(report)
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=darklead_{job_id}.pdf"})


@router.get("/export/{job_id}/csv")
def export_csv(job_id: str, db: Session = Depends(get_db)):
    report = build_report_dict(job_id, db)
    if not report:
        raise HTTPException(status_code=404)
    csv_data = generate_issues_csv(report)
    return Response(content=csv_data, media_type="text/csv",
                    headers={"Content-Disposition": f"attachment; filename=darklead_{job_id}.csv"})

# PERF: Report endpoint returns ETag based on job_id+completed_at. 304 on unchanged repo
