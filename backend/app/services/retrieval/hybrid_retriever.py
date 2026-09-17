"""
Hybrid Retrieval Engine for Module 5.
Combines:
- Exact identifier lookup (supporting fast path; respects active metadata filters)
- Pretrained/Semantic vector retrieval
- BM25 lexical keyword search
- Reciprocal Rank Fusion (RRF) & multi-signal reranking
- Metadata filtering (category, department, status, mandatory certification, QCO applicability)
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.models.standard import Standard
from backend.app.services.retrieval.embedding_provider import BaseEmbeddingProvider, get_embedding_provider
from backend.app.services.retrieval.lexical_retriever import BM25Index
from backend.app.services.retrieval.vector_retriever import VectorRetriever
from backend.app.services.retrieval.reranker import MultiSignalReranker, ScoredRecommendation, RerankingWeights
from backend.app.core.normalizers import parse_standard_id


class RetrievalFilter(BaseModel):
    category: Optional[str] = None
    department_id: Optional[int] = None
    status: Optional[str] = "CURRENT"
    is_mandatory_certification: Optional[bool] = None
    qco_applicable: Optional[bool] = None


class HybridRetrievalResponse(BaseModel):
    query: str
    is_exact_match_fast_path: bool = False
    filters_applied: Dict[str, Any] = Field(default_factory=dict)
    total_candidates_evaluated: int = 0
    recommendations: List[ScoredRecommendation] = Field(default_factory=list)
    embedding_model: str


class HybridRetrievalEngine:
    """Core hybrid retrieval engine combining vector, BM25, and metadata constraints."""

    def __init__(
        self,
        session: Session,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
        reranking_weights: Optional[RerankingWeights] = None,
    ):
        self.session = session
        self.provider = embedding_provider or get_embedding_provider()
        self.vector_retriever = VectorRetriever(session, self.provider)
        self.bm25_index = BM25Index()
        self.reranker = MultiSignalReranker(reranking_weights)

        # Build BM25 index over all standards
        stds = self.session.query(Standard).all()
        self.standards = stds
        self.standards_by_id = {s.id: s for s in stds}
        self.bm25_index.build_index(stds)

    def retrieve(
        self,
        query: str,
        filters: Optional[RetrievalFilter] = None,
        top_k: int = 10,
        rrf_k: int = 60,
    ) -> HybridRetrievalResponse:
        """
        Executes hybrid retrieval:
        1. Fast-path check: If query specifies an exact standard number and passes filters.
        2. Vector semantic search (top 30).
        3. BM25 lexical search (top 30).
        4. Reciprocal Rank Fusion (RRF) candidate merge.
        5. Apply metadata filters.
        6. Multi-signal reranking with transparent explainable score breakdown.
        """
        if not query or not query.strip():
            return HybridRetrievalResponse(
                query=query or "",
                recommendations=[],
                embedding_model=self.provider.model_name,
            )

        q_clean = query.strip()
        filter_dict = (filters.model_dump(exclude_none=True) if hasattr(filters, "model_dump") else filters.dict(exclude_none=True)) if filters else {}

        # 1. Fast-Path Exact Lookup (Must strictly respect active metadata filters)
        parsed = parse_standard_id(q_clean)
        if parsed:
            cid = parsed["canonical_id"].upper()
            is_num = parsed["is_number"].upper()

            for s in self.standards:
                if s.standard_id.strip().upper() == cid or s.is_number.strip().upper() == is_num:
                    if self._matches_filter(s, filters):
                        # Construct top recommendation for exact match
                        rec = ScoredRecommendation(
                            id=s.id,
                            standard_id=s.standard_id,
                            is_number=s.is_number,
                            title=s.title,
                            category=s.category,
                            status=s.status,
                            relevance_score=1.0,
                            rank=1,
                            signals={
                                "semantic_similarity": 1.0,
                                "bm25_score": 1.0,
                                "id_match": 1.0,
                                "category_match": 1.0,
                                "status_support": 1.0,
                            },
                            explanation=f"Exact identifier match for '{q_clean}' on {s.standard_id} (Filter matched).",
                        )
                        return HybridRetrievalResponse(
                            query=query,
                            is_exact_match_fast_path=True,
                            filters_applied=filter_dict,
                            total_candidates_evaluated=1,
                            recommendations=[rec],
                            embedding_model=self.provider.model_name,
                        )

        # 2. Vector Semantic Retrieval
        vector_results = self.vector_retriever.search(q_clean, top_k=30)

        # 3. BM25 Lexical Retrieval
        bm25_results = self.bm25_index.search(q_clean, top_k=30)

        # 4. Reciprocal Rank Fusion (RRF) Merge
        rrf_scores: Dict[int, float] = {}
        merged_candidates: Dict[int, Dict[str, Any]] = {}

        for item in vector_results:
            std_id = item["id"]
            rank = item["vector_rank"]
            rrf_scores[std_id] = rrf_scores.get(std_id, 0.0) + (1.0 / (rrf_k + rank))
            merged_candidates[std_id] = item.copy()

        for item in bm25_results:
            std_id = item["id"]
            rank = item["rank"]
            rrf_scores[std_id] = rrf_scores.get(std_id, 0.0) + (1.0 / (rrf_k + rank))
            if std_id in merged_candidates:
                merged_candidates[std_id]["bm25_score"] = item["bm25_score"]
                merged_candidates[std_id]["bm25_raw_score"] = item["bm25_raw_score"]
            else:
                merged_candidates[std_id] = item.copy()

        # 5. Apply Metadata Filtering
        filtered_candidates = []
        for std_id, cand in merged_candidates.items():
            std = self.standards_by_id.get(std_id)
            if not std:
                continue

            if not self._matches_filter(std, filters):
                continue

            # Add RRF score
            cand["rrf_score"] = rrf_scores.get(std_id, 0.0)
            filtered_candidates.append(cand)

        # 6. Multi-Signal Reranking
        final_recommendations = self.reranker.rerank(
            query=q_clean,
            candidates=filtered_candidates,
            top_k=top_k,
        )

        return HybridRetrievalResponse(
            query=query,
            is_exact_match_fast_path=False,
            filters_applied=filter_dict,
            total_candidates_evaluated=len(filtered_candidates),
            recommendations=final_recommendations,
            embedding_model=self.provider.model_name,
        )

    def _matches_filter(self, std: Standard, filters: Optional[RetrievalFilter]) -> bool:
        if not filters:
            return True
        if filters.status and std.status != filters.status:
            return False
        if filters.category and (not std.category or filters.category.lower() not in std.category.lower()):
            return False
        if filters.department_id is not None and std.department_id != filters.department_id:
            return False
        if filters.is_mandatory_certification is not None and std.is_mandatory_certification != filters.is_mandatory_certification:
            return False
        if filters.qco_applicable is not None and std.qco_applicable != filters.qco_applicable:
            return False
        return True
