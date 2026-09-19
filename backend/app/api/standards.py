"""
FastAPI Router for Standards & Knowledge Graph API (Module 7).
Implements Section 66 API specifications:
- GET /api/standards/{standard_id}
- GET /api/standards/{standard_id}/relationships
- GET /api/standards/{standard_id}/allied
- GET /api/standards/{standard_id}/graph
- GET /api/standards/{standard_id}/supersession
- GET /api/standards/{standard_id}/compliance
- GET /api/graph/path
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.standard import Standard
from backend.app.services.knowledge_graph.graph_models import ComplianceLinksResult
from backend.app.services.relationship_engine.engine import RelationshipEngine
from backend.app.services.relationship_engine.schemas import (
    RelationshipEdgePayload,
    AlliedStandardsGroup,
    DependencyGraphResponse,
    ShortestPathResponse,
    SupersessionLineageResponse,
)
from backend.app.services.version_intelligence import (
    VersionIntelligenceService,
    VersionIntelligenceReport,
    AmendmentRecord,
    CurrencyCheckResult,
)
from backend.app.services.compliance_intelligence import (
    ComplianceIntelligenceService,
    StandardCertificationReport,
    ComplianceIntelligenceReport,
    BatchComplianceRequest,
    BatchComplianceResult,
)

router = APIRouter(tags=["Standards & Graph API"])
standards_router = router


@router.get("/standards/{standard_id}/relationships", response_model=List[RelationshipEdgePayload])
def get_standard_relationships(
    standard_id: str = Path(..., description="Canonical standard ID (e.g. 'IS 12615:2018', 'IS 694') or integer DB ID"),
    relationship_types: Optional[List[str]] = Query(None, description="Filter by Module 4 normalized relation types (e.g. TESTING, SAFETY)"),
    is_explicit: Optional[bool] = Query(None, description="Filter by explicit source (True = relationships.json, False = derived)"),
    db: Session = Depends(get_db),
):
    """Retrieves direct relationship edges connected to the standard with provenance."""
    engine = RelationshipEngine(db)
    std = engine.resolve_standard(standard_id)
    if not std:
        raise HTTPException(status_code=404, detail=f"Standard '{standard_id}' not found in database.")

    return engine.get_relationships(
        standard_id_or_number=std.id,
        relationship_types=relationship_types,
        is_explicit=is_explicit,
    )


@router.get("/standards/{standard_id}/allied", response_model=AlliedStandardsGroup)
def get_standard_allied_grouping(
    standard_id: str = Path(..., description="Canonical standard ID or integer DB ID"),
    db: Session = Depends(get_db),
):
    """
    Returns system-generated allied groupings (normative, testing, safety, performance, installation).
    Explicitly disclaims official BIS designation.
    """
    engine = RelationshipEngine(db)
    allied = engine.get_allied_standards(standard_id)
    if not allied:
        raise HTTPException(status_code=404, detail=f"Standard '{standard_id}' not found in database.")
    return allied


@router.get("/standards/{standard_id}/graph", response_model=DependencyGraphResponse)
def get_standard_dependency_graph(
    standard_id: str = Path(..., description="Canonical standard ID or integer DB ID"),
    max_depth: int = Query(3, ge=1, le=5, description="Traversal depth limit (default 3, clamped to max 5)"),
    direction: str = Query("both", pattern="^(outgoing|incoming|both)$", description="Edge direction traversal"),
    db: Session = Depends(get_db),
):
    """Returns multi-hop, cycle-safe dependency graph with depth enforcement."""
    engine = RelationshipEngine(db)
    graph = engine.build_dependency_graph(standard_id, max_depth=max_depth, direction=direction)
    if not graph:
        raise HTTPException(status_code=404, detail=f"Standard '{standard_id}' not found in database.")
    return graph


@router.get("/standards/{standard_id}/supersession", response_model=SupersessionLineageResponse)
def get_standard_supersession(
    standard_id: str = Path(..., description="Canonical standard ID or integer DB ID"),
    db: Session = Depends(get_db),
):
    """Returns loop-free forward (successor) and backward (predecessor) supersession lineage."""
    engine = RelationshipEngine(db)
    lineage = engine.get_supersession_lineage(standard_id)
    if not lineage:
        raise HTTPException(status_code=404, detail=f"Standard '{standard_id}' not found in database.")
    return lineage


@router.get("/standards/{standard_id}/compliance", response_model=ComplianceIntelligenceReport)
def get_standard_compliance(
    standard_id: str = Path(..., description="Canonical standard ID or integer DB ID"),
    db: Session = Depends(get_db),
):
    """
    Returns comprehensive grounded compliance intelligence report:
    - Requirement level (MANDATORY, VOLUNTARY, CONDITIONAL, UNKNOWN)
    - Governing scheme (BIS_ISI, CRS, HALLMARKING, etc.)
    - Grounded certification records and QCO orders
    - Scope-aware regulatory divergence detection
    - Backward-compatible with Module 7 response schema
    """
    svc = ComplianceIntelligenceService(db)
    report = svc.evaluate_compliance(standard_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Standard '{standard_id}' not found in database.")
    return report


@router.get("/standards/{standard_id}/certification", response_model=StandardCertificationReport)
def get_standard_certification(
    standard_id: str = Path(..., description="Canonical standard ID (e.g. 'IS 12615:2018', 'IS 694') or integer DB ID"),
    db: Session = Depends(get_db),
):
    """
    Returns Section 66 specification report: grounded certification records, QCO mandates, and governing scheme.
    """
    svc = ComplianceIntelligenceService(db)
    report = svc.get_certification_report(standard_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Standard '{standard_id}' not found in database.")
    return report


@router.post("/standards/compliance/batch", response_model=BatchComplianceResult)
def batch_evaluate_compliance(
    payload: BatchComplianceRequest,
    db: Session = Depends(get_db),
):
    """
    Performs bounded bulk compliance evaluations across multiple standards without N+1 queries.
    """
    svc = ComplianceIntelligenceService(db)
    return svc.batch_evaluate_compliance(payload.identifiers)


@router.get("/standards/{standard_id}")
def get_standard_detail(
    standard_id: str = Path(..., description="Canonical standard ID or integer DB ID"),
    db: Session = Depends(get_db),
):
    """Returns canonical metadata for a single standard."""
    engine = RelationshipEngine(db)
    std = engine.resolve_standard(standard_id)
    if not std:
        raise HTTPException(status_code=404, detail=f"Standard '{standard_id}' not found in database.")
    return {
        "id": std.id,
        "standard_id": std.standard_id,
        "is_number": std.is_number,
        "title": std.title,
        "status": std.status,
        "category": std.category,
        "subject_area": std.subject_area,
        "publication_year": std.publication_year,
        "source_file": std.source_file,
    }


@router.get("/standards/{standard_id}/versions", response_model=VersionIntelligenceReport)
def get_standard_versions(
    standard_id: str = Path(..., description="Canonical standard ID (e.g. 'IS 12615:2018', 'IS 12615') or integer DB ID"),
    db: Session = Depends(get_db),
):
    """
    Returns consolidated version intelligence report for a standard:
    - Version records from StandardVersion table
    - Amendment records with provenance
    - Supersession lineage from Module 4 SupersessionChainService
    - Dataset-backed currency check and evidence-grounded warnings
    """
    svc = VersionIntelligenceService(db)
    report = svc.get_version_report(standard_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Standard '{standard_id}' not found in database.")
    return report


@router.get("/standards/{standard_id}/amendments", response_model=List[AmendmentRecord])
def get_standard_amendments(
    standard_id: str = Path(..., description="Canonical standard ID (e.g. 'IS 12615:2018', 'IS 12615') or integer DB ID"),
    db: Session = Depends(get_db),
):
    """
    Returns amendment-specific records with source dataset provenance.
    Grounded in StandardVersion table where amendment_number or amendment_year is set.
    """
    svc = VersionIntelligenceService(db)
    std = svc.resolve_standard(standard_id)
    if not std:
        raise HTTPException(status_code=404, detail=f"Standard '{standard_id}' not found in database.")
    return svc.get_amendments(std.id)


@router.get("/standards/{standard_id}/currency", response_model=CurrencyCheckResult)
def get_standard_currency(
    standard_id: str = Path(..., description="Canonical standard ID (e.g. 'IS 12615:2018', 'IS 12615') or integer DB ID"),
    db: Session = Depends(get_db),
):
    """
    Performs dataset-backed version and currency check for a standard.
    Primary status signal is Standard.status (CURRENT vs SUPERSEDED).
    Disclaims independent legal or regulatory currency determination.
    """
    svc = VersionIntelligenceService(db)
    result = svc.check_currency(standard_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Standard '{standard_id}' not found in database.")
    return result


# Path query router for /api/graph/path
graph_router = APIRouter(prefix="/graph", tags=["Graph Traversal & Paths"])


@graph_router.get("/path", response_model=ShortestPathResponse)
def get_shortest_path_between_standards(
    source: str = Query(..., description="Source standard identifier (e.g. 'IS 12615' or integer ID)"),
    target: str = Query(..., description="Target standard identifier (e.g. 'IS 900' or integer ID)"),
    max_depth: int = Query(3, ge=1, le=5, description="Maximum traversal depth (default: 3, max: 5)"),
    db: Session = Depends(get_db),
):
    """
    Computes shortest graph path between two standards based strictly on actual graph connectivity.
    Never invents paths based on title similarity or embeddings.
    """
    engine = RelationshipEngine(db)
    return engine.find_shortest_path(source_id_or_num=source, target_id_or_num=target, max_depth=max_depth)
