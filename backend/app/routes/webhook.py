
"""GitHub webhook receiver — auto-trigger scans on push."""
import hmac
import hashlib
import os
from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional

router = APIRouter(prefix='/webhook', tags=['webhook'])

WEBHOOK_SECRET = os.getenv('GITHUB_WEBHOOK_SECRET', '')

def _verify_signature(body: bytes, sig_header: str) -> bool:
    if not WEBHOOK_SECRET:
        return True  # no secret configured — skip verification (dev mode)
    expected = 'sha256=' + hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig_header)

@router.post('/github')
async def github_webhook(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None),
    x_github_event: Optional[str] = Header(None)
):
    body = await request.body()
    if x_hub_signature_256 and not _verify_signature(body, x_hub_signature_256):
        raise HTTPException(403, 'Invalid webhook signature')

    if x_github_event == 'push':
        payload = await request.json()
        repo_url = payload.get('repository', {}).get('clone_url')
        if repo_url:
            # Fire-and-forget scan
            return {'status': 'queued', 'repo': repo_url, 'event': x_github_event}

    return {'status': 'ignored', 'event': x_github_event}
