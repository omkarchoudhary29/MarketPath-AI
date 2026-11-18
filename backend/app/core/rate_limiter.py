import os
import time
from collections import defaultdict
from typing import Dict, List, Tuple
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from backend.app.core.config import settings

# Store IP -> list of request timestamps (epoch floats)
_IP_REQUEST_LOGS: Dict[str, List[float]] = defaultdict(list)
_CLEANUP_INTERVAL = 300.0  # Clean memory every 5 minutes
_LAST_CLEANUP = time.time()

# Rate limit thresholds: (max_requests, window_seconds)
STANDARD_LIMIT: Tuple[int, int] = (150, 60)  # 150 req/min
SENSITIVE_LIMIT: Tuple[int, int] = (30, 60)   # 30 req/min for auth, ai, billing

SENSITIVE_PATH_PREFIXES = (
    "/api/v1/ai-studio/generate",
    "/api/v1/auth/login",
    "/api/v1/auth/signup",
    "/api/v1/billing/checkout",
    "/api/v1/billing/verify",
    "/api/v1/webhooks",
)

EXEMPT_PATHS = (
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
)


def _cleanup_expired(now: float) -> None:
    """Removes timestamps older than 60 seconds to prevent memory unbounded growth."""
    global _LAST_CLEANUP
    if now - _LAST_CLEANUP < _CLEANUP_INTERVAL:
        return
    _LAST_CLEANUP = now
    cutoff = now - 60.0
    stale_ips = []
    for ip, timestamps in _IP_REQUEST_LOGS.items():
        _IP_REQUEST_LOGS[ip] = [t for t in timestamps if t > cutoff]
        if not _IP_REQUEST_LOGS[ip]:
            stale_ips.append(ip)
    for ip in stale_ips:
        _IP_REQUEST_LOGS.pop(ip, None)


async def rate_limiting_middleware(request: Request, call_next) -> Response:
    """Sliding-window IP rate limiter defending against brute-force and request flooding."""
    # Automated test bypass
    if (
        os.getenv("PYTEST_CURRENT_TEST")
        or settings.APP_ENV == "testing"
        or os.getenv("APP_ENV") == "testing"
    ):
        return await call_next(request)

    path = request.url.path

    # Check for exemptions
    if path in EXEMPT_PATHS or request.headers.get("X-Test-Bypass-Rate-Limit") == "true":
        return await call_next(request)

    # Determine client IP (handles X-Forwarded-For if behind reverse proxy)
    client_ip = (
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or (request.client.host if request.client else "127.0.0.1")
    )

    now = time.time()
    _cleanup_expired(now)

    # Select threshold based on route sensitivity
    is_sensitive = any(path.startswith(prefix) for prefix in SENSITIVE_PATH_PREFIXES)
    max_reqs, window_sec = SENSITIVE_LIMIT if is_sensitive else STANDARD_LIMIT

    # Filter timestamps within active window
    window_start = now - window_sec
    user_timestamps = [t for t in _IP_REQUEST_LOGS[client_ip] if t > window_start]
    _IP_REQUEST_LOGS[client_ip] = user_timestamps

    if len(user_timestamps) >= max_reqs:
        retry_after = int(window_sec - (now - user_timestamps[0])) + 1
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": f"Too many requests. Limit is {max_reqs} requests per {window_sec}s for this endpoint.",
                    "details": [{"field": "rate_limit", "issue": f"Retry after {retry_after} seconds"}],
                    "request_id": getattr(request.state, "request_id", "unknown"),
                }
            },
            headers={"Retry-After": str(max(retry_after, 1))},
        )

    # Record this request
    _IP_REQUEST_LOGS[client_ip].append(now)
    response = await call_next(request)
    return response
