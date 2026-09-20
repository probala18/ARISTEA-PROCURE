"""
Semantic Retrieval Engine for ARISTEA-PROCURE (PS 26108).
Uses pretrained Sentence Transformers dense vector embeddings and cosine similarity
as the sole relevance mechanism for natural-language procurement queries.

Architecture:
  User Procurement Query
          ↓
  Requirement Understanding / Normalization
          ↓
  Sentence Transformer Model (paraphrase-multilingual-MiniLM-L12-v2)
          ↓
  Query Embedding (384-dim unit-normalized)
          ↓
  Vector Similarity Search (Cosine Similarity)
          ↓
  Top-K Semantically Relevant Standards
          ↓
  Deterministic Metadata Filtering (Status, Category)
"""
import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.models.standard import Standard
from backend.app.services.retrieval.embedding_provider import BaseEmbeddingProvider, get_embedding_provider
from backend.app.services.retrieval.vector_retriever import VectorRetriever
from backend.app.core.normalizers import parse_standard_id


class RetrievalFilter(BaseModel):
    """Deterministic metadata filters. Never alters semantic similarity scores."""
    category: Optional[str] = None
    department_id: Optional[int] = None
    status: Optional[str] = None
    is_mandatory_certification: Optional[bool] = None
    qco_applicable: Optional[bool] = None


class ScoredRecommendation(BaseModel):
    """Recommendation item ranked solely by semantic vector similarity."""
    id: int
    standard_id: str
    is_number: str
    title: str
    category: Optional[str] = None
    status: Optional[str] = None
    relevance_score: float
    rank: int
    signals: Dict[str, float] = Field(default_factory=dict)
    explanation: str


class SemanticRetrievalResponse(BaseModel):
    """Response from SemanticRetrievalEngine."""
    query: str
    is_exact_match_fast_path: bool = False
    filters_applied: Dict[str, Any] = Field(default_factory=dict)
    total_candidates_evaluated: int = 0
    recommendations: List[ScoredRecommendation] = Field(default_factory=list)
    embedding_model: str


# Backward-compatibility alias for previous API references
HybridRetrievalResponse = SemanticRetrievalResponse


