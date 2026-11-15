"""Staging defense in depth; the private authenticated gateway is mandatory."""
import logging
import time
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger("uvicorn.error")


class StagingBoundaryMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, origins):
        super().__init__(app)
        self.origins = frozenset(origins)

    async def dispatch(self, request, call_next):
        started = time.monotonic()
        request_id = str(uuid4())
        if request.method not in {"GET", "HEAD", "OPTIONS"} and request.headers.get("origin") not in self.origins:
            response = JSONResponse(status_code=403, content={"error": {
                "code": "STAGING_ORIGIN_REQUIRED",
                "message": "Staging writes require the configured frontend origin.",
            }})
        else:
            response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        # No URLs, query strings, profiles, questions, credentials or record IDs.
        logger.info("staging_request id=%s method=%s status=%s duration_ms=%.1f",
                    request_id, request.method, response.status_code,
                    (time.monotonic() - started) * 1000)
        return response
