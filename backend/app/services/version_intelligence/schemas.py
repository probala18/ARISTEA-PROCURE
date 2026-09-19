"""
Pydantic Schemas for Module 8 — Version and Amendment Intelligence.
Strictly adheres to:
1. All version/amendment facts grounded in StandardVersion and Standard tables.
2. Supersession data delegated to Module 4 SupersessionChainService (single source of truth).
3. confidence_score is an internal decision-support metric, not probability or legal certainty.
4. Warnings are evidence-based: never inferred from title similarity or general domain knowledge.
5. Every fact carries source_dataset provenance.
6. Distinguishes "latest version information available in the supplied dataset"
   from "legally current standard".
7. OUTDATED_VERSION_WARNING is NOT triggered merely because latest_year != publication_year.
   A later latest_year may simply indicate a revision or amendment, not that the standard is outdated.
"""
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field


class WarningType(str, Enum):
    """
    Typed version/amendment warning categories.
    Terminology aligned with actual supplied data concepts:
    - SUPERSEDED: Standard.status == 'SUPERSEDED', with successor info from Module 4 graph only.
    - AMENDMENT_AVAILABLE: StandardVersion records with amendment_number exist.
    - VERSION_GAP: Dataset contains version records suggesting a revision history gap
      (e.g., publication_year present but no StandardVersion records at all).
    - UNKNOWN_VERSION_STATUS: No version evidence exists in the ingested dataset.
    """
    SUPERSEDED_WARNING = "SUPERSEDED_WARNING"
    AMENDMENT_AVAILABLE = "AMENDMENT_AVAILABLE"
    VERSION_GAP = "VERSION_GAP"
    UNKNOWN_VERSION_STATUS = "UNKNOWN_VERSION_STATUS"


class AmendmentRecord(BaseModel):
    """Single amendment entry with full provenance."""
    id: int
    standard_id: int
    is_number: str
    amendment_number: Optional[int] = None
    amendment_year: Optional[int] = None
    change_description: Optional[str] = None
    current_state: str
    source_dataset: str
    source_provenance: Optional[Dict[str, Any]] = None


class VersionWarning(BaseModel):
    """
    Evidence-grounded version warning.
    Every warning is strictly derived from ingested data fields,
    not inferred from external knowledge or title similarity.
    """
    warning_type: WarningType
    message: str
    severity: str = "INFO"  # INFO, WARNING, CRITICAL
    evidence: Dict[str, Any] = Field(default_factory=dict)
    source_dataset: Optional[str] = None


class CurrencyCheckResult(BaseModel):
    """
    Dataset-backed version/status intelligence for a single standard.
    is_current is derived strictly from Standard.status field (not from publication years).
    This does NOT independently establish legal or regulatory currency.
    Warnings are grounded in ingested version/amendment/supersession data only.
    """
    standard_id: str
    canonical_id: str
    is_number: str
    title: str
    status: str
    publication_year: Optional[int] = None
    latest_year: Optional[int] = None
    is_current: bool
    warnings: List[VersionWarning] = Field(default_factory=list)
    total_amendments: int = 0
    disclaimer: str = (
        "This is dataset-backed version/status intelligence derived from the ingested dataset. "
        "It does not independently establish legal or regulatory currency. "
        "For authoritative status, consult the official BIS catalogue."
    )


class VersionIntelligenceReport(BaseModel):
    """
    Comprehensive version intelligence report for a standard.
    Consolidates: current state, version records, amendments,
    supersession lineage (from Module 4), and evidence-grounded warnings.
    Distinguishes 'latest version information available in the supplied dataset'
    from 'legally current standard'.
    """
    standard_id: str
    canonical_id: str
    is_number: str
    title: str
    status: str
    publication_year: Optional[int] = None
    latest_year: Optional[int] = None

    # Version records from StandardVersion table
    version_records: List[Dict[str, Any]] = Field(default_factory=list)

    # Amendment-specific records (subset of version_records where amendment_number is set)
    amendments: List[AmendmentRecord] = Field(default_factory=list)

    # Supersession lineage from Module 4 SupersessionChainService
    supersession: Dict[str, Any] = Field(default_factory=dict)

    # Evidence-grounded warnings
    warnings: List[VersionWarning] = Field(default_factory=list)

    # Provenance
    source_file: str = ""
    disclaimer: str = (
        "Version intelligence reflects the latest version information available in the supplied dataset. "
        "It does not constitute a determination of legally current standard status. "
        "For authoritative current status and amendments, consult the official BIS catalogue."
    )


class BatchCurrencyItem(BaseModel):
    """Single item in a batch currency check result."""
    identifier: str
    found: bool
    result: Optional[CurrencyCheckResult] = None
    error: Optional[str] = None


class BatchCurrencyResult(BaseModel):
    """Batch currency check results for multiple standards."""
    total_requested: int
    total_found: int
    total_current: int
    total_with_warnings: int
    results: List[BatchCurrencyItem] = Field(default_factory=list)
