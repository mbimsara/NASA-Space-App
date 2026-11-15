"""Shared reviewer staging access only; not user identity or record ownership."""
from hmac import compare_digest

from starlette.responses import JSONResponse


class HostedAccessMiddleware:
    def __init__(self, app, token):
        self.app = app
        self.expected = ("Bearer " + token).encode("utf-8")

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Render's public probe must disclose no records or dependencies.
            public_probe = scope["path"] == "/api/v1/health" and scope["method"] in {"GET", "HEAD"}
            headers = dict(scope["headers"])
            if not public_probe and not compare_digest(headers.get(b"authorization", b""), self.expected):
                response = JSONResponse(status_code=401, content={"error": {
                    "code": "UNAUTHORIZED", "message": "Restricted staging access is required.",
                }}, headers={"Cache-Control": "no-store", "WWW-Authenticate": "Bearer"})
                await response(scope, receive, send)
                return
        await self.app(scope, receive, send)
