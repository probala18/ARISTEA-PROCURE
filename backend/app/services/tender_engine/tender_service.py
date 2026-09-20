"""
Tender Engine Orchestrator Service (Module 11).
Coordinates:
- Multi-format document parsing (PDF, DOCX, TXT)
- Section extraction and clause detection
- Explicit standard reference extraction and canonical database grounding
- Database persistence to tender_documents, tender_sections, tender_requirements, and tender_standard_references
- Observability and status lifecycle (QUEUED, PROCESSING, COMPLETED, FAILED)
"""
import uuid
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.models.tender import (
    TenderDocument,
    TenderSection,
    TenderRequirement,
    TenderStandardReference,
)
from backend.app.services.tender_engine.schemas import (
    TenderProcessingStatus,
    TenderUploadResponse,
    TenderDetailResponse,
    TenderStatusResponse,
    TenderRequirementsResponse,
    TenderReferencesResponse,
    ExtractedStandardReference,
)
from backend.app.services.tender_engine.parsers import get_parser, DocumentParseResult
from backend.app.services.tender_engine.clause_detector import ClauseDetector
from backend.app.services.tender_engine.standard_extractor import StandardExtractor

logger = logging.getLogger(__name__)


class TenderEngineService:
    """Unified service for tender document parsing, extraction, and grounding."""

    def __init__(self, db_session: Optional[Session] = None):
        self.db = db_session
        if self.db:
            try:
                from backend.app.core.database import Base
                import backend.app.models.tender
                import backend.app.models.specification
                Base.metadata.create_all(bind=self.db.get_bind())
            except Exception as e:
                logger.warning(f"Error ensuring tender tables exist: {e}")
        self.clause_detector = ClauseDetector()
        self.standard_extractor = StandardExtractor(db_session) if db_session else None

    def process_document(
        self,
        file_content: bytes,
        filename: str,
        file_type_hint: Optional[str] = None,
        tender_number: Optional[str] = None,
        title: Optional[str] = None,
        organization: Optional[str] = None,
    ) -> TenderDocument:
        """
        Parses document bytes, segments sections & clauses, extracts standard citations,
        and records everything in the database.
        """
        if not file_content or len(file_content) < 10:
            raise ValueError("Uploaded file is empty or corrupted.")

        # 1. Select parser and extract raw text & pages
        parser = get_parser(filename or file_type_hint or "txt")
        try:
            parse_result: DocumentParseResult = parser.parse(file_content, filename=filename)
        except Exception as e:
            logger.error(f"Failed to parse document '{filename}': {e}", exc_info=True)
            raise ValueError(f"Document parsing failed: {e}")

        # 2. Segment into sections and clauses
        sections = self.clause_detector.segment_sections_and_clauses(parse_result.pages)

        # 3. Extract explicit standard citations and ground against DB
        extractor = self.standard_extractor or StandardExtractor(self.db)
        standard_refs = extractor.extract_from_sections(sections)

        # 4. Generate unique tender number if not provided
        t_num = tender_number or f"TND-{uuid.uuid4().hex[:8].upper()}"

        # 5. Persist to Database if session available
        tender_doc = TenderDocument(
            tender_number=t_num,
            filename=filename,
            title=title or parse_result.metadata.get("title") or filename,
            organization=organization or "General Procurement",
            file_type=parse_result.file_type,
            file_size=len(file_content),
            raw_text=parse_result.raw_text,
            parsed_metadata={
                "total_pages": parse_result.total_pages,
                "total_sections": len(sections),
                "total_standards_detected": len(standard_refs),
                "metadata": parse_result.metadata,
            },
            status=TenderProcessingStatus.COMPLETED.value,
        )

        if self.db:
            self.db.add(tender_doc)
            self.db.flush()  # populate tender_doc.id

            # Save sections & clauses
            for sec in sections:
                db_sec = TenderSection(
                    tender_id=tender_doc.id,
                    section_title=sec.section_title,
                    section_number=sec.section_number,
                    page_number=sec.page_number,
                    content=sec.content,
                    section_type=sec.section_type.value,
                )
                self.db.add(db_sec)
                self.db.flush()

                # Map clauses to requirements
                for c in sec.clauses:
                    db_req = TenderRequirement(
                        tender_id=tender_doc.id,
                        section_id=db_sec.id,
                        requirement_text=c.text,
                        extracted_intent=c.extracted_intent,
                        product_keywords=c.product_keywords,
                        technical_attributes=c.technical_attributes,
                        is_mandatory=c.is_mandatory,
                    )
                    self.db.add(db_req)

            # Save explicit standard references
            for ref in standard_refs:
                db_ref = TenderStandardReference(
                    tender_id=tender_doc.id,
                    standard_number_raw=ref.standard_number_raw,
                    detected_standard_id=ref.detected_standard_id,
                    is_valid=ref.is_valid,
                    is_superseded=ref.is_superseded,
                    superseded_by_standard_id=ref.superseded_by_standard_id,
                    detected_clause=ref.detected_clause,
                )
                self.db.add(db_ref)

            self.db.commit()
            self.db.refresh(tender_doc)

        return tender_doc

    def get_tender(self, tender_id: int) -> Optional[TenderDocument]:
        """Retrieves TenderDocument with sections and requirements."""
        if not self.db:
            return None
        return self.db.query(TenderDocument).filter(TenderDocument.id == tender_id).first()

    def get_requirements(self, tender_id: int) -> List[TenderRequirement]:
        """Retrieves extracted technical requirements for a tender."""
        if not self.db:
            return []
        return self.db.query(TenderRequirement).filter(TenderRequirement.tender_id == tender_id).all()

    def get_references(self, tender_id: int) -> List[TenderStandardReference]:
        """Retrieves detected standard citations for a tender."""
        if not self.db:
            return []
        return self.db.query(TenderStandardReference).filter(TenderStandardReference.tender_id == tender_id).all()
