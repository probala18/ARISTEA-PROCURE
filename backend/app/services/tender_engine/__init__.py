"""
Module 11: Tender Document Engine Package.
Exports schemas, document parsers, clause detectors, standard extractors, and TenderEngineService.
"""
from backend.app.services.tender_engine.schemas import (
    TenderProcessingStatus,
    SectionType,
    ExtractedClause,
    ExtractedSection,
    ExtractedStandardReference,
    TenderUploadResponse,
    TenderDetailResponse,
    TenderStatusResponse,
    TenderRequirementsResponse,
    TenderReferencesResponse,
)
from backend.app.services.tender_engine.parsers import (
    BaseDocumentParser,
    PDFParser,
    DOCXParser,
    TXTParser,
    DocumentParseResult,
    ParsedPage,
    get_parser,
)
from backend.app.services.tender_engine.clause_detector import ClauseDetector
from backend.app.services.tender_engine.standard_extractor import StandardExtractor
from backend.app.services.tender_engine.tender_service import TenderEngineService

__all__ = [
    "TenderProcessingStatus",
    "SectionType",
    "ExtractedClause",
    "ExtractedSection",
    "ExtractedStandardReference",
    "TenderUploadResponse",
    "TenderDetailResponse",
    "TenderStatusResponse",
    "TenderRequirementsResponse",
    "TenderReferencesResponse",
    "BaseDocumentParser",
    "PDFParser",
    "DOCXParser",
    "TXTParser",
    "DocumentParseResult",
    "ParsedPage",
    "get_parser",
    "ClauseDetector",
    "StandardExtractor",
    "TenderEngineService",
]
