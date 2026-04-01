import httpx
import logging
from typing import List

logger = logging.getLogger(__name__)
OSV_BASE = "https://api.osv.dev/v1"


async def query_package(name: str, ecosystem: str, version: str = None) -> List[dict]:
    payload: dict = {"package": {"name": name, "ecosystem": ecosystem}}
    if version:
        payload["version"] = version
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(f"{OSV_BASE}/query", json=payload)
            if r.status_code == 200:
                return r.json().get("vulns", [])
    except Exception as e:
        logger.warning(f"OSV query failed for {name}: {e}")
    return []


async def batch_query(packages: list) -> dict:
    """packages = [{"name": ..., "ecosystem": ..., "version": ...}]"""
    payload = {"queries": [
        {"package": {"name": p["name"], "ecosystem": p["ecosystem"]},
         "version": p.get("version", "")}
        for p in packages
    ]}
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(f"{OSV_BASE}/querybatch", json=payload)
            if r.status_code == 200:
                results = r.json().get("results", [])
                return {packages[i]["name"]: r.get("vulns", []) for i, r in enumerate(results)}
    except Exception as e:
        logger.warning(f"OSV batch query failed: {e}")
    return {}
