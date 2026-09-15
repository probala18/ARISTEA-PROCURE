from sqlalchemy import Column, Integer, String, Boolean, Float, Text, DateTime, ForeignKey, JSON, UniqueConstraint, func
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class StandardRelationship(Base):
    """Stores connections between Indian Standards with explicit vs derived separation."""
    __tablename__ = "standard_relationships"

    id = Column(Integer, primary_key=True, index=True)
    source_standard_id = Column(Integer, ForeignKey("standards.id", ondelete="CASCADE"), index=True, nullable=False)
    target_standard_id = Column(Integer, ForeignKey("standards.id", ondelete="SET NULL"), index=True, nullable=True)
    source_standard_number = Column(String(100), index=True, nullable=True)
    target_standard_number = Column(String(100), index=True, nullable=False)
    target_standard_title = Column(Text, nullable=True)
    
    # Relationship type: NORMATIVE_REFERENCE, TESTING, SAFETY, PERFORMANCE, INSTALLATION,
    # TERMINOLOGY, RELATED_PRODUCT, SUBCOMPONENT, SUPERSEDES, ALLIED, APPLICATION, OTHER
    relationship_type = Column(String(100), index=True, nullable=False)
    relationship_category = Column(String(100), index=True, nullable=True)  # e.g., 'testing_standards', 'safety_standards'
    relationship_description = Column(Text, nullable=True)
    confidence = Column(Float, default=1.0, nullable=False)
    
    # Explicit vs derived separation
    is_explicit_source = Column(Boolean, default=True, index=True, nullable=False)  # True = relationships.json, False = derived
    source_dataset = Column(String(100), nullable=False)  # 'relationships.json', 'sample_standards.json', 'standards.csv'
    source_provenance = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    source_standard = relationship("Standard", foreign_keys=[source_standard_id])
    target_standard = relationship("Standard", foreign_keys=[target_standard_id])

    __table_args__ = (
        UniqueConstraint("source_standard_id", "target_standard_number", "relationship_type", "is_explicit_source", name="uq_std_rel_source_target_type_explicit"),
    )
