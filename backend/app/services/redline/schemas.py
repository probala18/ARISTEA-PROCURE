"""
Pydantic schemas for the Redline Document Analysis service.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class AnnotationType(str, Enum):
    """Inline annotation type for redline markup."""
    COMPLIANT = "COMPLIANT"          # Green — current, valid standard
    OUTDATED = "OUTDATED"            # Red — superseded/expired standard
    UNRECOGNIZED = "UNRECOGNIZED"    # Orange — standard not found in BIS dataset
    AMENDED = "AMENDED"              # Yellow — current but has amendments
    PLAIN = "PLAIN"                  # No annotation — regular text


class AutoFixAction(BaseModel):
    """Describes an auto-fix that can be applied to correct an outdated reference."""
    fix_id: str = Field(..., description="Unique ID for this fix action")
    old_text: str = Field(..., description="The original text segment to replace")
    new_text: str = Field(..., description="The corrected replacement text")
    old_standard_id: str = Field(..., description="The outdated standard identifier")
    new_standard_id: str = Field(..., description="The current/successor standard identifier")
    new_standard_title: Optional[str] = Field(None, description="Title of the successor standard")
    reason: str = Field(..., description="Human-readable explanation for the fix")
    year_old: Optional[int] = Field(None, description="Publication year of the old standard")
    year_new: Optional[int] = Field(None, description="Publication year of the new standard")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Confidence in this auto-fix")


class RedlineSegment(BaseModel):
    """A single annotated segment of the document."""
    segment_id: int = Field(..., description="Sequential segment index")
    text: str = Field(..., description="The text content of this segment")
    annotation_type: AnnotationType = Field(..., description="Annotation classification")
    standard_id: Optional[str] = Field(None, description="Detected standard reference, if any")
    standard_title: Optional[str] = Field(None, description="Title of the detected standard")
    status: Optional[str] = Field(None, description="Current status of the standard (CURRENT, SUPERSEDED, etc.)")
    publication_year: Optional[int] = Field(None)
    successor_id: Optional[str] = Field(None, description="Successor standard if superseded")
    successor_title: Optional[str] = Field(None, description="Title of successor standard")
    successor_year: Optional[int] = Field(None)
    tooltip: Optional[str] = Field(None, description="Hover tooltip message for the officer")
    auto_fix: Optional[AutoFixAction] = Field(None, description="Auto-fix action if applicable")
    amendments_count: Optional[int] = Field(None, description="Number of amendments if standard is current")
    evidence: Dict[str, Any] = Field(default_factory=dict, description="Grounding evidence metadata")


class RedlineAnalysisRequest(BaseModel):
    """Request payload for redline document analysis."""
    document_text: str = Field(..., min_length=10, description="The full tender document text to analyze")
    tender_id: Optional[int] = Field(None, description="Optional linked tender document ID")
    auto_fix_all: bool = Field(False, description="If true, return the fully auto-corrected document text")


class RedlineSummary(BaseModel):
    """Summary statistics for the redline analysis."""
    total_segments: int = 0
    compliant_count: int = 0
    outdated_count: int = 0
    unrecognized_count: int = 0
    amended_count: int = 0
    auto_fixes_available: int = 0
    compliance_score: float = Field(0.0, ge=0.0, le=1.0, description="Fraction of standard refs that are current")


class RedlineAnalysisResponse(BaseModel):
    """Response from the redline analysis service."""
    segments: List[RedlineSegment] = Field(default_factory=list, description="Ordered annotated segments")
    summary: RedlineSummary = Field(default_factory=RedlineSummary)
    corrected_text: Optional[str] = Field(None, description="Auto-corrected full text (if auto_fix_all=True)")
    auto_fixes: List[AutoFixAction] = Field(default_factory=list, description="All available auto-fix actions")
    disclaimer: str = Field(
        "Redline analysis is grounded in the verified BIS dataset. "
        "Auto-fix suggestions replace superseded standards with their known successors. "
        "All corrections should be reviewed by a qualified procurement officer before adoption.",
        description="Trust model disclaimer"
    )
