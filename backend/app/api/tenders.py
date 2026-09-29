"""
FastAPI Router for Tender Document Processing API (Module 11).
Implements Section 67 API specifications:
- POST /api/tenders/upload
- GET /api/tenders/{id}
- GET /api/tenders/{id}/status
- GET /api/tenders/{id}/requirements
- GET /api/tenders/{id}/references
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Path
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.core.security import validate_upload
from backend.app.models.tender import TenderDocument, TenderSection, TenderRequirement, TenderStandardReference
from backend.app.services.tender_engine import (
    TenderEngineService,
    TenderProcessingStatus,
    TenderUploadResponse,
    TenderDetailResponse,
    TenderStatusResponse,
    TenderRequirementsResponse,
    TenderReferencesResponse,
    ExtractedStandardReference,
)
from backend.app.services.tender_audit import TenderAuditService, TenderAuditReport

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tenders", tags=["Tender Document API"])
tenders_router = router


@router.post("/upload", response_model=TenderUploadResponse)
async def upload_tender_document(
    file: UploadFile = File(..., description="Tender document file (PDF, DOCX, TXT)"),
    tender_number: Optional[str] = Form(None, description="Optional custom tender/bid reference number"),
    title: Optional[str] = Form(None, description="Optional tender title"),
    organization: Optional[str] = Form(None, description="Procuring organization / department name"),
    db: Session = Depends(get_db),
):
    """
    Uploads and parses a tender document.
    Extracts pages, sections, technical clauses, and explicit Indian Standard references.
    """
    content = await file.read()
    if not content or len(content) < 10:
        raise HTTPException(
            status_code=400,
            detail="Uploaded tender file is empty or corrupted."
        )

    # Validate file format
    fname = file.filename or "tender.txt"
    try:
        fname = validate_upload(
            fname,
            content,
            {"pdf", "docx", "txt"},
            settings.MAX_UPLOAD_BYTES,
            file.content_type,
            {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"},
        )
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Unsupported or invalid tender upload. Supported formats are PDF, DOCX, and TXT within the configured size limit."
        )

    service = TenderEngineService(db)
    try:
        tender_doc = service.process_document(
            file_content=content,
            filename=fname,
            tender_number=tender_number,
            title=title,
            organization=organization,
        )

        parsed_meta = tender_doc.parsed_metadata or {}
        return TenderUploadResponse(
            tender_id=tender_doc.id,
            tender_number=tender_doc.tender_number,
            filename=tender_doc.filename,
            file_type=tender_doc.file_type,
            file_size=tender_doc.file_size or len(content),
            status=TenderProcessingStatus(tender_doc.status),
            total_pages=parsed_meta.get("total_pages", 1),
            total_sections=parsed_meta.get("total_sections", len(tender_doc.sections)),
            total_clauses=len(tender_doc.requirements),
            total_standards_detected=parsed_meta.get("total_standards_detected", 0),
            extracted_text=tender_doc.raw_text,
            created_at=tender_doc.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as exc:
        logger.exception("Tender processing failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Tender document processing failed: {exc}")


@router.get("/{id}", response_model=TenderDetailResponse)
def get_tender_details(
    id: int = Path(..., description="Unique Tender Document ID"),
    db: Session = Depends(get_db),
):
    """Retrieves metadata and extracted section outline for a tender document."""
    service = TenderEngineService(db)
    tender = service.get_tender(id)
    if not tender:
        raise HTTPException(status_code=404, detail=f"Tender document ID {id} not found.")

    sections_data = []
    for s in tender.sections:
        sections_data.append({
            "id": s.id,
            "section_number": s.section_number,
            "section_title": s.section_title,
            "page_number": s.page_number,
            "section_type": s.section_type,
            "clause_count": len([r for r in tender.requirements if r.section_id == s.id]),
        })

    return TenderDetailResponse(
        id=tender.id,
        tender_number=tender.tender_number,
        filename=tender.filename,
        title=tender.title,
        organization=tender.organization,
        file_type=tender.file_type,
        file_size=tender.file_size,
        status=tender.status,
        created_at=tender.created_at,
        updated_at=tender.updated_at,
        total_sections=len(tender.sections),
        total_requirements=len(tender.requirements),
        total_standard_references=len(service.get_references(tender.id)),
        sections=sections_data,
    )


@router.get("/{id}/status", response_model=TenderStatusResponse)
def get_tender_status(
    id: int = Path(..., description="Unique Tender Document ID"),
    db: Session = Depends(get_db),
):
    """Checks processing status for background or asynchronous parsing."""
    service = TenderEngineService(db)
    tender = service.get_tender(id)
    if not tender:
        raise HTTPException(status_code=404, detail=f"Tender document ID {id} not found.")

    return TenderStatusResponse(
        tender_id=tender.id,
        filename=tender.filename,
        status=TenderProcessingStatus(tender.status),
        progress_percentage=100 if tender.status == "COMPLETED" else 0,
        message=f"Document parsing {tender.status.lower()}",
        updated_at=tender.updated_at or tender.created_at,
    )


@router.get("/{id}/requirements", response_model=TenderRequirementsResponse)
def get_tender_requirements(
    id: int = Path(..., description="Unique Tender Document ID"),
    db: Session = Depends(get_db),
):
    """Retrieves all extracted technical clauses and requirements from the tender."""
    service = TenderEngineService(db)
    tender = service.get_tender(id)
    if not tender:
        raise HTTPException(status_code=404, detail=f"Tender document ID {id} not found.")

    reqs = service.get_requirements(id)
    reqs_data = []
    for r in reqs:
        reqs_data.append({
            "id": r.id,
            "section_id": r.section_id,
            "requirement_text": r.requirement_text,
            "extracted_intent": r.extracted_intent,
            "product_keywords": r.product_keywords or [],
            "technical_attributes": r.technical_attributes or {},
            "is_mandatory": r.is_mandatory,
        })

    return TenderRequirementsResponse(
        tender_id=tender.id,
        total_requirements=len(reqs_data),
        requirements=reqs_data,
    )


@router.get("/{id}/references", response_model=TenderReferencesResponse)
def get_tender_standard_references(
    id: int = Path(..., description="Unique Tender Document ID"),
    db: Session = Depends(get_db),
):
    """Retrieves all explicit standard citations detected in the tender."""
    service = TenderEngineService(db)
    tender = service.get_tender(id)
    if not tender:
        raise HTTPException(status_code=404, detail=f"Tender document ID {id} not found.")

    refs = service.get_references(id)
    refs_data = []
    for ref in refs:
        refs_data.append(ExtractedStandardReference(
            standard_number_raw=ref.standard_number_raw,
            canonical_identifier=ref.standard_number_raw,
            detected_standard_id=ref.detected_standard_id,
            title=ref.detected_standard.title if ref.detected_standard else None,
            is_valid=ref.is_valid,
            is_superseded=ref.is_superseded,
            superseded_by_standard_id=ref.superseded_by_standard_id,
            superseded_by_identifier=ref.superseded_by_standard.standard_id if ref.superseded_by_standard else None,
            page_number=ref.section.page_number if ref.section else None,
            clause_number=None,
            detected_clause=ref.detected_clause,
        ))

    return TenderReferencesResponse(
        tender_id=tender.id,
        total_references=len(refs_data),
        references=refs_data,
    )


@router.get("/{id}/audit", response_model=TenderAuditReport)
def get_tender_audit(
    id: int = Path(..., description="Unique Tender Document ID"),
    force_recompute: bool = Query(False, description="Whether to recompute audit report if already cached"),
    db: Session = Depends(get_db),
):
    """
    Executes or retrieves comprehensive evidence-grounded tender audit (Module 12):
    - Expected vs present standards
    - Missing primary standard references
    - Outdated/superseded citations with successor links
    - Potential allied testing & safety standard gaps
    - Mandatory certification / QCO gaps
    - Ambiguity detection
    - Calibrated standards coverage score
    """
    from backend.app.services.tender_audit import TenderAuditService, TenderAuditReport

    service = TenderAuditService(db)
    try:
        report = service.audit_tender(id, force_recompute=force_recompute)
        return report
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Tender audit execution failed for tender %s: %s", id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Tender audit execution failed: {str(e)}")


@router.post("/{id}/generate")
def generate_tender_specification(
    id: int = Path(..., description="Unique Tender Document ID"),
    generation_type: str = Query("technical_specification", description="Type: technical_specification, tender_clause, compliance_checklist, audit_correction"),
    title: Optional[str] = Query(None, description="Optional custom title"),
    db: Session = Depends(get_db),
):
    """
    Generates a standards-aligned specification, corrective clause, or compliance checklist
    derived from tender analysis and audit findings (Module 13).
    """
    from backend.app.services.specification_generator import (
        SpecificationService,
        SpecificationGenerationRequest,
        SpecificationType,
    )
    service = SpecificationService(db)
    try:
        g_type = SpecificationType(generation_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid generation_type '{generation_type}'. Supported: technical_specification, tender_clause, compliance_checklist, audit_correction."
        )

    req = SpecificationGenerationRequest(
        tender_id=id,
        generation_type=g_type,
        title=title,
    )
    return service.generate_specification(req)


@router.get("/{id}/specifications")
def list_tender_specifications(
    id: int = Path(..., description="Unique Tender Document ID"),
    db: Session = Depends(get_db),
):
    """Lists all specifications generated for a tender."""
    from backend.app.services.specification_generator import SpecificationService
    service = SpecificationService(db)
    return service.list_specifications_for_tender(id)
