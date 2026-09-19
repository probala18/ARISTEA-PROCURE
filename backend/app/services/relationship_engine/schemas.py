"""
Pydantic Schemas for Module 7 — Relationship Engine & Graph API.
Strictly adheres to:
1. Module 4 normalized RelationType names only.
2. System-generated grouping disclaimer for allied/testing/safety (not official BIS).
3. Preservation of unresolved targets (unresolved:{number}) without inventing integer FKs.
4. Complete provenance preservation on every edge and relationship.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from backend.app.services.knowledge_graph.graph_models import RelationType, NodeType, MatchType


class RelationshipEdgePayload(BaseModel):
    """Payload representing an authoritative relationship edge with full provenance."""
    source_id: str
    target_id: str
    source_standard_number: Optional[str] = None
    target_standard_number: str
    target_standard_id: Optional[str] = None
    target_title: Optional[str] = None
    relationship_type: str
    relationship_category: Optional[str] = None
    is_explicit_source: bool = True
    source_dataset: str
    source_provenance: Optional[Dict[str, Any]] = None
    confidence: float = 1.0
    is_unresolved: bool = False
    properties: Dict[str, Any] = Field(default_factory=dict)


class AlliedStandardItem(BaseModel):
    """Individual standard item categorized within an allied grouping."""
    standard_id: Optional[str] = None
    standard_number: str
    title: Optional[str] = None
    relationship_type: str
    relationship_category: Optional[str] = None
    is_explicit_source: bool = True
    source_dataset: str
    is_unresolved: bool = False
    provenance: Optional[Dict[str, Any]] = None


class AlliedStandardsGroup(BaseModel):
    """
    Classified allied standards grouped by Module 4 relationship types.
    Explicitly disclaims official BIS status.
    """
    standard_id: str
    canonical_id: str
    title: str
    grouping_disclaimer: str = (
        "Allied relationships (testing, safety, performance, installation, etc.) are "
        "system-generated groupings based on ingested Module 4 relationship types, "
        "not official BIS classifications."
    )
    normative: List[AlliedStandardItem] = Field(default_factory=list)
    testing: List[AlliedStandardItem] = Field(default_factory=list)
    safety: List[AlliedStandardItem] = Field(default_factory=list)
    performance: List[AlliedStandardItem] = Field(default_factory=list)
    installation: List[AlliedStandardItem] = Field(default_factory=list)
    related_products: List[AlliedStandardItem] = Field(default_factory=list)
    terminology: List[AlliedStandardItem] = Field(default_factory=list)
    superseded: List[AlliedStandardItem] = Field(default_factory=list)
    other: List[AlliedStandardItem] = Field(default_factory=list)
    total_allied: int = 0


class GraphNodePayload(BaseModel):
    """Graph node payload suitable for interactive D3/Cytoscape visualization."""
    id: str
    node_type: str
    label: str
    standard_id: Optional[str] = None
    is_number: Optional[str] = None
    title: Optional[str] = None
    is_unresolved: bool = False
    properties: Dict[str, Any] = Field(default_factory=dict)


class DependencyGraphResponse(BaseModel):
    """Multi-hop cycle-safe dependency graph response."""
    root_node_id: str
    depth: int
    nodes: List[GraphNodePayload] = Field(default_factory=list)
    edges: List[RelationshipEdgePayload] = Field(default_factory=list)
    total_nodes: int = 0
    total_edges: int = 0


class ShortestPathResponse(BaseModel):
    """Shortest path between two standards with grounded step-by-step explanation."""
    source_standard: str
    target_standard: str
    connected: bool
    depth: int
    path_nodes: List[str] = Field(default_factory=list)
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    explanation: str
    provenance_chain: List[Dict[str, Any]] = Field(default_factory=list)


class SupersessionLineageResponse(BaseModel):
    """Historical supersession lineage (forward successors and backward predecessors)."""
    standard_id: str
    canonical_id: str
    current_status: str
    supersedes: List[Dict[str, Any]] = Field(default_factory=list)
    superseded_by: List[Dict[str, Any]] = Field(default_factory=list)
    has_cycle: bool = False
    warning: Optional[str] = None
