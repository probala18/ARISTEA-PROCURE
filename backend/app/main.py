"""
Main FastAPI Application Entry Point for PS 26108.
Registers all API routers and provides health checks.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from backend.app.core.database import SessionLocal
from backend.app.api.standards import standards_router, graph_router
from backend.app.api.speech import speech_router
from backend.app.api.tenders import tenders_router
from backend.app.api.specifications import specifications_router
from backend.app.api.jobs import jobs_router
from backend.app.services.jobs import job_registry


@asynccontextmanager
async def app_lifespan(application: FastAPI):
    """Manage shared asynchronous resources for the API process."""
    yield
    job_registry.shutdown()

app = FastAPI(
    title="ARISTEA-PROCURE: Indian Standards Intelligence API",
    description="AI-powered recommendation engine, knowledge graph, and standards relationship platform for PS 26108.",
    version="1.0.0",
    lifespan=app_lifespan,
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers under /api
app.include_router(standards_router, prefix="/api")
app.include_router(graph_router, prefix="/api")
app.include_router(speech_router, prefix="/api")
app.include_router(tenders_router, prefix="/api")
app.include_router(specifications_router, prefix="/api")
app.include_router(jobs_router, prefix="/api")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "detail": "Request validation failed.",
            "fields": exc.errors(),
        },
    )


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
