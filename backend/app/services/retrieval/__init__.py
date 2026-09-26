"""
Retrieval Package Init for ARISTEA-PROCURE.
Exports Embedding Providers, Vector Retriever, and Semantic Retrieval Engine.
"""
from backend.app.services.retrieval.embedding_provider import (
    BaseEmbeddingProvider,
    DeterministicSemanticEmbeddingProvider,
    SentenceTransformerEmbeddingProvider,
    ONNXEmbeddingProvider,
    EmbeddingTextBuilder,
    get_embedding_provider,
)
from backend.app.services.retrieval.vector_retriever import VectorRetriever
from backend.app.services.retrieval.semantic_retriever import (
    SemanticRetrievalEngine,
    SemanticRetrievalResponse,
    RetrievalFilter,
    ScoredRecommendation,
    HybridRetrievalEngine,
    HybridRetrievalResponse,
)

__all__ = [
    "BaseEmbeddingProvider",
    "DeterministicSemanticEmbeddingProvider",
    "SentenceTransformerEmbeddingProvider",
    "ONNXEmbeddingProvider",
    "EmbeddingTextBuilder",
    "get_embedding_provider",
    "VectorRetriever",
    "SemanticRetrievalEngine",
    "SemanticRetrievalResponse",
    "RetrievalFilter",
    "ScoredRecommendation",
    "HybridRetrievalEngine",
    "HybridRetrievalResponse",
]
