"""
Retrieval Package Init for Module 5.
Exports Embedding Providers, BM25 Index, Vector Retriever, Reranker, and Hybrid Engine.
"""
from backend.app.services.retrieval.embedding_provider import (
    BaseEmbeddingProvider,
    DeterministicSemanticEmbeddingProvider,
    SentenceTransformerEmbeddingProvider,
    EmbeddingTextBuilder,
    get_embedding_provider,
)
from backend.app.services.retrieval.lexical_retriever import BM25Index
from backend.app.services.retrieval.vector_retriever import VectorRetriever
from backend.app.services.retrieval.reranker import (
    MultiSignalReranker,
    RerankingWeights,
    ScoredRecommendation,
)
from backend.app.services.retrieval.hybrid_retriever import (
    HybridRetrievalEngine,
    RetrievalFilter,
    HybridRetrievalResponse,
)

__all__ = [
    "BaseEmbeddingProvider",
    "DeterministicSemanticEmbeddingProvider",
    "SentenceTransformerEmbeddingProvider",
    "EmbeddingTextBuilder",
    "get_embedding_provider",
    "BM25Index",
    "VectorRetriever",
    "MultiSignalReranker",
    "RerankingWeights",
    "ScoredRecommendation",
    "HybridRetrievalEngine",
    "RetrievalFilter",
    "HybridRetrievalResponse",
]
