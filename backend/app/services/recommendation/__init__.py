"""
Module 6 — Recommendation Engine package.
Provides:
- RecommendationEngine: core pipeline facade
- Schemas: StandardRole, ConfidenceLevel, IntentType, RecommendationRequest, RecommendationResponse
- QueryAnalyzer, GraphEnricher, ConfidenceScorer, Explainer
"""
from backend.app.services.recommendation.schemas import (
    StandardRole,
    ConfidenceLevel,
    IntentType,
    EvidenceRecord,
    ExplainableScoreBreakdown,
    RecommendationCandidate,
    ClarificationPrompt,
    RecommendationRequest,
    RecommendationResponse,
)
from backend.app.services.recommendation.query_analyzer import QueryAnalyzer
from backend.app.services.recommendation.graph_enricher import GraphEnricher
from backend.app.services.recommendation.confidence_scorer import ConfidenceScorer
from backend.app.services.recommendation.explainer import Explainer
from backend.app.services.recommendation.recommendation_engine import RecommendationEngine

__all__ = [
    "StandardRole",
    "ConfidenceLevel",
    "IntentType",
    "EvidenceRecord",
    "ExplainableScoreBreakdown",
    "RecommendationCandidate",
    "ClarificationPrompt",
    "RecommendationRequest",
    "RecommendationResponse",
    "QueryAnalyzer",
    "GraphEnricher",
    "ConfidenceScorer",
    "Explainer",
    "RecommendationEngine",
]
