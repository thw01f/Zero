import shutil
import json
import asyncio
import subprocess
import datetime
import uuid
import logging
from typing import Optional
from .models import SelfHealthSnapshot
from .database import SessionLocal

logger = logging.getLogger(__name__)

SCANNERS = ["semgrep", "bandit", "ruff", "gitleaks", "trivy",
            "checkov", "hadolint", "tfsec", "lizard", "pip-audit", "osv-scanner"]


async def capture_snapshot() -> dict:
    versions: dict = {}
    for s in SCANNERS:
        if shutil.which(s):
            try:
                proc = await asyncio.create_subprocess_exec(
                    s, "--version",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=5)
                out = (stdout or stderr).decode(errors="replace").strip().split("\n")[0]
                versions[s] = out[:50]
            except Exception:
                versions[s] = "error"
        else:
            versions[s] = "missing"

    # Disk space
    disk = shutil.disk_usage("/tmp")
    disk_free_gb = round(disk.free / (1024 ** 3), 2)

    # Own CVE count
    own_cves = 0
    try:
        import sys, pathlib
        req = pathlib.Path(__file__).parent.parent / "requirements.txt"
        if req.exists():
            proc = await asyncio.create_subprocess_exec(
                "pip-audit", "-r", str(req), "--format", "json", "--progress-spinner", "off",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=30)
            data = json.loads(stdout)
            own_cves = sum(len(v.get("vulns", [])) for v in data.get("dependencies", []))
    except Exception:
        pass

    # Redis queue depth
    redis_depth = 0
    try:
        import redis as r
        from .config import settings
        rc = r.Redis.from_url(settings.redis_url)
        redis_depth = rc.llen("celery")
    except Exception:
        pass

    status = "healthy"
    if own_cves > 0:
        status = "degraded"
    if disk_free_gb < 1.0:
        status = "critical"

    snap = {
        "id": str(uuid.uuid4()),
        "captured_at": datetime.datetime.utcnow().isoformat(),
        "scanner_versions": versions,
        "own_cve_count": own_cves,
        "disk_free_gb": disk_free_gb,
        "redis_queue_depth": redis_depth,
        "last_advisory_poll": None,
        "celery_workers": 1,
        "status": status,
    }

    # Persist
    try:
        db = SessionLocal()
        db.add(SelfHealthSnapshot(**snap))
        db.commit()
        db.close()
    except Exception as e:
        logger.warning(f"Self-health persist failed: {e}")

    return snap
