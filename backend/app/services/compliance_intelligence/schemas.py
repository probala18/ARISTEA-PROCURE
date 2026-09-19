"""
Pydantic Schemas for Module 9 — Compliance Intelligence.
Strictly adheres to:
1. Deterministic evidence layer (no LLM, no external knowledge).
2. Requirement level: MANDATORY, VOLUNTARY, CONDITIONAL, UNKNOWN.
3. Explicit evidence required for MANDATORY (never inferred from standard existence or licence count).
4. QCO status preserved verbatim (never labeled ACTIVE without explicit dataset status).
5. Grounded scheme classification (BIS_ISI, CRS, Hallmarking, Scheme I/II/IV).
6. Preserves all evidence records (voluntary records never discarded when mandatory exists).
7. Scope-aware regulatory divergence flagging.
8. Backward compatibility with Module 7 ComplianceLinksResult.
"""
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field


class RequirementLevel(str, Enum):
    """
    Deterministic compliance requirement levels.
    Evaluated strictly from ingested dataset records:
    - MANDATORY: Supported by explicit mandatory QCO or mandatory certification record.
    - CONDITIONAL: Supported by explicit conditional certification record.
    - VOLUNTARY: Supported by explicit voluntary certification with no applicable mandatory QCO.
    - UNKNOWN: Insufficient or missing evidence in ingested dataset.
    """
    MANDATORY = "MANDATORY"
    VOLUNTARY = "VOLUNTARY"
    CONDITIONAL = "CONDITIONAL"
    UNKNOWN = "UNKNOWN"


class CertificationSchemeType(str, Enum):
    """
    Standard certification schemes grounded in actual dataset fields:
    - BIS_ISI: Scheme-I Product Certification (ISI Mark)
    - CRS: Compulsory Registration Scheme (Scheme-II)
    - HALLMARKING: Precious metals fineness and marking
    - SCHEME_I: General Scheme-I
    - SCHEME_II: General Scheme-II
    - SCHEME_IV: Management/Testing/Codes of practice
    - UNKNOWN: No scheme recorded in dataset
    """
    BIS_ISI = "BIS_ISI"
    CRS = "CRS"
    HALLMARKING = "HALLMARKING"
    SCHEME_I = "SCHEME_I"
    SCHEME_II = "SCHEME_II"
    SCHEME_IV = "SCHEME_IV"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


class GroundedCertificationRecord(BaseModel):
    """Single certification record with complete provenance."""
    id: int
    standard_id: Optional[int] = None
    standard_number: str
    product_name: Optional[str] = None
    product_rating: Optional[str] = None
    certification_type: Optional[str] = None
    certification_status: Optional[str] = None
    is_mandatory: Optional[bool] = None
    requirement_level: str = "UNKNOWN"
    source_dataset: str
    provenance: Optional[Dict[str, Any]] = None


class GroundedQCORecord(BaseModel):
    """Single Quality Control Order record with complete provenance."""
    id: int
    standard_id: Optional[int] = None
    standard_number: str
    product_name: Optional[str] = None
    qco_id: Optional[str] = None
    qco_title: Optional[str] = None
    notification_number: Optional[str] = None
    notification_date: Optional[str] = None
    notification_links: Optional[str] = None
    ministry_department: Optional[str] = None
    status: Optional[str] = None  # Preserved verbatim from dataset
    is_mandatory: bool = True
    source_dataset: str
    provenance: Optional[Dict[str, Any]] = None


class GroundedLicenceContext(BaseModel):
    """Product licence count context from productlicence.csv."""
    id: int
    product_category: str
    licence_count: int
    source_dataset: str = "productlicence.csv"
    provenance: Optional[Dict[str, Any]] = None


class GroundedMinistryMapping(BaseModel):
    """Ministry and department procurement linkage from upcomming.csv."""
    id: int
    ministry_department: Optional[str] = None
    product_name: Optional[str] = None
    standard_number: Optional[str] = None
    source_dataset: str = "upcomming.csv"
    provenance: Optional[Dict[str, Any]] = None


class RegulatoryDivergenceItem(BaseModel):
    """Scope-aware regulatory divergence notice."""
    standard_number: str
    divergence_type: str = "REGULATORY_DIVERGENCE"
    description: str
    voluntary_record: Dict[str, Any]
    mandatory_record: Dict[str, Any]


class StandardCertificationReport(BaseModel):
    """
    Section 66 endpoint report: GET /api/standards/{standard_id}/certification.
    Consolidates certification records, QCO mandates, and governing scheme.
    """
    standard_id: str
    canonical_id: str
    is_number: str
    title: str
    requirement_level: RequirementLevel
    governing_scheme: str
    total_certifications: int = 0
    total_qcos: int = 0
    certifications: List[GroundedCertificationRecord] = Field(default_factory=list)
    qco_mandates: List[GroundedQCORecord] = Field(default_factory=list)
    disclaimer: str = (
        "Compliance intelligence reflects facts ingested in the project dataset. "
        "It does not constitute independent legal advice or an authoritative regulatory determination. "
        "Consult official BIS Gazette notifications for statutory compliance."
    )


class ComplianceIntelligenceReport(BaseModel):
    """
    Comprehensive compliance intelligence report.
    Extends and preserves all fields of Module 7 ComplianceLinksResult for 100% backward compatibility.
    """
    standard_id: str
    canonical_id: str
    is_number: Optional[str] = None
    title: Optional[str] = None
    status: Optional[str] = None

    # Module 9 Deterministic Evidence Conclusions
    requirement_level: RequirementLevel = RequirementLevel.UNKNOWN
    governing_scheme: str = "UNKNOWN"

    # Module 7 Legacy Fields (Preserved identically)
    is_mandatory_certification: Optional[bool] = None
    qco_applicable: Optional[bool] = None
    certification_records: List[Dict[str, Any]] = Field(default_factory=list)
    qco_records: List[Dict[str, Any]] = Field(default_factory=list)
    product_licences: List[Dict[str, Any]] = Field(default_factory=list)
    ministry_mappings: List[Dict[str, Any]] = Field(default_factory=list)
    regulatory_divergence_detected: bool = False
    regulatory_divergence_notes: List[str] = Field(default_factory=list)

    # Detailed Divergences & Provenance
    divergences: List[RegulatoryDivergenceItem] = Field(default_factory=list)
    confidence_score: float = 1.0  # Internal decision-support metric
    evidence_count: int = 0
    disclaimer: str = (
        "Compliance intelligence is derived from the project dataset. "
        "Requirement levels (MANDATORY/VOLUNTARY/CONDITIONAL/UNKNOWN) are deterministic reflections of ingested records. "
        "Confidence score is an internal decision-support metric, not a probability or legal certainty."
    )


class BatchComplianceItem(BaseModel):
    """Single item in a batch compliance check result."""
    identifier: str
    found: bool
    result: Optional[ComplianceIntelligenceReport] = None
    error: Optional[str] = None


class BatchComplianceResult(BaseModel):
    """Batch compliance evaluation result."""
    total_requested: int
    total_found: int
    total_mandatory: int
    total_voluntary: int
    total_conditional: int
    total_unknown: int
    total_with_divergence: int
    results: List[BatchComplianceItem] = Field(default_factory=list)


class BatchComplianceRequest(BaseModel):
    """Request payload for batch compliance evaluation."""
    identifiers: List[str] = Field(..., min_length=1, max_length=100, description="List of standard identifiers or IDs")
