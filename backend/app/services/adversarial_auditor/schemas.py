"""
Pydantic schemas for the Adversarial Auditor AI service.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class VerificationVerdict(str, Enum):
    """Verdict from the adversarial auditor for each standard reference."""
    VERIFIED = "VERIFIED"                  # ✅ Confirmed real and current in BIS database
    SUPERSEDED_VERIFIED = "SUPERSEDED_VERIFIED"  # ⚠ Real but superseded — successor confirmed
    SUSPICIOUS = "SUSPICIOUS"              # 🟡 Looks plausible but not confirmed — manual check needed
    HALLUCINATION = "HALLUCINATION"        # 🔴 Does not exist in any known BIS dataset — blocked
    PARTIAL_MATCH = "PARTIAL_MATCH"        # 🟠 Partial match found — ambiguous, needs review
    FORMAT_INVALID = "FORMAT_INVALID"      # Standard number format is wrong


class VerifiedStandard(BaseModel):
    """Result of adversarial verification for a single standard reference."""
    input_reference: str = Field(..., description="The original standard reference string")
    normalized_reference: str = Field(..., description="Normalized form of the reference")
    verdict: VerificationVerdict = Field(..., description="Auditor's verdict")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Auditor's confidence in the verdict")
    matched_standard_id: Optional[str] = Field(None, description="Matched canonical standard ID if found")
    matched_title: Optional[str] = Field(None, description="Title of matched standard")
    matched_status: Optional[str] = Field(None, description="Status of matched standard (CURRENT, SUPERSEDED)")
    successor_id: Optional[str] = Field(None, description="Successor standard if superseded")
    closest_matches: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Closest matching standards for SUSPICIOUS/PARTIAL_MATCH verdicts"
    )
    reason: str = Field(..., description="Human-readable explanation of the verdict")
    blocked: bool = Field(False, description="If True, this reference should NOT be used without manual review")
    evidence: Dict[str, Any] = Field(default_factory=dict, description="Grounding evidence")


class AuditVerificationRequest(BaseModel):
    """Request payload for adversarial verification."""
    references: List[str] = Field(
        ...,
        min_length=1,
        description="List of standard reference strings to verify (e.g. ['IS 325:1996', 'IS 9999'])"
    )
    strict_mode: bool = Field(
        True,
        description="If True, any reference not 100% confirmed is blocked"
    )
    include_closest_matches: bool = Field(
        True,
        description="Include closest database matches for suspicious references"
    )


class AuditVerificationResponse(BaseModel):
    """Response from the adversarial auditor."""
    total_checked: int = Field(0, description="Total references checked")
    verified_count: int = Field(0, description="References confirmed as real and valid")
    suspicious_count: int = Field(0, description="References flagged as suspicious")
    hallucination_count: int = Field(0, description="References flagged as likely fabricated")
    blocked_count: int = Field(0, description="References blocked from use")
    results: List[VerifiedStandard] = Field(default_factory=list, description="Per-reference verification results")
    overall_trust_score: float = Field(
        0.0, ge=0.0, le=1.0,
        description="Overall trust score (1.0 = all verified, 0.0 = all hallucinated)"
    )
    auditor_warning: Optional[str] = Field(
        None,
        description="High-level warning message from the auditor"
    )
    disclaimer: str = Field(
        "The Adversarial Auditor AI cross-checks all standard references against the verified BIS dataset. "
        "References marked SUSPICIOUS or HALLUCINATION should NOT be used in official procurement documents "
        "without manual verification. This system is designed to catch AI hallucinations and prevent "
        "legal issues from fabricated standard numbers.",
        description="Mandatory trust model disclaimer"
    )
