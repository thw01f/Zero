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