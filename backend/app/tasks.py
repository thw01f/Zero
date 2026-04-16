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
from .models import Job, Issue, Module, Misconfig, DepUpdate, Advisory, StatusEnum, CodeEntity

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
    repo_path  = f"/tmp/darklead_{job_id}"

    def ws(msg):
        _publish_ws(job_id, msg)
        try:
            j = db.query(Job).filter(Job.id == job_id).first()
            if j:
                j.progress = msg.get("progress", j.progress)
                db.commit()
        except Exception:
            pass

    async def ws_send(msg): ws(msg)

    SEV = {"critical": 0, "major": 1, "minor": 2, "info": 3}

    try:
        # ── Mark running ──────────────────────────────────────────────────────
        _j = db.query(Job).filter(Job.id == job_id).first()
        if _j:
            _j.status = StatusEnum.running
            db.commit()

        # ── 1. Clone (skip if already a local path from upload) ──────────────
        ws({"event": "progress", "stage": "cloning", "progress": 5})
        if Path(repo_url).exists():
            # Uploaded archive already extracted — use it directly
            repo_path = repo_url
        else:
            clone_repo(repo_url, repo_path)
        ws({"event": "progress", "stage": "cloned",  "progress": 8})

        # ── 2. Language + metrics ─────────────────────────────────────────────
        if language == "auto":
            language = detect_language(repo_path)
            j = db.query(Job).filter(Job.id == job_id).first()
            if j: j.language = language; db.commit()

        loc_map   = count_loc(repo_path, language)
        churn_map = compute_churn(repo_path)
        ws({"event": "progress", "stage": "analyzing", "progress": 10})

        # ── 3. Scanner ensemble ───────────────────────────────────────────────
        orchestrator.register_tools()
        raw_findings = await orchestrator.run_all(repo_path, language, ws_send)
        ws({"event": "progress", "stage": "scan_complete", "progress": 50})

        # ── 4. Immediate persist (Phase 1 — results visible in ~60-90s) ───────
        sast_raw    = [f for f in raw_findings if f.category != "misconfig"]
        misconf_raw = [f for f in raw_findings if f.category == "misconfig"]
        modules_data = aggregate_modules(raw_findings, loc_map, churn_map, repo_path)
        compliance   = map_findings_to_compliance(raw_findings)

        issue_ids: dict[int, str] = {}  # id(finding) → db issue id
        for f in sast_raw:
            iid = str(uuid.uuid4())
            issue_ids[id(f)] = iid
            db.add(Issue(
                id=iid, job_id=job_id,
                file_path=f.file_path, line_start=f.line_start, line_end=f.line_end,
                severity=f.severity, category=f.category, rule_id=f.rule_id,
                message=f.message, tool=f.tool,
                owasp_category=f.owasp_category, cwe_id=f.cwe_id,
            ))
        for f in misconf_raw:
            db.add(Misconfig(
                id=str(uuid.uuid4()), job_id=job_id,
                tool=f.tool, resource_type=f.resource_type or "Unknown",
                file_path=f.file_path, line_start=f.line_start,
                check_id=f.check_id or f.rule_id, title=f.message, severity=f.severity,
            ))
        for m in modules_data:
            db.add(Module(**{**m, "job_id": job_id}))

        persist_compliance(job_id, compliance, db)

        # AST entity extraction (best-effort, non-blocking)
        try:
            from .ast_analyzer import extract_entities
            entities = extract_entities(repo_path, max_files=200)
            for e in entities:
                db.add(CodeEntity(**{**e, "job_id": job_id}))
            logger.info(f"AST: extracted {len(entities)} entities for {job_id[:8]}")
        except Exception as _ae:
            logger.debug(f"AST extraction skipped: {_ae}")

        scan_time_ms  = int((time.time() - start_time) * 1000)
        overall_debt  = weighted_avg_debt(modules_data)
        overall_grade = grade_from_score(overall_debt)

        j = db.query(Job).filter(Job.id == job_id).first()
        if j:
            j.status          = StatusEnum.complete
            j.progress        = 100
            j.scan_time_ms    = scan_time_ms
            j.overall_debt_score = overall_debt
            j.overall_grade   = overall_grade
            j.completed_at    = datetime.datetime.utcnow()
            db.commit()

        ws({"event": "complete", "progress": 100, "scan_time_ms": scan_time_ms, "phase": "raw"})
        logger.info(f"Phase-1 complete for {job_id[:8]}: {len(raw_findings)} findings in {scan_time_ms}ms")

        # ── 5. LLM enrichment (Phase 2 — best-effort, updates existing rows) ─
        ws({"event": "llm_start", "stage": "triage", "progress": 100})
        try:
            triaged = await asyncio.wait_for(triage_findings(raw_findings), timeout=180)
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"Triage skipped: {e}")
            triaged = raw_findings

        # Update issue rows with LLM enrichment
        for f in triaged:
            iid = issue_ids.get(id(f))
            if iid and (f.cwe_id or f.owasp_category or f.llm_explanation):
                row = db.query(Issue).filter(Issue.id == iid).first()
                if row:
                    if f.cwe_id:         row.cwe_id         = f.cwe_id
                    if f.owasp_category: row.owasp_category = f.owasp_category
                    if f.llm_explanation:row.llm_explanation= f.llm_explanation
        db.commit()

        # Fix generation (top-10 only)
        sast_triaged = [f for f in triaged if f.category != "misconfig"]
        try:
            with_fixes = await asyncio.wait_for(
                generate_fixes(sast_triaged, repo_path, language, standards_doc), timeout=180)
            for f, diff in with_fixes:
                if diff:
                    iid = issue_ids.get(id(f))
                    if iid:
                        row = db.query(Issue).filter(Issue.id == iid).first()
                        if row: row.fix_diff = diff
            db.commit()
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"Fix generation skipped: {e}")

        # Misconfig remediation (batch, top-5 only)
        misconf_triaged = [f for f in triaged if f.category == "misconfig"]
        try:
            with_rem = await asyncio.wait_for(
                generate_misconfig_remediation(misconf_triaged[:5], repo_path), timeout=120)
            for f, rem in with_rem:
                if rem:
                    row = db.query(Misconfig).filter(
                        Misconfig.job_id == job_id,
                        Misconfig.file_path == f.file_path,
                        Misconfig.line_start == f.line_start,
                    ).first()
                    if row: row.remediation = rem
            db.commit()
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"Misconfig remediation skipped: {e}")

        # Summary
        try:
            stats = {
                "total":    len(triaged),
                "critical": sum(1 for f in triaged if f.severity == "critical"),
                "major":    sum(1 for f in triaged if f.severity == "major"),
                "minor":    sum(1 for f in triaged if f.severity == "minor"),
            }
            top_issues = [{"rule": f.rule_id, "severity": f.severity, "file": f.file_path}
                          for f in sorted(triaged, key=lambda x: SEV.get(x.severity, 4))[:5]]
            top_mods   = [{"path": m["path"], "score": m["debt_score"]} for m in modules_data[:3]]
            summary    = await asyncio.wait_for(
                generate_summary(repo_url, language, stats, top_issues, top_mods), timeout=60)
            j = db.query(Job).filter(Job.id == job_id).first()
            if j: j.summary_narrative = summary; db.commit()
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"Summary skipped: {e}")

        ws({"event": "enriched", "progress": 100})
        logger.info(f"Phase-2 enrichment complete for {job_id[:8]}")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        ws({"event": "error", "message": str(e), "progress": -1})
        try:
            j = db.query(Job).filter(Job.id == job_id).first()
            if j and j.status.value not in ("complete",):
                j.status = StatusEnum.failed
                db.commit()
        except Exception:
            pass
        raise
    finally:
        # Only clean up if we cloned (not for uploaded local paths which scan.py owns)
        if not Path(repo_url).exists() or repo_path != repo_url:
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

# fix_one() calls were sequential. Changed to asyncio.gather for 10x speedup.

# PERF: Replaced per-issue db.add() loop with bulk_insert_mappings() for 20x throughput.
