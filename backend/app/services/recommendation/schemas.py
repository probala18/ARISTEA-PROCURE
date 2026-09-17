"""
Pydantic Schemas and Enums for Module 6 — Recommendation Engine.
Strictly adheres to:
1. Module 4 normalized RelationType names only.
2. Internal role designation for PRIMARY (not official BIS).
3. Internal decision-support definition for confidence_score (not legal certainty).
4. Full provenance and evidence traceability.
"""
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from backend.app.services.knowledge_graph.graph_models import RelationType
from backend.app.services.retrieval.hybrid_retriever import RetrievalFilter


class StandardRole(str, Enum):
    """Internal recommendation roles. Not official BIS designations."""
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    TESTING = "TESTING"
    SAFETY = "SAFETY"
    PERFORMANCE = "PERFORMANCE"
    INSTALLATION = "INSTALLATION"
    TERMINOLOGY = "TERMINOLOGY"
    RELATED_PRODUCT = "RELATED_PRODUCT"
    SUPERSEDED = "SUPERSEDED"
    NORMATIVE_REFERENCE = "NORMATIVE_REFERENCE"
    CONDITIONAL = "CONDITIONAL"


class ConfidenceLevel(str, Enum):
    """Internal decision-support confidence category."""
    HIGH = "HIGH"       # score >= 0.75
    MEDIUM = "MEDIUM"   # score >= 0.50
    LOW = "LOW"         # score < 0.50
    UNKNOWN = "UNKNOWN" # insufficient evidence


class IntentType(str, Enum):
    """Query intent classification types."""
    STANDARD_LOOKUP = "STANDARD_LOOKUP"
    PRODUCT_STANDARD_RECOMMENDATION = "PRODUCT_STANDARD_RECOMMENDATION"
    CERTIFICATION_REQUIREMENT = "CERTIFICATION_REQUIREMENT"
    TECHNICAL_QUESTION = "TECHNICAL_QUESTION"
    TESTING_REQUIREMENT = "TESTING_REQUIREMENT"
    GENERAL_BIS_QUERY = "GENERAL_BIS_QUERY"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    AMBIGUOUS_QUERY = "AMBIGUOUS_QUERY"
    MULTI_HOP_QUERY = "MULTI_HOP_QUERY"


class EvidenceRecord(BaseModel):
    """Authoritative traceable evidence grounded strictly in database records."""
    source_type: str  # STANDARD_RECORD, RELATIONSHIP_EDGE, CERTIFICATION_RECORD, QCO_ORDER, PROVENANCE
    standard_id: Optional[str] = None
    standard_number: str
    title: Optional[str] = None
    relationship_type: Optional[str] = None  # Strictly from RelationType
    is_explicit_source: Optional[bool] = None
    source_dataset: str
    record_identifier: Optional[str] = None
    details: str


class ExplainableScoreBreakdown(BaseModel):
    """Transparent breakdown of signals composing the internal RELEVANCE SCORE."""
    semantic_similarity: float = 0.0
    bm25_score: float = 0.0
    id_token_match: float = 0.0
    category_match: float = 0.0
    status_support: float = 0.0
    relationship_support: float = 0.0
    provenance_quality: float = 0.0
    raw_relevance_score: float = 0.0
    explanation: str = ""


class RecommendationCandidate(BaseModel):
    """A single recommended standard with explainable scoring, role, and evidence."""
    id: int
    standard_id: str
    is_number: str
    title: str
    category: Optional[str] = None
    status: str = "CURRENT"
    role: StandardRole
    role_disclaimer: str = (
        "Role 'PRIMARY' is an internal recommendation designation indicating the primary matching "
        "standard for query requirements. It is not an official BIS classification."
    )
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel
    confidence_disclaimer: str = (
        "Confidence score is an internal decision-support metric, not a probability, "
        "legal certainty, or claimed correctness percentage."
    )
    score_breakdown: ExplainableScoreBreakdown
    evidence: List[EvidenceRecord] = Field(default_factory=list)
    relationship_type: Optional[str] = None
    supersession_note: Optional[str] = None
    compliance_note: Optional[str] = None


class ClarificationPrompt(BaseModel):
    """Structured discriminator questions for genuinely ambiguous queries."""
    is_ambiguous: bool = True
    query: str
    explanation: str
    missing_discriminators: List[str] = Field(default_factory=list)
    suggested_options: List[Dict[str, Any]] = Field(default_factory=list)


class RecommendationRequest(BaseModel):
    """Input payload for the recommendation engine."""
    query_text: str
    language: Optional[str] = "en"
    category_hint: Optional[str] = None
    department_hint: Optional[int] = None
    filters: Optional[RetrievalFilter] = None
    session_id: Optional[str] = None
    max_primary: int = 3
    include_allied: bool = True


class RecommendationResponse(BaseModel):
    """Full recommendation payload matching Section 65 /api/analyze specifications."""
    analysis_id: str
    query: str
    detected_intent: IntentType
    detected_language: str = "en"
    extracted_attributes: Dict[str, Any] = Field(default_factory=dict)
    is_out_of_scope: bool = False
    is_ambiguous: bool = False
    overall_confidence_score: float = 0.0
    overall_confidence_level: ConfidenceLevel = ConfidenceLevel.UNKNOWN
    primary_standards: List[RecommendationCandidate] = Field(default_factory=list)
    allied_standards: Dict[str, List[RecommendationCandidate]] = Field(default_factory=dict)
    superseded_standards: List[RecommendationCandidate] = Field(default_factory=list)
    candidate_spectrum: List[RecommendationCandidate] = Field(default_factory=list)
    clarification_prompt: Optional[ClarificationPrompt] = None
    evidence_summary: List[EvidenceRecord] = Field(default_factory=list)
    explanation_summary: str = ""
    disclaimer: str = (
        "System recommendations are decision-support aids based strictly on supplied BIS records "
        "and do not constitute official BIS legal certification or statutory advice."
    )
