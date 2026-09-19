"""
Module 9 — Compliance Intelligence.
Provides deterministic, evidence-driven compliance and regulatory intelligence
linking standards with QCOs, certification schemes (BIS/ISI, CRS, Hallmarking),
licence context, and scope-aware divergence detection.
"""
from backend.app.services.compliance_intelligence.schemas import (
    RequirementLevel,
    CertificationSchemeType,
    GroundedCertificationRecord,
    GroundedQCORecord,
    GroundedLicenceContext,
    GroundedMinistryMapping,
    RegulatoryDivergenceItem,
    StandardCertificationReport,
    ComplianceIntelligenceReport,
    BatchComplianceItem,
    BatchComplianceResult,
    BatchComplianceRequest,
)
from backend.app.services.compliance_intelligence.compliance_intelligence_service import (
    ComplianceIntelligenceService,
)

__all__ = [
    "RequirementLevel",
    "CertificationSchemeType",
    "GroundedCertificationRecord",
    "GroundedQCORecord",
    "GroundedLicenceContext",
    "GroundedMinistryMapping",
    "RegulatoryDivergenceItem",
    "StandardCertificationReport",
    "ComplianceIntelligenceReport",
    "BatchComplianceItem",
    "BatchComplianceResult",
    "BatchComplianceRequest",
    "ComplianceIntelligenceService",
]
