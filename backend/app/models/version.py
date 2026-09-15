from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class StandardVersion(Base):
    """Tracks version history, amendments, and supersession facts."""
    __tablename__ = "standard_versions"

    id = Column(Integer, primary_key=True, index=True)
    standard_id = Column(Integer, ForeignKey("standards.id", ondelete="CASCADE"), index=True, nullable=False)
    is_number = Column(String(100), index=True, nullable=False)
    version_year = Column(Integer, nullable=True)
    latest_year = Column(Integer, nullable=True)
    amendment_number = Column(Integer, nullable=True)
    amendment_year = Column(Integer, nullable=True)
    change_description = Column(Text, nullable=True)
    current_state = Column(String(50), default="CURRENT", index=True, nullable=False)  # CURRENT, REVISED, SUPERSEDED, OBSOLETE
    superseded_by = Column(String(100), nullable=True)
    superseded_state = Column(Boolean, default=False, index=True)
    effective_date = Column(String(100), nullable=True)
    source_dataset = Column(String(100), nullable=False)  # 'sample_standards.json', 'standards.csv'
    source_provenance = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    standard = relationship("Standard", foreign_keys=[standard_id])
