"""
FastAPI Router for the three differentiating features:
1. Redline Document Editor — Visual compliance annotation
2. Adversarial Auditor AI — Hallucination detection & double-check
3. Vision AI Table Reader — Engineering table/chart extraction
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import base64
import logging

from backend.app.core.database import get_db
from backend.app.services.redline import RedlineService, RedlineAnalysisRequest, RedlineAnalysisResponse
from backend.app.services.redline.schemas import AutoFixAction
from backend.app.services.adversarial_auditor import (
    AdversarialAuditorService,
    AuditVerificationRequest,
    AuditVerificationResponse,
)
from backend.app.services.vision_table import (
    VisionTableService,
    VisionTableRequest,
    VisionTableResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Advanced Features"])
advanced_router = router


# ============================================================
# 1. REDLINE DOCUMENT EDITOR
# ============================================================

@router.post(
    "/redline/analyze",
    response_model=RedlineAnalysisResponse,
    summary="Redline Document Analysis",
    description=(
        "Analyzes tender document text and returns annotated segments with "
        "inline compliance markers: GREEN (current), RED (outdated with auto-fix), "
        "ORANGE (unrecognized), YELLOW (has amendments)."
    ),
)
def analyze_redline(
    request: RedlineAnalysisRequest,
    db: Session = Depends(get_db),
):
    """Visual redline analysis of tender documents with auto-fix suggestions."""
    service = RedlineService(db)
    try:
        return service.analyze(request)
    except Exception as e:
        logger.error("Redline analysis failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Redline analysis failed: {e}")


@router.post(
    "/redline/apply-fix",
    summary="Apply Single Auto-Fix",
    description="Applies a single auto-fix to the document text, replacing an outdated standard with its successor.",
)
def apply_redline_fix(
    document_text: str = Form(..., description="The current document text"),
    fix_id: str = Form(..., description="The fix_id to apply"),
    old_text: str = Form(..., description="The old text to replace"),
    new_text: str = Form(..., description="The new replacement text"),
    db: Session = Depends(get_db),
):
    """Apply a single auto-fix to correct an outdated standard reference."""
    corrected = document_text.replace(old_text, new_text, 1)
    return {
        "corrected_text": corrected,
        "fix_applied": fix_id,
        "old_text": old_text,
        "new_text": new_text,
    }


@router.post(
    "/redline/apply-all-fixes",
    summary="Apply All Auto-Fixes",
    description="Applies all available auto-fixes to the document text at once.",
)
def apply_all_redline_fixes(
    request: RedlineAnalysisRequest,
    db: Session = Depends(get_db),
):
    """Auto-correct all outdated standard references in the document."""
    request.auto_fix_all = True
    service = RedlineService(db)
    try:
        result = service.analyze(request)
        return {
            "corrected_text": result.corrected_text,
            "fixes_applied": len(result.auto_fixes),
            "auto_fixes": result.auto_fixes,
            "summary": result.summary,
        }
    except Exception as e:
        logger.error("Redline auto-fix failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Redline auto-fix failed: {e}")


# ============================================================
# 2. ADVERSARIAL AUDITOR AI
# ============================================================

@router.post(
    "/auditor/verify",
    response_model=AuditVerificationResponse,
    summary="Adversarial AI Verification",
    description=(
        "A second 'Auditor AI' that aggressively double-checks standard references "
        "against the verified BIS database. Catches hallucinated/fabricated standard "
        "numbers and blocks suspicious references."
    ),
)
def verify_standards(
    request: AuditVerificationRequest,
    db: Session = Depends(get_db),
):
    """Double-check standard references for hallucination detection."""
    service = AdversarialAuditorService(db)
    try:
        return service.verify(request)
    except Exception as e:
        logger.error("Adversarial audit failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Adversarial audit failed: {e}")


@router.post(
    "/auditor/verify-text",
    response_model=AuditVerificationResponse,
    summary="Verify Standards in Free Text",
    description=(
        "Extracts all standard references from free text and runs adversarial "
        "verification on each one."
    ),
)
def verify_standards_in_text(
    text: str = Form(..., description="Free text containing standard references"),
    strict_mode: bool = Form(True, description="Block unverified references"),
    db: Session = Depends(get_db),
):
    """Extract and verify all standard references from free text."""
    from backend.app.services.tender_engine.standard_extractor import StandardExtractor

    extractor = StandardExtractor(db)
    mentions = extractor.find_standard_mentions(text)
    references = [norm for _, norm, _, _ in mentions]

    if not references:
        return AuditVerificationResponse(
            total_checked=0,
            results=[],
            overall_trust_score=1.0,
            auditor_warning="No standard references detected in the provided text.",
        )

    request = AuditVerificationRequest(
        references=references,
        strict_mode=strict_mode,
        include_closest_matches=True,
    )
    service = AdversarialAuditorService(db)
    return service.verify(request)


# ============================================================
# 3. VISION AI TABLE READER
# ============================================================

@router.post(
    "/vision/extract-table",
    response_model=VisionTableResponse,
    summary="Vision AI Table Extraction",
    description=(
        "Extracts structured data from images of engineering tables, "
        "mathematical formulas, and charts from Indian Standard documents."
    ),
)
async def extract_table_from_image(
    file: UploadFile = File(..., description="Image of a table/chart (PNG, JPG, WEBP)"),
    extraction_mode: str = Form("auto", description="Mode: auto, table, formula, chart, mixed"),
    enhance_ocr: bool = Form(True, description="Apply image enhancement"),
    detect_standards: bool = Form(True, description="Detect IS references in content"),
):
    """Upload a table/chart image for structured data extraction."""
    content = await file.read()
    if not content or len(content) < 100:
        raise HTTPException(status_code=400, detail="Image file is empty or too small.")

    # Determine format
    fname = (file.filename or "image.png").lower()
    if fname.endswith(".jpg") or fname.endswith(".jpeg"):
        fmt = "jpeg"
    elif fname.endswith(".webp"):
        fmt = "webp"
    else:
        fmt = "png"

    # Encode to base64
    image_b64 = base64.b64encode(content).decode("utf-8")

    service = VisionTableService()
    request = VisionTableRequest(
        image_base64=image_b64,
        image_format=fmt,
        extraction_mode=extraction_mode,
        enhance_ocr=enhance_ocr,
        detect_standards=detect_standards,
    )

    try:
        return service.extract(request)
    except Exception as e:
        logger.error("Vision extraction failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Vision extraction failed: {e}")


@router.post(
    "/vision/extract-from-text",
    response_model=VisionTableResponse,
    summary="Extract Tables from Pre-OCR'd Text",
    description=(
        "Parses table structures from pre-extracted text (when image OCR "
        "has already been done externally or for pasted text content)."
    ),
)
def extract_table_from_text(
    text: str = Form(..., description="Text content potentially containing tables"),
    detect_standards: bool = Form(True, description="Detect IS references"),
):
    """Extract table structures from raw text content."""
    service = VisionTableService()
    try:
        return service.extract_from_text(text, detect_standards=detect_standards)
    except Exception as e:
        logger.error("Text table extraction failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Text table extraction failed: {e}")
