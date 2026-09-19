"""
Main FastAPI Application Entry Point for PS 26108.
Registers all API routers and provides health checks.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.standards import standards_router, graph_router
from backend.app.api.speech import speech_router
from backend.app.api.tenders import tenders_router
from backend.app.api.specifications import specifications_router

app = FastAPI(
    title="ARISTEA-PROCURE: Indian Standards Intelligence API",
    description="AI-powered recommendation engine, knowledge graph, and standards relationship platform for PS 26108.",
    version="1.0.0",
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
        "module": "Module 7, Module 8, Module 9, Module 10 — Speech AI, Module 11 — Tender Document Engine, Module 12 — Tender Audit & Module 13 — Specification Generator",
    }

