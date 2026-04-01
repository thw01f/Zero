import httpx
import datetime
import logging
from typing import List

logger = logging.getLogger(__name__)
NVD_BASE = "https://services.nvd.nist.gov/rest/json/cves/2.0"


async def fetch_recent_cves(hours: int = 6, api_key: str = None) -> List[dict]:
    now = datetime.datetime.utcnow()
    start = now - datetime.timedelta(hours=hours)
    params = {
        "pubStartDate": start.strftime("%Y-%m-%dT%H:%M:%S.000"),
        "pubEndDate": now.strftime("%Y-%m-%dT%H:%M:%S.000"),
        "resultsPerPage": 100,
    }
    headers = {}
    if api_key:
        headers["apiKey"] = api_key

    try:
        async with httpx.AsyncClient(timeout=30, headers=headers) as client:
            r = await client.get(NVD_BASE, params=params)
            r.raise_for_status()
            return r.json().get("vulnerabilities", [])
    except Exception as e:
        logger.warning(f"NVD fetch failed: {e}")
        return []
