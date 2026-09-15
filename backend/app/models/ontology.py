from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON, UniqueConstraint, func
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class ProcurementOntology(Base):
    """Procurement vocabulary, hierarchy, domains, and terminology."""
    __tablename__ = "procurement_ontology"

    id = Column(Integer, primary_key=True, index=True)
    term = Column(String(255), unique=True, index=True, nullable=False)
    category = Column(String(100), index=True, nullable=True)
    domain = Column(String(100), index=True, nullable=True)
    definition = Column(Text, nullable=True)
    canonical_name = Column(String(255), index=True, nullable=True)
    synonyms = Column(JSON, nullable=True)  # List of synonym phrases
    parent_term_id = Column(Integer, ForeignKey("procurement_ontology.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    parent_term = relationship("ProcurementOntology", remote_side=[id])


class ProcurementAlias(Base):
    """Informal / colloquial product names mapped to canonical standard numbers."""
    __tablename__ = "procurement_aliases"

    id = Column(Integer, primary_key=True, index=True)
    alias = Column(String(255), index=True, nullable=False)
    canonical_standard_number = Column(String(100), index=True, nullable=False)
    standard_id = Column(Integer, ForeignKey("standards.id", ondelete="CASCADE"), index=True, nullable=True)
    product_context = Column(Text, nullable=True)
    confidence = Column(Float, default=1.0, nullable=False)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    standard = relationship("Standard", foreign_keys=[standard_id])

    __table_args__ = (
        UniqueConstraint("alias", "canonical_standard_number", name="uq_procurement_alias_std"),
    )
