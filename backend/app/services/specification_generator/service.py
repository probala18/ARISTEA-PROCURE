"""
Service Layer for Module 13 — Specification Generator.
Manages database persistence, lifecycle, editing, and versioning for generated specifications
in the tender_specifications table.
Ensures regeneration and user edits never mutate or corrupt original tender evidence.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from backend.app.models.analysis import GeneratedSpecification
from backend.app.models.tender import TenderDocument
from backend.app.services.specification_generator.schemas import (
    SpecificationGenerationRequest,
    GeneratedSpecificationResponse,
    SpecificationUpdateRequest,
    SpecificationType,
)
from backend.app.services.specification_generator.generator import SpecificationGenerator


class SpecificationService:
    """Service facade for generating, retrieving, and editing specifications."""

    def __init__(self, db: Session):
        self.db = db
        self.generator = SpecificationGenerator(db)

    def generate_specification(self, req: SpecificationGenerationRequest) -> GeneratedSpecificationResponse:
        """
        Generates a specification, stores it in generated_specifications, and returns response.
        """
        # Validate tender exists if tender_id provided
        if req.tender_id:
            tender = self.db.query(TenderDocument).filter(TenderDocument.id == req.tender_id).first()
            if not tender:
                raise HTTPException(status_code=404, detail=f"Tender ID {req.tender_id} not found.")

        gen_text, structured, provenance = self.generator.generate(
            generation_type=req.generation_type,
            tender_id=req.tender_id,
            analysis_id=req.analysis_id,
            query_text=req.query_text,
            title=req.title,
            include_allied=req.include_allied,
            include_checklists=req.include_checklists,
        )

        spec_title = req.title or (
            f"Generated {req.generation_type.value.replace('_', ' ').title()}"
        )

        spec_record = GeneratedSpecification(
            tender_id=req.tender_id,
            analysis_id=req.analysis_id,
            spec_type=req.generation_type.value,
            title=spec_title,
            content=gen_text,
            structured_content=structured,
            grounding_evidence=provenance,
            is_edited=False,
            version=1,
        )

        self.db.add(spec_record)
        self.db.commit()
        self.db.refresh(spec_record)

        return self._to_response(spec_record)

    def get_specification(self, spec_id: int) -> GeneratedSpecificationResponse:
        """Retrieves a single generated specification by ID."""
        spec = self.db.query(GeneratedSpecification).filter(GeneratedSpecification.id == spec_id).first()
        if not spec:
            raise HTTPException(status_code=404, detail=f"Specification ID {spec_id} not found.")
        return self._to_response(spec)

    def list_specifications_for_tender(self, tender_id: int) -> List[GeneratedSpecificationResponse]:
        """Lists all specifications generated for a specific tender."""
        specs = self.db.query(GeneratedSpecification).filter(
            GeneratedSpecification.tender_id == tender_id
        ).order_by(GeneratedSpecification.created_at.desc()).all()
        return [self._to_response(s) for s in specs]

    def update_specification(self, spec_id: int, req: SpecificationUpdateRequest) -> GeneratedSpecificationResponse:
        """
        Updates an existing specification with user edits.
        Crucially: Modifies only the GeneratedSpecification record without corrupting
        or altering underlying tender documents, requirements, or audit findings.
        """
        spec = self.db.query(GeneratedSpecification).filter(GeneratedSpecification.id == spec_id).first()
        if not spec:
            raise HTTPException(status_code=404, detail=f"Specification ID {spec_id} not found.")

        if req.title is not None:
            spec.title = req.title
        if req.generated_text is not None:
            spec.content = req.generated_text
        if req.structured_content is not None:
            spec.structured_content = req.structured_content

        spec.is_edited = True
        spec.version = (spec.version or 1) + 1

        self.db.commit()
        self.db.refresh(spec)

        return self._to_response(spec)

    def delete_specification(self, spec_id: int) -> bool:
        """Deletes a generated specification."""
        spec = self.db.query(GeneratedSpecification).filter(GeneratedSpecification.id == spec_id).first()
        if not spec:
            raise HTTPException(status_code=404, detail=f"Specification ID {spec_id} not found.")
        self.db.delete(spec)
        self.db.commit()
        return True

    def _to_response(self, spec: GeneratedSpecification) -> GeneratedSpecificationResponse:
        """Converts ORM model to API response model."""
        return GeneratedSpecificationResponse(
            id=spec.id,
            tender_id=spec.tender_id,
            analysis_id=spec.analysis_id or (str(spec.session_id) if spec.session_id else None),
            generation_type=spec.spec_type,
            title=spec.title or "Procurement Specification",
            generated_text=spec.content,
            structured_content=spec.structured_content or {},
            provenance_records=spec.grounding_evidence or [],
            is_edited=spec.is_edited or False,
            version=spec.version or 1,
            created_at=str(spec.created_at) if spec.created_at else None,
            updated_at=str(spec.updated_at) if spec.updated_at else None,
        )
