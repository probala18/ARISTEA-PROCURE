"""
Adversarial Auditor AI Service.
Implements a "second opinion" AI that aggressively double-checks
every standard reference for hallucination, fabrication, and uncertainty.
"""
from backend.app.services.adversarial_auditor.auditor_service import (
    AdversarialAuditorService,
    AuditVerificationRequest,
    AuditVerificationResponse,
)

__all__ = [
    "AdversarialAuditorService",
    "AuditVerificationRequest",
    "AuditVerificationResponse",
]
