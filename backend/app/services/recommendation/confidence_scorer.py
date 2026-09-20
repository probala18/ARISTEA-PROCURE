"""
Confidence & Relevance Scorer for Module 6 — Recommendation Engine.
Calculates transparent RELEVANCE SCORE and internal decision-support CONFIDENCE SCORE.
Strictly disclaims legal certainty and official BIS designation.
"""
from typing import Dict, Any, List, Optional
from backend.app.services.recommendation.schemas import (
    ConfidenceLevel,
    ExplainableScoreBreakdown,
)


class ConfidenceScorer:
    """
    Computes transparent RELEVANCE SCORE (ranking) and CONFIDENCE SCORE (decision-support metric).
    Never presents confidence as a probability or legal certainty.
    """

    def compute_confidence(
        self,
        top_relevance: float,
        runner_up_relevance: Optional[float] = None,
        is_exact_lookup: bool = False,
        is_ambiguous: bool = False,
        is_out_of_scope: bool = False,
    ) -> float:
        """
        Calculates an internal decision-support confidence score between 0.0 and 1.0.
        Grounded strictly in semantic vector similarity and distinct candidate separation.
        """
        if is_out_of_scope or top_relevance <= 0.0:
            return 0.0

        if is_ambiguous:
            # Genuinely ambiguous queries lack discriminators; ceiling on confidence
            return min(0.45, round(top_relevance * 0.5, 3))

        if is_exact_lookup:
            # Direct IS standard lookup fast path
            return min(0.95, round(top_relevance, 3))

        # Base confidence from top candidate relevance (calibrated for 384d semantic vector similarity)
        conf = top_relevance * 0.95

        # Margin bonus: distinct gap over runner-up indicates clear separation
        if runner_up_relevance is not None:
            margin = max(0.0, top_relevance - runner_up_relevance)
            conf += min(0.15, margin * 1.0)

        # Bound strictly between 0.05 and 0.95 (never claim 100% legal certainty)
        return min(0.95, max(0.05, round(conf, 3)))

    def get_confidence_level(self, score: float) -> ConfidenceLevel:
        """Categorizes score into internal decision-support levels."""
        if score >= 0.75:
            return ConfidenceLevel.HIGH
        elif score >= 0.50:
            return ConfidenceLevel.MEDIUM
        elif score > 0.0:
            return ConfidenceLevel.LOW
        return ConfidenceLevel.UNKNOWN
