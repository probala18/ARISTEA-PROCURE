"""
FastAPI Router for Specification Generator API (Module 13).
Implements Section 67 & 69 Generation API specifications:
- POST /api/specifications/generate
- GET /api/specifications/{id}
- PUT /api/specifications/{id}
- DELETE /api/specifications/{id}
- POST /api/analysis/{analysis_id}/generate (Section 69)
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.services.specification_generator import (
    SpecificationService,
    SpecificationGenerationRequest,
    GeneratedSpecificationResponse,
    SpecificationUpdateRequest,
    SpecificationType,
)

router = APIRouter(tags=["Specification Generator API"])
specifications_router = router


@router.post("/specifications/generate", response_model=GeneratedSpecificationResponse)
def generate_specification(
    request: SpecificationGenerationRequest,
    db: Session = Depends(get_db),
):
    """
    Generates an evidence-grounded procurement specification:
    - technical_specification
    - tender_clause / corrective_clause
    - compliance_checklist
    - audit_correction
    Grounded strictly in verified BIS records and analyzed tender requirements.
    """
    service = SpecificationService(db)
    try:
        return service.generate_specification(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Specification generation failed: {str(e)}")


@router.get("/specifications/{id}", response_model=GeneratedSpecificationResponse)
def get_specification(
    id: int = Path(..., description="Unique Generated Specification ID"),
    db: Session = Depends(get_db),
):
    """Retrieves a previously generated procurement specification by ID."""
    service = SpecificationService(db)
    return service.get_specification(id)


@router.put("/specifications/{id}", response_model=GeneratedSpecificationResponse)
def update_specification(
    id: int = Path(..., description="Unique Generated Specification ID"),
    request: SpecificationUpdateRequest = Body(...),
    db: Session = Depends(get_db),
):
    """
    Updates or edits a generated specification without altering or corrupting
    underlying tender document evidence.
    """
    service = SpecificationService(db)
    return service.update_specification(id, request)


@router.delete("/specifications/{id}")
def delete_specification(
    id: int = Path(..., description="Unique Generated Specification ID"),
    db: Session = Depends(get_db),
):
    """Deletes a generated specification."""
    service = SpecificationService(db)
    service.delete_specification(id)
    return {"status": "success", "message": f"Specification {id} deleted successfully."}


@router.post("/analysis/{analysis_id}/generate", response_model=GeneratedSpecificationResponse)
def generate_from_analysis(
    analysis_id: str = Path(..., description="Analysis / Recommendation Session ID"),
    generation_type: SpecificationType = Query(SpecificationType.TECHNICAL_SPECIFICATION, description="Specification output type"),
    title: Optional[str] = Query(None, description="Optional specification title"),
    query_text: Optional[str] = Query(None, description="Optional requirement text if not cached"),
    db: Session = Depends(get_db),
):
    """
    Implements Section 69 Generation API:
    POST /api/analysis/{analysis_id}/generate
    Generates standards-aligned technical specs, clauses, or checklists from analysis session.
    """
    service = SpecificationService(db)
    req = SpecificationGenerationRequest(
        analysis_id=analysis_id,
        generation_type=generation_type,
        title=title,
        query_text=query_text or f"Analysis requirement for session {analysis_id}",
    )
    return service.generate_specification(req)
