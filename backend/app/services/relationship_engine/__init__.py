"""
Module 7 — Relationship Engine package.
Provides:
- RelationshipEngine: Service expansion over Module 4 Knowledge Graph
- Schemas: RelationshipEdgePayload, AlliedStandardsGroup, DependencyGraphResponse, ShortestPathResponse, SupersessionLineageResponse
"""
from backend.app.services.relationship_engine.schemas import (
    RelationshipEdgePayload,
    AlliedStandardItem,
    AlliedStandardsGroup,
    GraphNodePayload,
    DependencyGraphResponse,
    ShortestPathResponse,
    SupersessionLineageResponse,
)
from backend.app.services.relationship_engine.engine import RelationshipEngine

__all__ = [
    "RelationshipEdgePayload",
    "AlliedStandardItem",
    "AlliedStandardsGroup",
    "GraphNodePayload",
    "DependencyGraphResponse",
    "ShortestPathResponse",
    "SupersessionLineageResponse",
    "RelationshipEngine",
]
