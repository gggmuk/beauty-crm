"""
BeautyCRM — Middleware
CORS, Tenant context, and basic Rate Limiting.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class MultiTenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware that inspects incoming requests and adds tenant headers
    or context if present.
    """

    async def dispatch(self, request: Request, call_next):
        tenant_id = request.headers.get("X-Tenant-ID")
        if tenant_id:
            request.state.tenant_id = tenant_id

        response = await call_next(request)
        return response
