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
                cwe_id=f.cwe_id,
                llm_explanation=f.llm_explanation,
                fix_diff=fix_map.get(id(f)),
            )
            db.add(issue)

        # Persist misconfigs
        remediation_map = {id(f): rem for f, rem in with_remediations}
        for f in misconfig_findings:
            db.add(Misconfig(
                id=str(uuid.uuid4()),
                job_id=job_id,
                tool=f.tool,
                resource_type=f.resource_type or "Unknown",
                file_path=f.file_path,
                line_start=f.line_start,
                check_id=f.check_id or f.rule_id,
                title=f.message,
                severity=f.severity,
                remediation=remediation_map.get(id(f)),
            ))

        # Persist modules
        for m in modules_data:
            db.add(Module(**{**m, "job_id": job_id}))

        db.commit()
        ws({"event": "progress", "stage": "persisted", "progress": 90})

        # 11. Summary
        secret_count = sum(1 for f in triaged if f.category == "secret")
        stats = {
            "total": len(triaged),
            "critical": sum(1 for f in triaged if f.severity == "critical"),
            "major": sum(1 for f in triaged if f.severity == "major"),
            "minor": sum(1 for f in triaged if f.severity == "minor"),
            "misconfigs": len(misconfig_findings),
            "secrets": secret_count,
            "mandatory_updates": 0,
            "scan_ms": int((time.time() - start_time) * 1000),
        }
        top_issues = [{"rule": f.rule_id, "severity": f.severity, "file": f.file_path, "message": f.message[:100]}
                      for f in sorted(triaged, key=lambda x: {"critical": 0, "major": 1, "minor": 2, "info": 3}.get(x.severity, 4))[:10]]
        top_mods = [{"path": m["path"], "score": m["debt_score"], "grade": m["grade"]}
                    for m in modules_data[:5]]

        summary = await generate_summary(repo_url, language, stats, top_issues, top_mods)
        ws({"event": "llm_done", "stage": "summary", "progress": 95})

        # 12. Finalize job
        scan_time_ms = int((time.time() - start_time) * 1000)
        overall_debt = weighted_avg_debt(modules_data)

        j = db.query(Job).filter(Job.id == job_id).first()
        if j:
            j.status = StatusEnum.complete
            j.progress = 100
            j.scan_time_ms = scan_time_ms
            j.summary_narrative = summary
            j.overall_debt_score = overall_debt
            j.overall_grade = grade_from_score(overall_debt)
            j.completed_at = datetime.datetime.utcnow()
            db.commit()

        ws({"event": "complete", "progress": 100, "scan_time_ms": scan_time_ms})

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        ws({"event": "error", "message": str(e), "progress": -1})
        raise
    finally:
        shutil.rmtree(repo_path, ignore_errors=True)


@celery_app.task(name="app.tasks.monitor_advisories_task")
def monitor_advisories_task():
    asyncio.run(_monitor_advisories())


async def _monitor_advisories():
    from .monitor.nvd_feed import fetch_recent_cves
    from .database import SessionLocal
    from .models import Advisory
    import uuid

    db = SessionLocal()
    try:
        cves = await fetch_recent_cves(hours=settings.advisory_poll_hours)
        for item in cves:
            cve = item.get("cve", {})
            cve_id = cve.get("id", "")
            if not cve_id:
                continue
            existing = db.query(Advisory).filter(Advisory.advisory_id == cve_id).first()
            if existing:
                continue
            metrics = cve.get("metrics", {})
            cvss = None
            for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
                if key in metrics and metrics[key]:
                    cvss = metrics[key][0].get("cvssData", {}).get("baseScore")
                    break
            severity = "info"
            if cvss:
                if cvss >= 9.0: severity = "critical"
                elif cvss >= 7.0: severity = "major"
                elif cvss >= 4.0: severity = "minor"

            descs = cve.get("descriptions", [])
            desc_text = next((d["value"] for d in descs if d.get("lang") == "en"), "")
            db.add(Advisory(
                id=str(uuid.uuid4()),
                source="nvd",
                advisory_id=cve_id,
                severity=severity,
                cvss_score=cvss,
                title=cve_id + ": " + desc_text[:100],
                description=desc_text[:500],
                advisory_url=f"https://nvd.nist.gov/vuln/detail/{cve_id}",
            ))
        db.commit()
    except Exception as e:
        logger.warning(f"Advisory monitor failed: {e}")
    finally:
        db.close()


@celery_app.task(name="app.tasks.self_health_task")
def self_health_task():
    asyncio.run(_self_health())


async def _self_health():
    from .self_health import capture_snapshot
    from .ws_manager import sse_manager
    snap = await capture_snapshot()
    if snap["status"] != "healthy":
        try:
            loop = asyncio.get_event_loop()
            await sse_manager.publish({"type": "self_health_alert", "data": snap})
        except Exception:
            pass
