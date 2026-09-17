"""
Multi-Signal Reranker for Module 5.
Combines:
- semantic_similarity (from vector search)
- lexical_score (from BM25)
- exact_id_match
- category_match
- current_status_support
into a transparent, explainable relevance_score (0.0 to 1.0).
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class RerankingWeights(BaseModel):
    weight_semantic: float = 0.40
    weight_lexical: float = 0.35
    weight_id_match: float = 0.15
    weight_category: float = 0.05
    weight_status: float = 0.05


class ScoredRecommendation(BaseModel):
    id: int
    standard_id: str
    is_number: str
    title: str
    category: Optional[str] = None
    status: str = "CURRENT"
    relevance_score: float
    rank: int
    signals: Dict[str, float] = Field(default_factory=dict)
    explanation: str


class MultiSignalReranker:
    """Transparent multi-signal reranker providing auditable relevance scores."""

    def __init__(self, weights: Optional[RerankingWeights] = None):
        self.weights = weights or RerankingWeights()

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 10,
    ) -> List[ScoredRecommendation]:
        """Calculates transparent relevance scores and produces explainable candidate ranking."""
        if not candidates:
            return []

        q_lower = query.lower()
        scored: List[ScoredRecommendation] = []

        for item in candidates:
            std_id = item.get("standard_id", "")
            is_num = item.get("is_number", "")
            title = item.get("title", "")
            category = item.get("category", "") or ""
            status = item.get("status", "CURRENT")

            # 1. Semantic similarity signal (0..1)
            semantic_sim = float(item.get("vector_similarity", 0.0))
            # Clamp negative similarities to 0
            semantic_sim = max(0.0, min(1.0, semantic_sim))

            # 2. Lexical BM25 signal (0..1)
            bm25_score = float(item.get("bm25_score", 0.0))
            bm25_score = max(0.0, min(1.0, bm25_score))

            # 3. Exact ID / token match signal (0..1)
            id_match = 0.0
            is_num_clean = is_num.lower().replace(" ", "")
            std_id_clean = std_id.lower().replace(" ", "")
            q_clean = q_lower.replace(" ", "")
            if is_num_clean in q_clean or std_id_clean in q_clean or q_clean in std_id_clean:
                id_match = 1.0
            elif any(part in q_lower for part in is_num.lower().split() if len(part) > 2):
                id_match = 0.5

            # 4. Category / Domain match signal (0..1)
            cat_match = 0.0
            if category and category.lower() in q_lower:
                cat_match = 1.0

            # 5. Status support (prefer active CURRENT standards over SUPERSEDED/WITHDRAWN)
            status_support = 1.0 if status == "CURRENT" else 0.4

            # Combined weighted score
            total_score = (
                self.weights.weight_semantic * semantic_sim
                + self.weights.weight_lexical * bm25_score
                + self.weights.weight_id_match * id_match
                + self.weights.weight_category * cat_match
                + self.weights.weight_status * status_support
            )
            # Normalize to 0..1
            total_score = round(min(1.0, max(0.0, total_score)), 4)

            explanation = (
                f"Relevance: {total_score:.2f} "
                f"(Semantic: {semantic_sim:.2f}x{self.weights.weight_semantic}, "
                f"BM25: {bm25_score:.2f}x{self.weights.weight_lexical}, "
                f"ID Match: {id_match:.2f}, Status: {status})"
            )

            scored.append(
                ScoredRecommendation(
                    id=item.get("id", 0),
                    standard_id=std_id,
                    is_number=is_num,
                    title=title,
                    category=category,
                    status=status,
                    relevance_score=total_score,
                    rank=0,
                    signals={
                        "semantic_similarity": round(semantic_sim, 4),
                        "bm25_score": round(bm25_score, 4),
                        "id_match": round(id_match, 4),
                        "category_match": round(cat_match, 4),
                        "status_support": round(status_support, 4),
                    },
                    explanation=explanation,
                )
            )

        # Sort by relevance_score descending
        scored.sort(key=lambda x: x.relevance_score, reverse=True)

        # Assign final 1-based ranks
        final_list = []
        for rank, rec in enumerate(scored[:top_k], start=1):
            rec.rank = rank
            final_list.append(rec)

        return final_list
