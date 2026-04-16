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
        q = q.filter(Advisory.project_id == project_id)
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