"""
Pydantic schemas for Module 12: Tender Gap Detection & Audit.
Defines data structures for:
- Expected vs Present standard comparisons
- Gap classifications (MISSING_REFERENCE, OUTDATED_REFERENCE, POTENTIALLY_MISSING_TESTING_STANDARD, etc.)
- Trust models (KNOWN, INFERRED, UNKNOWN)
- Comprehensive evidence-based audit reports
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class GapSeverity(str, Enum):
    """Severity classification of identified procurement gaps."""
    CRITICAL = "CRITICAL"      # e.g., Outdated mandatory standard, omitted mandatory safety standard
    WARNING = "WARNING"        # e.g., Missing reference for clearly identified product
    ADVISORY = "ADVISORY"      # e.g., Potentially missing allied testing standard
    INFO = "INFO"              # e.g., Amendment available or sufficient evidence verified


class GapCategory(str, Enum):
    """Categorized gap types adhering to evidence-grounded rules."""
    MISSING_REFERENCE = "MISSING_REFERENCE"
    OUTDATED_REFERENCE = "OUTDATED_REFERENCE"
    POTENTIALLY_MISSING_TESTING_STANDARD = "POTENTIALLY_MISSING_TESTING_STANDARD"
    POTENTIALLY_MISSING_SAFETY_STANDARD = "POTENTIALLY_MISSING_SAFETY_STANDARD"
    CERTIFICATION_GAP = "CERTIFICATION_GAP"
    COMPLIANCE_EVIDENCE_MISSING = "COMPLIANCE_EVIDENCE_MISSING"
    AMBIGUOUS_SPECIFICATION = "AMBIGUOUS_SPECIFICATION"
    SUFFICIENT_EVIDENCE = "SUFFICIENT_EVIDENCE"


class TrustLevel(str, Enum):
    """Section 83 Tender Audit Trust Model."""
    KNOWN = "KNOWN"            # Explicitly mentioned in tender document text
    INFERRED = "INFERRED"      # Derived via semantic retrieval, recommendation, or graph traversal
    UNKNOWN = "UNKNOWN"        # Unresolved or missing evidence in authoritative dataset


class TenderGapItem(BaseModel):
    """A specific gap, discrepancy, or compliance observation identified during audit."""
    gap_category: GapCategory = Field(..., description="Categorized gap type")
    severity: GapSeverity = Field(..., description="Risk/urgency severity")
    trust_level: TrustLevel = Field(..., description="Trust level: KNOWN, INFERRED, or UNKNOWN")
    standard_id: Optional[str] = Field(None, description="Standard ID involved, e.g. 'IS 325' or 'IS 12615:2018'")
    title: Optional[str] = Field(None, description="Title of the standard")
    clause_reference: Optional[str] = Field(None, description="Clause number in tender where issue originates")
    clause_text: Optional[str] = Field(None, description="Source snippet from tender text")
    successor_standard_id: Optional[str] = Field(None, description="Successor standard ID if superseded")
    successor_title: Optional[str] = Field(None, description="Title of successor standard if superseded")
    issue_description: str = Field(..., description="Detailed explanation of the gap")
    recommendation: str = Field(..., description="Actionable correction guidance for procurement official")
    evidence: Dict[str, Any] = Field(default_factory=dict, description="Underlying dataset grounding evidence")


class ExpectedVsPresentComparison(BaseModel):
    """Structured breakdown of expected vs present standards."""
    present_standards: List[Dict[str, Any]] = Field(default_factory=list, description="Standards explicitly cited in tender")
    expected_standards: List[Dict[str, Any]] = Field(default_factory=list, description="Standards recommended based on requirements")
    missing_standards: List[Dict[str, Any]] = Field(default_factory=list, description="Expected standards not cited in tender")
    outdated_standards: List[Dict[str, Any]] = Field(default_factory=list, description="Present standards that are superseded")
    testing_gaps: List[Dict[str, Any]] = Field(default_factory=list, description="Allied testing standards from graph not cited")
    safety_gaps: List[Dict[str, Any]] = Field(default_factory=list, description="Allied safety standards from graph not cited")
    certification_gaps: List[Dict[str, Any]] = Field(default_factory=list, description="QCO/Mandatory certification discrepancies")


class TenderAuditReport(BaseModel):
    """Comprehensive evidence-grounded tender audit report."""
    tender_id: int = Field(..., description="Database ID of the tender document")
    tender_number: Optional[str] = Field(None, description="Tender or bid reference number")
    filename: str = Field(..., description="Tender filename")
    coverage_score: float = Field(..., ge=0.0, le=1.0, description="Audit coverage score (0.0 to 1.0)")
    coverage_percentage: float = Field(..., ge=0.0, le=100.0, description="Coverage score percentage")
    audit_summary: str = Field(..., description="Executive summary of tender audit findings")
    total_gaps_found: int = Field(0, description="Total number of gaps and observations detected")
    critical_issues_count: int = Field(0, description="Count of CRITICAL severity issues")
    warnings_count: int = Field(0, description="Count of WARNING severity issues")
    advisories_count: int = Field(0, description="Count of ADVISORY severity issues")
    gaps: List[TenderGapItem] = Field(default_factory=list, description="Individual gap observations")
    expected_vs_present: ExpectedVsPresentComparison = Field(..., description="Expected vs present breakdown")
    trust_disclaimer: str = Field(
        "Tender audit results distinguish KNOWN facts (explicit text citations), INFERRED recommendations "
        "(knowledge graph and retrieval), and UNKNOWN evidence. Inferred recommendations do not constitute "
        "statutory legal advice.",
        description="Section 83 mandatory trust model disclaimer"
    )
    created_at: Optional[datetime] = None
