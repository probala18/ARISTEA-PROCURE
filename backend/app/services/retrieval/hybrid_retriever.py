"""
Backward-compatibility adapter for HybridRetrievalEngine.
Delegates directly to SemanticRetrievalEngine to ensure pure semantic vector retrieval.
"""
from backend.app.services.retrieval.semantic_retriever import (
    SemanticRetrievalEngine,
    SemanticRetrievalResponse,
    RetrievalFilter,
    ScoredRecommendation,
    HybridRetrievalEngine,
    HybridRetrievalResponse,
)

__all__ = [
    "SemanticRetrievalEngine",
    "SemanticRetrievalResponse",
    "RetrievalFilter",
    "ScoredRecommendation",
    "HybridRetrievalEngine",
    "HybridRetrievalResponse",
]
