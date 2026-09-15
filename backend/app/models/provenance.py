from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, func
from backend.app.core.database import Base

class SourceDocument(Base):
    """Tracks document provenance from manifest.json and local files."""
    __tablename__ = "source_documents"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(100), unique=True, index=True, nullable=False)
    filename = Column(String(255), nullable=False)
    standard_number = Column(String(100), index=True, nullable=True)
    revision = Column(String(50), nullable=True)
    source_type = Column(String(50), nullable=False, default="STANDARDS_DOCUMENT")
    source_url = Column(String(500), nullable=True)
    local_path = Column(String(500), nullable=True)
    status = Column(String(50), nullable=True)
    downloaded = Column(Boolean, default=False)
    title = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
