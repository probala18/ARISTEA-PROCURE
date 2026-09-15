from sqlalchemy import Column, Integer, String, Boolean, Float, Text, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class AnalysisSession(Base):
    """User interaction sessions for text, voice queries, tender checks, and multi-turn chat."""
    __tablename__ = "analysis_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    session_type = Column(String(50), nullable=False, index=True)  # TEXT_SEARCH, VOICE_QUERY, TENDER_ANALYSIS, CHAT
    user_input = Column(Text, nullable=False)
    detected_language = Column(String(20), default="en", nullable=False)
    intent = Column(String(100), index=True, nullable=True)
    ambiguity_flag = Column(Boolean, default=False)
    clarification_prompt = Column(Text, nullable=True)
    conversation_context = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    requirements = relationship("AnalysisRequirement", back_populates="session", cascade="all, delete-orphan")
    recommendations = relationship("RecommendationResult", back_populates="session", cascade="all, delete-orphan")


class AnalysisRequirement(Base):
    """Normalized requirements extracted from procurement input."""
    __tablename__ = "analysis_requirements"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("analysis_sessions.id", ondelete="CASCADE"), index=True, nullable=False)
    requirement_type = Column(String(100), index=True, nullable=False)  # PRODUCT, VOLTAGE, APPLICATION, MATERIAL, etc.
    extracted_key = Column(String(100), nullable=False)
    extracted_value = Column(Text, nullable=False)
    confidence = Column(Float, default=1.0, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    session = relationship("AnalysisSession", back_populates="requirements")


class RecommendationResult(Base):
    """Ranked standard recommendations with explainability, confidence, and grounding evidence."""
    __tablename__ = "recommendation_results"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("analysis_sessions.id", ondelete="CASCADE"), index=True, nullable=False)
    primary_standard_id = Column(Integer, ForeignKey("standards.id", ondelete="SET NULL"), index=True, nullable=True)
    primary_standard_number = Column(String(100), nullable=False, index=True)
    relevance_score = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=False)
    explanation = Column(Text, nullable=True)
    evidence_summary = Column(JSON, nullable=True)
    matched_requirements = Column(JSON, nullable=True)
    rank = Column(Integer, default=1, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    session = relationship("AnalysisSession", back_populates="recommendations")
    primary_standard = relationship("Standard", foreign_keys=[primary_standard_id])


class GeneratedSpecification(Base):
    """Tender specifications and compliance checklists grounded in Indian Standards."""
    __tablename__ = "generated_specifications"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("analysis_sessions.id", ondelete="SET NULL"), index=True, nullable=True)
    tender_id = Column(Integer, ForeignKey("tender_documents.id", ondelete="SET NULL"), index=True, nullable=True)
    standard_id = Column(Integer, ForeignKey("standards.id", ondelete="SET NULL"), index=True, nullable=True)
    spec_type = Column(String(100), index=True, nullable=False)  # TENDER_CLAUSE, TECHNICAL_SPECIFICATION, COMPLIANCE_CHECKLIST, CORRECTIVE_CLAUSE
    content = Column(Text, nullable=False)
    grounding_evidence = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    session = relationship("AnalysisSession")
    tender = relationship("TenderDocument")
    standard = relationship("Standard", foreign_keys=[standard_id])
