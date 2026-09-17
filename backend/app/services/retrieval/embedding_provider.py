"""
Embedding Provider Abstraction for Module 5.
Supports 384-dimensional vector embeddings for Indian Standards and search queries.

Architectural Rule:
The pretrained embedding provider is the primary semantic retrieval mechanism.
The deterministic embedding provider is strictly an offline/testing fallback and
must never be presented as equivalent to pretrained semantic embeddings.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import os
import logging
import hashlib
import numpy as np

logger = logging.getLogger("retrieval.embedding")


class EmbeddingTextBuilder:
    """Constructs canonical domain embedding text from standard fields and relationships."""

    @staticmethod
    def build_standard_embedding_text(standard: Any) -> str:
        """
        Builds rich embedding text from:
        - standard number & canonical ID
        - title
        - scope
        - description
        - category & subject area
        - keywords
        - relationships (normative refs, testing, safety, supersedes)
        Strictly excludes any fabricated information.
        """
        parts = []

        std_num = getattr(standard, "is_number", "") or ""
        std_id = getattr(standard, "standard_id", "") or ""
        title = getattr(standard, "title", "") or ""
        category = getattr(standard, "category", "") or ""
        subject = getattr(standard, "subject_area", "") or ""
        scope = getattr(standard, "scope", "") or ""
        description = getattr(standard, "description", "") or ""
        keywords = getattr(standard, "keywords", None) or []
        supersedes = getattr(standard, "supersedes", "") or ""

        if std_id:
            parts.append(f"Standard ID: {std_id}")
        if std_num and std_num != std_id:
            parts.append(f"IS Number: {std_num}")
        if title:
            parts.append(f"Title: {title}")
        if category:
            parts.append(f"Category: {category}")
        if subject:
            parts.append(f"Subject Area: {subject}")
        if scope:
            parts.append(f"Scope: {scope}")
        if description and description != scope:
            parts.append(f"Description: {description}")
        if keywords:
            if isinstance(keywords, list):
                parts.append(f"Keywords: {', '.join(keywords)}")
            else:
                parts.append(f"Keywords: {str(keywords)}")
        if supersedes:
            parts.append(f"Supersedes: {supersedes}")

        return " | ".join(parts)


class BaseEmbeddingProvider(ABC):
    """Abstract interface for 384-dimensional embedding models."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Embedding vector dimension (fixed to 384)."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Human-readable identifier of the embedding model."""
        pass

    @property
    @abstractmethod
    def is_pretrained(self) -> bool:
        """True for real neural pretrained models; False for offline testing fallbacks."""
        pass

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Embeds a single search query."""
        pass

    @abstractmethod
    def embed_standard(self, standard: Any) -> List[float]:
        """Embeds a standard entity using canonical text construction."""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Batch embeds multiple texts."""
        pass


class DeterministicSemanticEmbeddingProvider(BaseEmbeddingProvider):
    """
    Offline/testing fallback provider.
    Generates deterministic 384-dimensional unit-normalized vectors using feature hashing
    and character n-gram projections.
    IMPORTANT: This is strictly an offline fallback and not equivalent to pretrained embeddings.
    """

    def __init__(self, dimension: int = 384):
        self._dim = dimension

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def model_name(self) -> str:
        return "deterministic-offline-fallback-384d"

    @property
    def is_pretrained(self) -> bool:
        return False

    def embed_query(self, text: str) -> List[float]:
        return self._vectorize(text)

    def embed_standard(self, standard: Any) -> List[float]:
        text = EmbeddingTextBuilder.build_standard_embedding_text(standard)
        return self._vectorize(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self._vectorize(t) for t in texts]

    def _vectorize(self, text: str) -> List[float]:
        if not text or not text.strip():
            # Zero vector normalized to unit length along first dimension
            v = np.zeros(self._dim, dtype=np.float32)
            v[0] = 1.0
            return v.tolist()

        vec = np.zeros(self._dim, dtype=np.float32)
        tokens = text.lower().replace("|", " ").replace(":", " ").replace("-", " ").split()

        for token in tokens:
            # Word-level hash projection
            h = int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16)
            idx = h % self._dim
            sign = 1.0 if ((h >> 8) % 2 == 0) else -1.0
            vec[idx] += sign * 1.5

            # Character 3-gram projections for morphological/partial matching
            if len(token) >= 3:
                for i in range(len(token) - 2):
                    ngram = token[i:i+3]
                    h_ng = int(hashlib.md5(ngram.encode("utf-8")).hexdigest(), 16)
                    idx_ng = h_ng % self._dim
                    sign_ng = 1.0 if ((h_ng >> 4) % 2 == 0) else -1.0
                    vec[idx_ng] += sign_ng * 0.5

        # L2 Unit Normalization
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        else:
            vec[0] = 1.0

        return vec.tolist()


class SentenceTransformerEmbeddingProvider(BaseEmbeddingProvider):
    """
    Primary semantic retrieval provider using pretrained SentenceTransformer models
    (e.g., 'all-MiniLM-L6-v2' or 'paraphrase-multilingual-MiniLM-L12-v2', producing 384-dim vectors).
    """

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self._model_name = model_name
        self._model = None
        self._load_model()

    def _load_model(self):
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)
            logger.info(f"Loaded pretrained embedding model: {self._model_name}")
        except Exception as e:
            logger.warning(f"Failed to load SentenceTransformer ({e}). Pretrained provider unavailable.")
            self._model = None

    @property
    def dimension(self) -> int:
        return 384

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def is_pretrained(self) -> bool:
        return True

    def embed_query(self, text: str) -> List[float]:
        if not self._model:
            raise RuntimeError("SentenceTransformer model is not loaded.")
        emb = self._model.encode(text, normalize_embeddings=True)
        return emb.tolist()

    def embed_standard(self, standard: Any) -> List[float]:
        text = EmbeddingTextBuilder.build_standard_embedding_text(standard)
        return self.embed_query(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not self._model:
            raise RuntimeError("SentenceTransformer model is not loaded.")
        embs = self._model.encode(texts, batch_size=32, normalize_embeddings=True)
        return [e.tolist() for e in embs]


def get_embedding_provider(prefer_pretrained: bool = True) -> BaseEmbeddingProvider:
    """
    Factory to retrieve embedding provider.
    Attempts pretrained SentenceTransformer first if prefer_pretrained is True and available;
    falls back cleanly to DeterministicSemanticEmbeddingProvider.
    """
    if prefer_pretrained:
        try:
            import sentence_transformers
            provider = SentenceTransformerEmbeddingProvider()
            if provider._model is not None:
                return provider
        except Exception:
            pass

    return DeterministicSemanticEmbeddingProvider()
