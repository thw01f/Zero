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
                db.commit()
        except Exception:
            pass

    async def ws_send(msg):
        ws(msg)

    try:
        # 1. Clone
        ws({"event": "progress", "stage": "cloning", "progress": 5})
        clone_repo(repo_url, repo_path)
        ws({"event": "progress", "stage": "cloned", "progress": 8})

        # 2. Language detect
        if language == "auto":
            language = detect_language(repo_path)
            j = db.query(Job).filter(Job.id == job_id).first()
            if j:
                j.language = language
                db.commit()

        # 3. Prep
        loc_map = count_loc(repo_path, language)
        churn_map = compute_churn(repo_path)
        ws({"event": "progress", "stage": "analyzing", "progress": 10})

        # 4. Scanner ensemble
        orchestrator.register_tools()
        raw_findings = await orchestrator.run_all(repo_path, language, ws_send)
        ws({"event": "progress", "stage": "scan_complete", "progress": 50})

        # 5. LLM triage
        ws({"event": "llm_start", "stage": "triage", "progress": 52})
        triaged = await triage_findings(raw_findings)
        ws({"event": "llm_done", "stage": "triage", "progress": 65})

        # 6. Fix generation
        sast_findings = [f for f in triaged if f.category != "misconfig"]
        with_fixes = await generate_fixes(sast_findings, repo_path, language, standards_doc)
        ws({"event": "llm_done", "stage": "fixes", "progress": 75})

        # 7. Misconfig remediation
        misconfig_findings = [f for f in triaged if f.category == "misconfig"]
        with_remediations = await generate_misconfig_remediation(misconfig_findings, repo_path)
        ws({"event": "llm_done", "stage": "misconfigs", "progress": 80})

        # 8. Module aggregation
        modules_data = aggregate_modules(triaged, loc_map, churn_map, repo_path)
        ws({"event": "progress", "stage": "debt_scored", "progress": 83})

        # 9. Compliance mapping
        compliance = map_findings_to_compliance(triaged)
        persist_compliance(job_id, compliance, db)
        ws({"event": "progress", "stage": "compliance", "progress": 86})

        # 10. Persist issues
        fix_map = {id(f): diff for f, diff in with_fixes}
        for f in triaged:
            if f.category == "misconfig":
                continue
            issue = Issue(
                id=str(uuid.uuid4()),
                job_id=job_id,
                file_path=f.file_path,
                line_start=f.line_start,
                line_end=f.line_end,
                severity=f.severity,
                category=f.category,
                rule_id=f.rule_id,
                message=f.message,
                tool=f.tool,
                owasp_category=f.owasp_category,