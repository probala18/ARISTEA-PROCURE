from sqlalchemy import Column, Integer, String, Boolean, Float, Text, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class TenderDocument(Base):
    """Uploaded tender documents (PDF, DOCX, TXT) for procurement audit."""
    __tablename__ = "tender_documents"

    id = Column(Integer, primary_key=True, index=True)
    tender_number = Column(String(100), unique=True, index=True, nullable=True)
    filename = Column(String(255), nullable=False)
    title = Column(String(500), nullable=True)
    organization = Column(String(255), index=True, nullable=True)
    file_type = Column(String(50), nullable=False)  # 'PDF', 'DOCX', 'TXT'
    file_size = Column(Integer, nullable=True)
    raw_text = Column(Text, nullable=True)
    parsed_metadata = Column(JSON, nullable=True)
    status = Column(String(50), default="UPLOADED", index=True, nullable=False)  # UPLOADED, PARSED, AUDITED, FAILED

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    sections = relationship("TenderSection", back_populates="tender", cascade="all, delete-orphan")
    requirements = relationship("TenderRequirement", back_populates="tender", cascade="all, delete-orphan")
    audit_result = relationship("TenderAuditResult", back_populates="tender", uselist=False, cascade="all, delete-orphan")


class TenderSection(Base):
    """Extracted sections/pages of a tender document."""
    __tablename__ = "tender_sections"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tender_documents.id", ondelete="CASCADE"), index=True, nullable=False)
    section_title = Column(String(255), nullable=True)
    section_number = Column(String(50), nullable=True)
    page_number = Column(Integer, nullable=True)
    content = Column(Text, nullable=False)
    section_type = Column(String(100), index=True, nullable=True)  # 'TECHNICAL_SPEC', 'ELIGIBILITY', 'BOQ', 'GENERAL_TERMS'

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    tender = relationship("TenderDocument", back_populates="sections")


class TenderRequirement(Base):
    """Extracted technical clauses and procurement requirements from tender text."""
    __tablename__ = "tender_requirements"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tender_documents.id", ondelete="CASCADE"), index=True, nullable=False)
    section_id = Column(Integer, ForeignKey("tender_sections.id", ondelete="SET NULL"), index=True, nullable=True)
    requirement_text = Column(Text, nullable=False)
    extracted_intent = Column(String(100), index=True, nullable=True)
    product_keywords = Column(JSON, nullable=True)
    technical_attributes = Column(JSON, nullable=True)
    is_mandatory = Column(Boolean, default=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    tender = relationship("TenderDocument", back_populates="requirements")
    section = relationship("TenderSection")


class TenderStandardReference(Base):
    """Explicit standard references identified within tender clauses."""
    __tablename__ = "tender_standard_references"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tender_documents.id", ondelete="CASCADE"), index=True, nullable=False)
    section_id = Column(Integer, ForeignKey("tender_sections.id", ondelete="SET NULL"), index=True, nullable=True)
    requirement_id = Column(Integer, ForeignKey("tender_requirements.id", ondelete="SET NULL"), index=True, nullable=True)
    standard_number_raw = Column(String(100), nullable=False)
    detected_standard_id = Column(Integer, ForeignKey("standards.id", ondelete="SET NULL"), index=True, nullable=True)
    is_valid = Column(Boolean, default=True)
    is_superseded = Column(Boolean, default=False)
    superseded_by_standard_id = Column(Integer, ForeignKey("standards.id", ondelete="SET NULL"), index=True, nullable=True)
    detected_clause = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    tender = relationship("TenderDocument")
    detected_standard = relationship("Standard", foreign_keys=[detected_standard_id])
    superseded_by_standard = relationship("Standard", foreign_keys=[superseded_by_standard_id])


class TenderAuditResult(Base):
    """Auditing result comparing tender clauses against expected standards & gaps."""
    __tablename__ = "tender_audit_results"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tender_documents.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    audit_summary = Column(JSON, nullable=True)
    expected_standards = Column(JSON, nullable=True)
    missing_standards = Column(JSON, nullable=True)
    outdated_standards = Column(JSON, nullable=True)
    testing_gaps = Column(JSON, nullable=True)
    safety_gaps = Column(JSON, nullable=True)
    certification_gaps = Column(JSON, nullable=True)
    coverage_score = Column(Float, nullable=True)
    audit_report = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    tender = relationship("TenderDocument", back_populates="audit_result")
