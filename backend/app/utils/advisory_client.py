
"""NVD / OSV advisory client for CVE lookups."""
import httpx
import os
from typing import Optional

NVD_BASE = 'https://services.nvd.nist.gov/rest/json/cves/2.0'
OSV_BASE = 'https://api.osv.dev/v1'

async def lookup_cve(cve_id: str) -> Optional[dict]:
    """Fetch CVE details from NVD."""
    api_key = os.getenv('NVD_API_KEY', '')
    headers = {'apiKey': api_key} if api_key else {}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f'{NVD_BASE}?cveId={cve_id}', headers=headers)
            if r.status_code == 200:
                data = r.json()
                vulns = data.get('vulnerabilities', [])
                if vulns:
                    cve = vulns[0].get('cve', {})
                    desc = cve.get('descriptions', [{}])[0].get('value', '')
                    metrics = cve.get('metrics', {})
                    cvss = None
                    for key in ('cvssMetricV31', 'cvssMetricV30', 'cvssMetricV2'):
                        if key in metrics and metrics[key]:
                            cvss = metrics[key][0].get('cvssData', {}).get('baseScore')
                            break
                    return {'cve_id': cve_id, 'description': desc, 'cvss_score': cvss}
    except Exception:
        pass
    return None

async def query_osv(package: str, version: str, ecosystem: str='PyPI') -> list:
    """Query OSV for known vulnerabilities in a package version."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(f'{OSV_BASE}/query',
                json={'version': version, 'package': {'name': package, 'ecosystem': ecosystem}})
            if r.status_code == 200:
                return r.json().get('vulns', [])
    except Exception:
        pass
    return []
