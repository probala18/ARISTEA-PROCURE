"""
Main FastAPI Application Entry Point for PS 26108.
Registers all API routers and provides health checks.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import logging
from sqlalchemy import text

from backend.app.core.database import SessionLocal, get_db
from backend.app.api.standards import standards_router, graph_router
from backend.app.api.speech import speech_router
from backend.app.api.tenders import tenders_router
from backend.app.api.specifications import specifications_router
from backend.app.api.jobs import jobs_router
from backend.app.api.evaluations import evaluations_router
from backend.app.api.autopilot import autopilot_router
from backend.app.services.recommendation import RecommendationEngine, RecommendationRequest, RecommendationResponse
from backend.app.services.jobs import job_registry
from backend.app.core.config import settings

logger = logging.getLogger("aristea.api")
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))


@asynccontextmanager
async def app_lifespan(application: FastAPI):
    """Manage shared asynchronous resources for the API process."""
    try:
        from backend.app.core.database import Base, engine
        import backend.app.models
        Base.metadata.create_all(bind=engine)
    except Exception as exc:
        logger.warning("Could not auto-create database tables: %s", exc)
    yield
    job_registry.shutdown()

app = FastAPI(
    title="ARISTEA-PROCURE: Indian Standards Intelligence API",
    description="AI-powered recommendation engine, knowledge graph, and standards relationship platform for PS 26108.",
    version="1.0.0",
    lifespan=app_lifespan,
)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)

# Register routers under /api
app.include_router(standards_router, prefix="/api")
app.include_router(graph_router, prefix="/api")
app.include_router(speech_router, prefix="/api")
app.include_router(tenders_router, prefix="/api")
app.include_router(specifications_router, prefix="/api")
app.include_router(jobs_router, prefix="/api")
app.include_router(evaluations_router, prefix="/api")
app.include_router(autopilot_router, prefix="/api")


@app.post("/api/analyze", response_model=RecommendationResponse, tags=["Recommendation API"])
def analyze_requirement(payload: RecommendationRequest, db=Depends(get_db)):
    """Expose the existing recommendation engine for typed frontend queries."""
    return RecommendationEngine(db).recommend(payload)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    error_details = []
    for err in errors:
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        msg = err.get("msg", "Invalid value")
        error_details.append(f"{loc}: {msg}" if loc else msg)
    detailed_msg = "; ".join(error_details) if error_details else "Request validation failed."
    logger.warning("Request validation error on %s %s: %s", request.method, request.url.path, detailed_msg)
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "detail": "Request validation failed.",
            "message": detailed_msg,
            "fields": errors,
        },
    )


@app.exception_handler(Exception)
async def unexpected_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled API exception on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"error": "internal_server_error", "detail": "An unexpected error occurred."})


@app.get("/")
def root():
    return {
        "service": "ARISTEA-PROCURE",
        "description": "Indian Standards Procurement Intelligence Engine (PS 26108)",
        "version": "1.0.0",
        "docs_url": "/docs",
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "version": "1.0.0",
        "module": "Module 7, Module 8, Module 9, Module 10 — Speech AI, Module 11 — Tender Document Engine, Module 12 — Tender Audit, Module 13 — Specification Generator & Module 14 — FastAPI Integration",
        "modules": {
            "module13": "operational",
            "module14": "operational",
        },
        "async_jobs": {
            "status": "operational",
            "status_endpoint": "/api/jobs/{job_id}",
        },
    }


@app.get("/api/ready")
def readiness_check():
    """Reports whether the API can reach its configured database."""
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "database": "ready",
            "async_jobs": "available",
        }
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "database": "unavailable",
                "async_jobs": "available",
                "detail": str(exc),
            },
        )
    finally:
        db.close()
