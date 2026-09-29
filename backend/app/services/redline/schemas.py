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


class MeasurementItem(BaseModel):
    """Extracted physical or engineering measurement from tender."""
    parameter: str
    value: str
    unit: str
    tolerance: Optional[str] = None
    standard_ref: Optional[str] = None
    category: str = "General"


class TenderOverview(BaseModel):
    """Executive tender overview with extracted measurements."""
    title: str
    department: str
    nit_number: str
    scope_summary: str
    estimated_timeline: str
    measurements: List[MeasurementItem] = Field(default_factory=list)


class ComparisonRow(BaseModel):
    """Single row in the tender vs IS standard vs benchmark comparison matrix."""
    parameter: str
    clause: str
    specified_value: str
    is_standard_mandate: str
    industry_benchmark: str
    status: str  # COMPLIANT, OUTDATED, DEFICIENT, EXCEEDS
    delta: str
    chart_value_specified: Optional[float] = None
    chart_value_required: Optional[float] = None
    chart_unit: Optional[str] = None


class EcoTrack(BaseModel):
    """Green procurement and sustainability footprint analytics."""
    eco_score: int = Field(85, ge=0, le=100)
    grade: str = "Tier-A Green Procurement"
    energy_efficiency_class: str = "IE3 / BEE 5-Star"
    annual_kwh_savings: float = 14200.0
    annual_co2_reduction_tons: float = 11.6
    lifecycle_cost_savings_inr: float = 340800.0
    compliance_tags: List[str] = Field(default_factory=list)
    sustainability_insights: List[str] = Field(default_factory=list)


class BidderRequirements(BaseModel):
    """Summary of bidder qualification criteria."""
    technical_criteria: List[str] = Field(default_factory=list)
    financial_criteria: List[str] = Field(default_factory=list)
    statutory_declarations: List[str] = Field(default_factory=list)
    required_documents: List[str] = Field(default_factory=list)


class StandardRedlineMapping(BaseModel):
    """Check old standard (marked red) -> get new standard with official reference."""
    old_standard: str
    old_status: str
    old_title: str
    new_standard: str
    new_status: str
    new_title: str
    bis_reference: str
    circular_number: str
    reason: str
    clause_impact: str


class PrimarySourceItem(BaseModel):
    """Authoritative primary source link."""
    name: str
    category: str
    url: str
    description: str


class ComplianceTaskItem(BaseModel):
    """Actionable compliance task that can be tracked in the app."""
    id: str
    title: str
    description: str
    primary_source_name: str
    primary_source_url: str
    priority: str = "High"  # High, Medium, Low
    status: str = "PENDING"  # PENDING, IN_PROGRESS, COMPLETED
    due_stage: str = "Pre-Tender Technical Vetting"


class CostLineItem(BaseModel):
    category: str
    amount: float
    percentage: float
    basis: str


class AiCostEstimation(BaseModel):
    """AI cost & expenditure recommendation for the project."""
    estimated_total_inr: float
    estimated_range_inr: str
    rates_basis: str
    line_items: List[CostLineItem] = Field(default_factory=list)
    potential_savings_inr: float = 0.0
    cost_optimizations: List[str] = Field(default_factory=list)


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
    
    # 7 New Powerful Capabilities
    tender_overview: Optional[TenderOverview] = None
    comparison_matrix: List[ComparisonRow] = Field(default_factory=list)
    eco_track: Optional[EcoTrack] = None
    bidder_requirements: Optional[BidderRequirements] = None
    standards_redline_mappings: List[StandardRedlineMapping] = Field(default_factory=list)
    primary_sources: List[PrimarySourceItem] = Field(default_factory=list)
    compliance_tasks: List[ComplianceTaskItem] = Field(default_factory=list)
    cost_estimation: Optional[AiCostEstimation] = None

    disclaimer: str = Field(
        "Redline analysis is grounded in the verified BIS dataset. "
        "Auto-fix suggestions replace superseded standards with their known successors. "
        "All corrections should be reviewed by a qualified procurement officer before adoption.",
        description="Trust model disclaimer"
    )

