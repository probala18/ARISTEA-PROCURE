"""
Vector Semantic Retriever for Module 5.
Computes cosine similarity over 384-dimensional standard vectors.
"""
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from sqlalchemy.orm import Session

from backend.app.models.standard import Standard
from backend.app.services.retrieval.embedding_provider import (
    BaseEmbeddingProvider,
    EmbeddingTextBuilder,
    get_embedding_provider,
)

logger = logging.getLogger("retrieval.vector")


class VectorRetriever:
    """Vector semantic similarity retriever over 384-dimensional standard embeddings."""

    _cached_indexed_ids: Optional[np.ndarray] = None
    _cached_matrix: Optional[np.ndarray] = None

    def __init__(self, session: Session, embedding_provider: Optional[BaseEmbeddingProvider] = None):
        self.session = session
        self.provider = embedding_provider or get_embedding_provider()
        self._load_vector_index()

    def _load_vector_index(self):
        """Loads all standard vectors into memory for fast cosine ranking."""
        stds = self.session.query(Standard).all()
        self.standards = stds
        self.standard_map = {s.id: s for s in stds}

        # Reuse pre-computed matrix if available for the same standard count
        if (
            VectorRetriever._cached_matrix is not None
            and VectorRetriever._cached_indexed_ids is not None
            and len(VectorRetriever._cached_indexed_ids) == len(stds)
        ):
            self.indexed_ids = VectorRetriever._cached_indexed_ids
            self.matrix = VectorRetriever._cached_matrix
            return

        valid_ids = []
        vectors = []

        for s in stds:
            vec = s.embedding
            if vec is None or len(vec) != self.provider.dimension:
                # Dynamically generate vector if not yet persisted in database
                vec = self.provider.embed_standard(s)

            valid_ids.append(s.id)
            vectors.append(vec)

        # Guard against stored vectors produced by a different model (e.g. the offline
        # fallback): mixing vector spaces makes cosine ranking effectively random.
        if vectors and self.provider.is_pretrained and not self._stored_vectors_match(stds[0], vectors[0]):
            logger.warning(
                "Stored standard embeddings do not match %s; re-embedding in memory. "
                "Run scripts/generate_embeddings.py --force to persist.",
                self.provider.model_name,
            )
            texts = [EmbeddingTextBuilder.build_standard_embedding_text(s) for s in stds]
            vectors = self.provider.embed_batch(texts)

        self.indexed_ids = np.array(valid_ids, dtype=np.int64)
        if vectors:
            self.matrix = np.array(vectors, dtype=np.float32)
            # Ensure unit normalization for fast dot-product cosine similarity
            norms = np.linalg.norm(self.matrix, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            self.matrix = self.matrix / norms
        else:
            self.matrix = np.empty((0, self.provider.dimension), dtype=np.float32)

        VectorRetriever._cached_indexed_ids = self.indexed_ids
        VectorRetriever._cached_matrix = self.matrix

    def _stored_vectors_match(self, standard: Standard, stored_vec) -> bool:
        fresh = np.array(self.provider.embed_standard(standard), dtype=np.float32)
        stored = np.array(stored_vec, dtype=np.float32)
        denom = float(np.linalg.norm(fresh) * np.linalg.norm(stored)) or 1.0
        return float(np.dot(fresh, stored)) / denom > 0.95

    def search(self, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        """Vector semantic search using cosine similarity."""
        if not query or len(self.indexed_ids) == 0:
            return []

        q_vec = np.array(self.provider.embed_query(query), dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 0:
            q_vec = q_vec / q_norm

        # Cosine similarities = dot product of normalized vectors
        sims = np.dot(self.matrix, q_vec)

        top_indices = np.argsort(sims)[::-1][:top_k]

        results = []
        for rank, idx in enumerate(top_indices):
            score = float(sims[idx])
            std_id = int(self.indexed_ids[idx])
            std = self.standard_map.get(std_id)
            if not std:
                continue

            results.append({
                "id": std.id,
                "standard_id": std.standard_id,
                "is_number": std.is_number,
                "title": std.title,
                "category": std.category,
                "status": std.status,
                "vector_similarity": score,
                "vector_rank": rank + 1,
            })

        return results
