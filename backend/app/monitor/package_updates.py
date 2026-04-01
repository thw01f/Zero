import httpx
import asyncio
import logging
import re
from packaging.version import Version, InvalidVersion
from typing import Optional

logger = logging.getLogger(__name__)


async def get_latest_pypi(package: str) -> Optional[str]:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"https://pypi.org/pypi/{package}/json")
            if r.status_code == 200:
                return r.json()["info"]["version"]
    except Exception:
        pass
    return None


async def get_latest_npm(package: str) -> Optional[str]:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"https://registry.npmjs.org/{package}/latest")
            if r.status_code == 200:
                return r.json().get("version")
    except Exception:
        pass
    return None


def classify_update(
    current: str,
    latest: str,
    cve_ids: list,
    cvss_max: Optional[float],
    changelog: str = "",
) -> str:
    if cve_ids and (cvss_max or 0) >= 7.0:
        return "MANDATORY"
    sec_pattern = r"(rce|remote code|sql injection|auth bypass|hardcoded|privilege escalation|critical)"
    if re.search(sec_pattern, changelog, re.IGNORECASE):
        return "MANDATORY"
    if cve_ids:
        return "SUGGESTED"
    try:
        cur, lat = Version(current), Version(latest)
        if lat.major > cur.major:
            return "INFORMATIONAL"
        if lat.minor > cur.minor or lat.micro > cur.micro:
            return "OPTIONAL"
    except InvalidVersion:
        pass
    return "INFORMATIONAL"