class SemanticRetrievalEngine:
    """
    Core semantic retrieval engine.
    Uses dense vector similarity as the sole relevance/ranking signal for natural-language queries.
    Deterministic direct lookup is maintained exclusively for canonical standard identifiers.
    """

    def __init__(
        self,
        session: Session,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
    ):
        self.session = session
        self.provider = embedding_provider or get_embedding_provider()
        self.vector_retriever = VectorRetriever(session, self.provider)

        stds = self.session.query(Standard).all()
        self.standards = stds
        self.standards_by_id = {s.id: s for s in stds}

    def _matches_filter(self, std: Standard, filters: Optional[RetrievalFilter]) -> bool:
        """Applies deterministic metadata constraints without altering relevance scores."""
        if not filters:
            return True

        if filters.category and std.category:
            if filters.category.lower() not in std.category.lower():
                return False

        if filters.department_id and std.department_id:
            if std.department_id != filters.department_id:
                return False

        if filters.status and std.status:
            if filters.status.upper() != std.status.upper():
                return False

        if filters.is_mandatory_certification is not None:
            if bool(std.is_mandatory) != filters.is_mandatory_certification:
                return False

        if filters.qco_applicable is not None:
            has_qco = bool(getattr(std, "qco_orders", None))
            if has_qco != filters.qco_applicable:
                return False

        return True

    def retrieve(
        self,
        query: str,
        filters: Optional[RetrievalFilter] = None,
        top_k: int = 10,
    ) -> SemanticRetrievalResponse:
        """
        Executes semantic retrieval:
        1. Deterministic Fast-Path: If query specifies an exact standard identifier and passes filters.
        2. Vector Semantic Search: Cosine similarity over 384-dimensional dense embeddings.
        3. Deterministic Metadata Filtering: Excludes non-matching records without lexical weighting.
        4. Pure Semantic Ranking: Results ranked strictly by vector cosine similarity.
        """
        if not query or not query.strip():
            return SemanticRetrievalResponse(
                query=query or "",
                recommendations=[],
                embedding_model=self.provider.model_name,
            )

        q_clean = query.strip()
        filter_dict = (
            filters.model_dump(exclude_none=True)
            if hasattr(filters, "model_dump")
            else filters.dict(exclude_none=True)
        ) if filters else {}

        # 1. Deterministic Direct Lookup for queries specifying or containing a standard identifier
        # (Must strictly respect active metadata filters)
        matched_exact_std = None
        is_exact_query = False

        # First check if query is strictly an exact standard identifier
        parsed = parse_standard_id(q_clean)
        if parsed and parsed.get("number"):
            cid = (parsed.get("canonical_id") or "").upper()
            is_num = (parsed.get("is_number") or "").upper()
            for s in self.standards:
                if s.standard_id.strip().upper() == cid or s.is_number.strip().upper() == is_num:
                    if self._matches_filter(s, filters):
                        matched_exact_std = s
                        is_exact_query = True
                        break

        # If not an exact query string, check if natural language query mentions an explicit standard identifier
        if not matched_exact_std:
            std_mentions = re.findall(
                r'\b(?:IS(?:\s*/\s*(?:IEC|ISO))?\s*\d+(?:\s*\([^\)]+\))?(?::\d{4})?|\bIS\d{2,6})\b',
                q_clean,
                re.IGNORECASE,
            )
            for m in std_mentions:
                p_mention = parse_standard_id(m)
                if p_mention and p_mention.get("number"):
                    cid_m = (p_mention.get("canonical_id") or "").upper()
                    is_num_m = (p_mention.get("is_number") or "").upper()
                    for s in self.standards:
                        if s.standard_id.strip().upper() == cid_m or s.is_number.strip().upper() == is_num_m:
                            if self._matches_filter(s, filters):
                                matched_exact_std = s
                                break
                if matched_exact_std:
                    break

        # If exact query, return fast-path single response
        if matched_exact_std and is_exact_query:
            rec = ScoredRecommendation(
                id=matched_exact_std.id,
                standard_id=matched_exact_std.standard_id,
                is_number=matched_exact_std.is_number,
                title=matched_exact_std.title,
                category=matched_exact_std.category,
                status=matched_exact_std.status,
                relevance_score=1.0,
                rank=1,
                signals={
                    "semantic_similarity": 1.0,
                    "id_match": 1.0,
                    "status_support": 1.0,
                },
                explanation=f"Exact standard identifier direct lookup for '{q_clean}' on {matched_exact_std.standard_id} (Filter matched).",
            )
            return SemanticRetrievalResponse(
                query=query,
                is_exact_match_fast_path=True,
                filters_applied=filter_dict,
                total_candidates_evaluated=1,
                recommendations=[rec],
                embedding_model=self.provider.model_name,
            )

        # 2. Vector Semantic Retrieval (Dense Embedding Cosine Similarity)
        # Retrieve candidates based purely on semantic understanding
        vector_results = self.vector_retriever.search(q_clean, top_k=max(top_k * 3, 30))

        # 3. Deterministic Metadata Filtering & Direct Semantic Score Assignment
        filtered_candidates: List[ScoredRecommendation] = []
        seen_ids = set()

        if matched_exact_std:
            seen_ids.add(matched_exact_std.id)
            filtered_candidates.append(
                ScoredRecommendation(
                    id=matched_exact_std.id,
                    standard_id=matched_exact_std.standard_id,
                    is_number=matched_exact_std.is_number,
                    title=matched_exact_std.title,
                    category=matched_exact_std.category,
                    status=matched_exact_std.status,
                    relevance_score=1.0,
                    rank=1,
                    signals={
                        "semantic_similarity": 1.0,
                        "id_match": 1.0,
                        "status_support": 1.0,
                    },
                    explanation=f"Direct lookup for standard identifier '{matched_exact_std.standard_id}' mentioned in query (Filter matched).",
                )
            )

        for rank_idx, item in enumerate(vector_results):
            if item["id"] in seen_ids:
                continue

            std = self.standards_by_id.get(item["id"])
            if not std:
                continue

            if not self._matches_filter(std, filters):
                continue

            # Vector cosine similarity is the ONLY relevance signal
            sim_score = max(0.0, min(1.0, float(item.get("vector_similarity", 0.0))))
            seen_ids.add(std.id)

            rec = ScoredRecommendation(
                id=std.id,
                standard_id=std.standard_id,
                is_number=std.is_number,
                title=std.title,
                category=std.category,
                status=std.status,
                relevance_score=round(sim_score, 4),
                rank=len(filtered_candidates) + 1,
                signals={
                    "semantic_similarity": round(sim_score, 4),
                    "status_support": 1.0 if std.status == "CURRENT" else 0.5,
                },
                explanation=f"Dense semantic vector similarity: {sim_score:.2f} (Model: {self.provider.model_name})",
            )
            filtered_candidates.append(rec)

            if len(filtered_candidates) >= top_k:
                break

        return SemanticRetrievalResponse(
            query=query,
            is_exact_match_fast_path=False,
            filters_applied=filter_dict,
            total_candidates_evaluated=len(vector_results) + (1 if matched_exact_std else 0),
            recommendations=filtered_candidates,
            embedding_model=self.provider.model_name,
        )


# Backward-compatibility alias
HybridRetrievalEngine = SemanticRetrievalEngine
