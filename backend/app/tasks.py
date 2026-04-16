import asyncio
import datetime
import json
import logging
import shutil
import time
import uuid
from pathlib import Path

from .celery_app import celery_app
from .config import settings
from .database import SessionLocal
from .models import Job, Issue, Module, Misconfig, DepUpdate, Advisory, StatusEnum

logger = logging.getLogger(__name__)


def _publish_ws(job_id: str, msg: dict):
    """Publish progress via Redis pub/sub."""
    try:
        import redis as r
        rc = r.Redis.from_url(settings.redis_url)
        rc.publish(f"ws:{job_id}", json.dumps(msg))
    except Exception as e:
        logger.debug(f"WS publish failed: {e}")


@celery_app.task(bind=True, name="app.tasks.run_scan_task")
def run_scan_task(self, job_id: str, repo_url: str, language: str, standards_doc: str = None):
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return
        job.status = StatusEnum.running
        job.progress = 5
        db.commit()

        asyncio.run(_scan_pipeline(job_id, repo_url, language, standards_doc, db))

    except Exception as e:
        logger.error(f"Scan task failed for {job_id}: {e}", exc_info=True)
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                job.status = StatusEnum.failed
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


async def _scan_pipeline(job_id: str, repo_url: str, language: str, standards_doc: str, db):
    from .mcp import orchestrator
    from .mcp.llm_layer import triage_findings, generate_fixes, generate_misconfig_remediation, generate_summary
    from .git_utils import clone_repo, detect_language, count_loc, compute_churn
    from .aggregator import aggregate_modules, weighted_avg_debt
    from .debt_score import grade_from_score
    from .compliance import map_findings_to_compliance, persist_compliance

    start_time = time.time()
    repo_path = f"/tmp/darklead_{job_id}"

    def ws(msg):
        _publish_ws(job_id, msg)
        # Update DB progress
        try:
            j = db.query(Job).filter(Job.id == job_id).first()
            if j:
                j.progress = msg.get("progress", j.progress)