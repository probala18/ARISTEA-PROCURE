from sqlalchemy import Column, Integer, String, Boolean, Float, Text, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class EvaluationQuery(Base):
    """Benchmark test queries imported from query_dataset.json."""
    __tablename__ = "evaluation_queries"

    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(String(50), unique=True, index=True, nullable=False)  # 'Q01', 'Q02', etc.
    query_text = Column(Text, nullable=False)
    category = Column(String(100), index=True, nullable=True)
    expected_intent = Column(String(100), index=True, nullable=False)
    clarification_expected = Column(Boolean, default=False)
    expected_retrieval_operations = Column(JSON, nullable=True)
    expected_evidence = Column(Text, nullable=True)
    answerable_with_current_data = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    results = relationship("EvaluationResult", back_populates="query", cascade="all, delete-orphan")


class EvaluationResult(Base):
    """Actual performance metrics logged during evaluation runs."""
    __tablename__ = "evaluation_results"

    id = Column(Integer, primary_key=True, index=True)
    evaluation_query_id = Column(Integer, ForeignKey("evaluation_queries.id", ondelete="CASCADE"), index=True, nullable=False)
    test_run_id = Column(String(100), index=True, nullable=False)
    actual_intent = Column(String(100), nullable=True)
    actual_retrieved_standards = Column(JSON, nullable=True)
    precision_at_1 = Column(Float, nullable=True)
    precision_at_3 = Column(Float, nullable=True)
    recall_at_5 = Column(Float, nullable=True)
    mrr = Column(Float, nullable=True)
    latency_ms = Column(Float, nullable=True)
    pass_fail = Column(Boolean, default=True)
    error_details = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    query = relationship("EvaluationQuery", back_populates="results")
