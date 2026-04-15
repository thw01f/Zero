
"""Add X-Response-Time header for performance monitoring."""
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers['X-Response-Time'] = f'{elapsed_ms:.1f}ms'
        return response
