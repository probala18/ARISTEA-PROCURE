from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from backend.app.core.database import Base, PGVectorType

class Standard(Base):
    """Core Indian Standard entity merging standards.csv and sample_standards.json with provenance."""
    __tablename__ = "standards"

    id = Column(Integer, primary_key=True, index=True)
    standard_id = Column(String(100), unique=True, index=True, nullable=False)  # e.g., 'IS 694:2010'
    is_number = Column(String(100), index=True, nullable=False)  # e.g., 'IS 694'
    part = Column(String(50), nullable=True)
    section = Column(String(50), nullable=True)
    title = Column(Text, nullable=False)
    scope = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), index=True, nullable=True)  # Electrical, Civil, etc.
    subject_area = Column(String(100), index=True, nullable=True)
    division = Column(String(100), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), index=True, nullable=True)
    technical_committee = Column(String(100), index=True, nullable=True)
    publication_year = Column(Integer, index=True, nullable=True)
    latest_year = Column(Integer, nullable=True)
    status = Column(String(50), default="CURRENT", index=True, nullable=False)  # CURRENT, SUPERSEDED, etc.
    supersedes = Column(String(255), nullable=True)
    certification_scheme = Column(String(255), nullable=True)
    is_mandatory_certification = Column(Boolean, index=True, nullable=True)
    qco_applicable = Column(Boolean, index=True, nullable=True)
    qco_reference = Column(Text, nullable=True)
    keywords = Column(JSON, nullable=True)
    source_document_id = Column(Integer, ForeignKey("source_documents.id", ondelete="SET NULL"), index=True, nullable=True)
    source_file = Column(String(100), nullable=False)
    source_provenance = Column(JSON, nullable=True)
    
    # 384-dimensional vector embedding for multilingual semantic retrieval
    embedding = Column(PGVectorType(384), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    department = relationship("Department", foreign_keys=[department_id])
    source_document = relationship("SourceDocument", foreign_keys=[source_document_id])
