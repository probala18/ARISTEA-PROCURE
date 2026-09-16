"""
Knowledge Graph Data Models and Enums for Module 4.
Represents nodes, edges, match types, traversal requests, and explainable paths.
"""
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class NodeType(str, Enum):
    STANDARD = "STANDARD"
    STANDARD_VERSION = "STANDARD_VERSION"
    CERTIFICATION_RECORD = "CERTIFICATION_RECORD"
    QCO_RECORD = "QCO_RECORD"
    PRODUCT_CATEGORY = "PRODUCT_CATEGORY"
    MINISTRY_PRODUCT_MAPPING = "MINISTRY_PRODUCT_MAPPING"
    PROCUREMENT_CONCEPT = "PROCUREMENT_CONCEPT"
    SOURCE_DOCUMENT = "SOURCE_DOCUMENT"
    UNRESOLVED_STANDARD_REFERENCE = "UNRESOLVED_STANDARD_REFERENCE"


class RelationType(str, Enum):
    # Core technical relationships from supplied datasets
    NORMATIVE_REFERENCE = "NORMATIVE_REFERENCE"
    TESTING = "TESTING"
    SAFETY = "SAFETY"
    PERFORMANCE = "PERFORMANCE"
    RELATED_PRODUCT = "RELATED_PRODUCT"
    TERMINOLOGY = "TERMINOLOGY"
    INSTALLATION = "INSTALLATION"
    SEISMIC_SAFETY = "SEISMIC_SAFETY"
    FOOD_CONTACT_SAFETY = "FOOD_CONTACT_SAFETY"
    SUPERSEDES = "SUPERSEDES"
    SUPERSEDED_BY = "SUPERSEDED_BY"
    
    # Compliance & hierarchy relationships
    CERTIFICATION_SCHEME = "CERTIFICATION_SCHEME"
    QCO_REFERENCE = "QCO_REFERENCE"
    PRODUCT_MAPPING = "PRODUCT_MAPPING"
    VERSION_OF = "VERSION_OF"
    SOURCE_OF = "SOURCE_OF"
    OTHER = "OTHER"


class MatchType(str, Enum):
    EXACT = "EXACT"                       # Exact match by canonical ID (e.g., 'IS 694:2010')
    PART = "PART"                         # Unambiguous part-level match (e.g., 'IS 1554 (Part 1)')
    SERIES_AMBIGUOUS = "SERIES_AMBIGUOUS" # Cited base IS number matching multiple parts (e.g., 'IS 2386' -> Part 1 & Part 4)
    UNRESOLVED = "UNRESOLVED"             # Target absent from supplied datasets (e.g., 'IS 1599')


class GraphNode(BaseModel):
    id: str
    node_type: NodeType
    label: str
    standard_id: Optional[str] = None
    is_number: Optional[str] = None
    title: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    source_id: str
    target_id: str
    relationship_type: RelationType
    source_relationship_label: Optional[str] = None
    is_explicit_source: bool = True  # True = relationships.json, False = derived
    source_dataset: str
    source_provenance: Optional[Dict[str, Any]] = None
    confidence: float = 1.0
    properties: Dict[str, Any] = Field(default_factory=dict)


class StandardResolutionResult(BaseModel):
    query_string: str
    match_type: MatchType
    canonical_id: Optional[str] = None
    standard_id: Optional[str] = None
    matched_standards: List[Dict[str, Any]] = Field(default_factory=list)
    is_ambiguous: bool = False
    details: Optional[str] = None


class TraversalStep(BaseModel):
    source: str
    relationship: RelationType
    target: str
    is_explicit_source: bool
    source_dataset: str
    depth: int
    resolution: Optional[MatchType] = None
    provenance: Optional[Dict[str, Any]] = None


class TraversalPath(BaseModel):
    start_node: str
    end_node: str
    depth: int
    steps: List[TraversalStep] = Field(default_factory=list)


class TraversalResult(BaseModel):
    root_node_id: str
    max_depth: int
    nodes: Dict[str, GraphNode] = Field(default_factory=dict)
    edges: List[GraphEdge] = Field(default_factory=list)
    paths: List[TraversalPath] = Field(default_factory=list)
    total_nodes: int = 0
    total_edges: int = 0


class SupersessionChainResult(BaseModel):
    standard_id: str
    canonical_id: str
    current_status: str
    supersedes: List[Dict[str, Any]] = Field(default_factory=list)
    superseded_by: List[Dict[str, Any]] = Field(default_factory=list)
    has_cycle: bool = False


class ComplianceLinksResult(BaseModel):
    standard_id: str
    canonical_id: str
    is_mandatory_certification: Optional[bool] = None
    qco_applicable: Optional[bool] = None
    certification_records: List[Dict[str, Any]] = Field(default_factory=list)
    qco_records: List[Dict[str, Any]] = Field(default_factory=list)
    product_licences: List[Dict[str, Any]] = Field(default_factory=list)
    ministry_mappings: List[Dict[str, Any]] = Field(default_factory=list)
    regulatory_divergence_detected: bool = False
    regulatory_divergence_notes: List[str] = Field(default_factory=list)
