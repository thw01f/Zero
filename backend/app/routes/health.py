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
    snap = db.query(SelfHealthSnapshot).order_by(SelfHealthSnapshot.created_at.desc()).first()
    if not snap:
        from ..self_health import capture_snapshot
        snap_dict = await capture_snapshot()
        return snap_dict
    import json as _json
    return {
        "id": snap.id,
        "created_at": snap.created_at.isoformat(),
        "scanner_versions": _json.loads(snap.scanner_versions or "{}"),
        "own_cve_count": _json.loads(snap.own_cves or "0"),
        "disk_free_gb": snap.disk_free_gb,
        "redis_queue_depth": snap.redis_queue_depth,
        "status": snap.status,
    }


@router.get("/self-health/history")
def self_health_history(db: Session = Depends(get_db)):
    import json as _json
    snaps = db.query(SelfHealthSnapshot).order_by(
        SelfHealthSnapshot.created_at.desc()
    ).limit(24).all()
    return [{"created_at": s.created_at.isoformat(), "status": s.status,
             "own_cve_count": _json.loads(s.own_cves or "0"), "disk_free_gb": s.disk_free_gb}
            for s in snaps]


@router.get("/compliance/{job_id}")
def get_compliance(job_id: str, db: Session = Depends(get_db)):
    from ..models import ComplianceResult
    results = db.query(ComplianceResult).filter(ComplianceResult.job_id == job_id).all()
    return [{"standard": r.standard, "control_id": r.control_id,
             "control_name": r.control_name, "status": r.status,
             "issue_count": r.issue_count, "evidence": r.evidence}
            for r in results]
