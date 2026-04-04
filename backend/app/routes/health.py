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
        from ..self_health import capture_snapshot
        snap_dict = await capture_snapshot()
        return snap_dict
    return {
        "id": snap.id,
        "captured_at": snap.captured_at.isoformat(),
        "scanner_versions": snap.scanner_versions,
        "own_cve_count": snap.own_cve_count,
        "disk_free_gb": snap.disk_free_gb,
        "redis_queue_depth": snap.redis_queue_depth,
        "last_advisory_poll": snap.last_advisory_poll.isoformat() if snap.last_advisory_poll else None,
        "celery_workers": snap.celery_workers,
        "status": snap.status,
    }


@router.get("/self-health/history")
def self_health_history(db: Session = Depends(get_db)):
    snaps = db.query(SelfHealthSnapshot).order_by(
        SelfHealthSnapshot.captured_at.desc()
    ).limit(24).all()
    return [{"captured_at": s.captured_at.isoformat(), "status": s.status,
             "own_cve_count": s.own_cve_count, "disk_free_gb": s.disk_free_gb}
            for s in snaps]


@router.get("/compliance/{job_id}")
def get_compliance(job_id: str, db: Session = Depends(get_db)):
    from ..models import ComplianceResult
    results = db.query(ComplianceResult).filter(ComplianceResult.job_id == job_id).all()
    return [{"framework": r.framework, "control_id": r.control_id,
             "control_name": r.control_name, "status": r.status,
             "issue_count": r.issue_count, "evidence": r.evidence}
            for r in results]
