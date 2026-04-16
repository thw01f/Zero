
"""Add X-Request-ID header to every response."""
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get('X-Request-ID', str(uuid.uuid4())[:8])
        response = await call_next(request)
        response.headers['X-Request-ID'] = req_id
        response.headers['X-Powered-By'] = 'DarkLead/1.0 (Claude Sonnet 4.6)'
        return response
