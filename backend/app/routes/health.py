from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import SelfHealthSnapshot

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0", "service": "DarkLead"}


@router.get("/self-health")
async def self_health(db: Session = Depends(get_db)):
    snap = db.query(SelfHealthSnapshot).order_by(SelfHealthSnapshot.captured_at.desc()).first()
    if not snap: