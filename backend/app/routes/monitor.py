from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from ..database import get_db
from ..models import Advisory, DepUpdate, Project
from ..schemas import AdvisorySchema, DepUpdateSchema, ProjectCreate, ProjectSchema
import uuid, datetime

router = APIRouter(tags=["monitor"])


@router.get("/advisories", response_model=List[AdvisorySchema])
def list_advisories(
    project_id: Optional[str] = None,
    unread_only: bool = False,
    severity: Optional[str] = None,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    q = db.query(Advisory)
    if project_id:
        pass  # Advisory is global; project_id filter not applicable
    if unread_only:
        q = q.filter(Advisory.is_read == False)
    if severity:
        q = q.filter(Advisory.severity == severity)
    advisories = q.order_by(Advisory.fetched_at.desc()).limit(limit).all()
    return [_adv_schema(a) for a in advisories]


@router.post("/advisories/{advisory_id}/read")
def mark_read(advisory_id: str, db: Session = Depends(get_db)):
    adv = db.query(Advisory).filter(Advisory.id == advisory_id).first()
    if adv:
        adv.is_read = True
        db.commit()
    return {"ok": True}


@router.get("/updates/{job_id}", response_model=List[DepUpdateSchema])
def get_updates(job_id: str, db: Session = Depends(get_db)):
    updates = db.query(DepUpdate).filter(DepUpdate.job_id == job_id).all()
    return [_dep_schema(d) for d in updates]


@router.post("/projects", response_model=ProjectSchema)
def create_project(body: ProjectCreate, db: Session = Depends(get_db)):
    proj = Project(
        id=str(uuid.uuid4()),
        name=body.name,
        repo_url=str(body.repo_url),
        language=body.language.value,
        standards_doc=body.standards_doc,
        auto_rescan=body.auto_rescan,
        rescan_hours=body.rescan_hours,
    )
    db.add(proj)
    db.commit()
    return _proj_schema(proj)


@router.get("/projects", response_model=List[ProjectSchema])
def list_projects(db: Session = Depends(get_db)):
    return [_proj_schema(p) for p in db.query(Project).all()]


@router.delete("/projects/{project_id}")
def delete_project(project_id: str, db: Session = Depends(get_db)):
    p = db.query(Project).filter(Project.id == project_id).first()
    if p:
        db.delete(p)
        db.commit()
    return {"ok": True}


def _adv_schema(a) -> dict:
    return {
        "id": a.id, "source": a.source, "advisory_id": a.advisory_id,
        "package_name": a.package_name, "ecosystem": a.ecosystem,
        "severity": a.severity, "cvss_score": a.cvss_score,
        "title": a.title, "description": a.description,
        "fixed_version": a.fixed_version, "advisory_url": a.advisory_url,
        "affects_project": a.affects_project, "is_read": a.is_read,
        "published_at": a.published_at.isoformat() if a.published_at else None,
    }

def _dep_schema(d) -> dict:
    return {
        "id": d.id, "ecosystem": d.ecosystem, "package_name": d.package_name,
        "current_version": d.current_version, "latest_version": d.latest_version,
        "classification": d.classification, "cve_ids": d.cve_ids or [],
        "changelog_summary": d.changelog_summary, "upgrade_command": d.upgrade_command,
    }

def _proj_schema(p) -> dict:
    return {
        "id": p.id, "name": p.name, "repo_url": p.repo_url,
        "language": p.language, "auto_rescan": p.auto_rescan,
        "rescan_hours": p.rescan_hours,
        "created_at": p.created_at.isoformat(),
        "last_scan_at": p.last_scan_at.isoformat() if p.last_scan_at else None,
    }
