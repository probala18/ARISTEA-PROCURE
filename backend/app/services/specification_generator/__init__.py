"""
Module 13 — Specification Generator.
"""
from backend.app.services.specification_generator.schemas import (
    SpecificationType,
    RequirementOrigin,
    RegulatoryStatus,
    GeneratedRequirementItem,
    TechnicalSpecificationContent,
    TenderClauseContent,
    ComplianceChecklistItem,
    AuditCorrectionContent,
    SpecificationGenerationRequest,
    GeneratedSpecificationResponse,
    SpecificationUpdateRequest,
)
from backend.app.services.specification_generator.generator import SpecificationGenerator
from backend.app.services.specification_generator.service import SpecificationService

__all__ = [
    "SpecificationType",
    "RequirementOrigin",
    "RegulatoryStatus",
    "GeneratedRequirementItem",
    "TechnicalSpecificationContent",
    "TenderClauseContent",
    "ComplianceChecklistItem",
    "AuditCorrectionContent",
    "SpecificationGenerationRequest",
    "GeneratedSpecificationResponse",
    "SpecificationUpdateRequest",
    "SpecificationGenerator",
    "SpecificationService",
]
