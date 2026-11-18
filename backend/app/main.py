from contextlib import asynccontextmanager
import uuid
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.v1.router import api_router
from backend.app.core.config import settings
from backend.app.core.database import AsyncSessionLocal
from backend.app.core.exceptions import MarketPathException
from backend.app.services.billing_service import BillingService


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Seed default SaaS plans if database is unseeded
    try:
        async with AsyncSessionLocal() as session:
            await BillingService.seed_default_plans(session)
    except Exception as e:
        print(f"Data initialization notice: {e}")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for MarketPath AI — D2C Commerce & Growth Operating Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Configuration
origins = list(set([settings.FRONTEND_URL] + settings.ALLOWED_ORIGINS))
allow_origin_regex = (
    r"https?://(localhost|127\.0\.0\.1|.*\.up\.railway\.app|.*\.railway\.app)(:\d+)?"
    if settings.APP_ENV != "production"
    else None
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-Id"],
)

from backend.app.core.rate_limiter import rate_limiting_middleware

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Enforces defense-in-depth HTTP security response headers."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    if request.url.scheme == "https" or settings.APP_ENV == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.middleware("http")
async def apply_rate_limiting(request: Request, call_next):
    return await rate_limiting_middleware(request, call_next)


@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id") or f"req_{uuid.uuid4().hex[:12]}"
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    return response


# Global Exception Handlers conforming to API contracts defined in README.md
@app.exception_handler(MarketPathException)
async def marketpath_exception_handler(request: Request, exc: MarketPathException):
    req_id = getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:12]}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "request_id": req_id,
            }
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    req_id = getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:12]}")
    code_map = {
        status.HTTP_401_UNAUTHORIZED: "UNAUTHORIZED",
        status.HTTP_403_FORBIDDEN: "FORBIDDEN",
        status.HTTP_404_NOT_FOUND: "NOT_FOUND",
        status.HTTP_400_BAD_REQUEST: "BAD_REQUEST",
        status.HTTP_409_CONFLICT: "CONFLICT",
    }
    code = code_map.get(exc.status_code, "ERROR")
    msg = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": code,
                "message": msg,
                "details": [],
                "request_id": req_id,
            },
            "detail": msg,
        },
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    req_id = getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:12]}")
    details = []
    issues = []
    for err in exc.errors():
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        msg = err.get("msg", "Invalid value")
        details.append({"field": loc, "issue": msg})
        issues.append(f"{loc}: {msg}")
    first_issue = issues[0] if issues else "The request payload failed schema validation."
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_FAILED",
                "message": first_issue,
                "details": details,
                "request_id": req_id,
            },
            "detail": first_issue,
        },
    )


# Mount versioned API routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# Root health alias
@app.get("/health", tags=["Health"])
async def root_health():
    return {"status": "healthy", "service": "MarketPath AI API"}


# Production Single-Service Frontend Serving (React / Vite SPA)
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

_candidates = [
    Path(__file__).resolve().parent.parent.parent / "frontend" / "dist",
    Path("/app/frontend/dist"),
    Path("./frontend/dist"),
]
FRONTEND_DIST = next((p for p in _candidates if p.exists() and (p / "index.html").exists()), None)

if FRONTEND_DIST:
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa_frontend(request: Request, full_path: str):
        if (
            full_path.startswith("api/")
            or full_path == "api"
            or full_path == "health"
            or full_path.startswith("docs")
            or full_path.startswith("redoc")
            or full_path.startswith("openapi.json")
        ):
            raise HTTPException(status_code=404, detail="API endpoint not found")

        file_path = FRONTEND_DIST / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")

