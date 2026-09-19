"""
Module 8 — Version and Amendment Intelligence.
Provides consolidated version, amendment, supersession, and currency checks
grounded strictly in ingested dataset records and Module 4's SupersessionChainService.
"""
from backend.app.services.version_intelligence.schemas import (
    WarningType,
    AmendmentRecord,
    VersionWarning,
    CurrencyCheckResult,
    VersionIntelligenceReport,
    BatchCurrencyItem,
    BatchCurrencyResult,
)
from backend.app.services.version_intelligence.version_intelligence_service import (
    VersionIntelligenceService,
)

__all__ = [
    "WarningType",
    "AmendmentRecord",
    "VersionWarning",
    "CurrencyCheckResult",
    "VersionIntelligenceReport",
    "BatchCurrencyItem",
    "BatchCurrencyResult",
    "VersionIntelligenceService",
]
