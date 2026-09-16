"""
Knowledge Graph Service Facade for Module 4.
Combines:
- Standard identifier resolution
- Direct and typed relationship retrieval
- Multi-hop traversal and path finding
- Supersession history
- Regulatory and compliance linkages
- Explainable paths
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.models.standard import Standard
from backend.app.services.knowledge_graph.graph_models import (
    GraphEdge,
    TraversalResult,
    TraversalPath,
    StandardResolutionResult,
    SupersessionChainResult,
    ComplianceLinksResult,
)
from backend.app.services.knowledge_graph.relationship_resolver import StandardReferenceResolver
from backend.app.services.knowledge_graph.traversal_service import GraphTraversalService
from backend.app.services.knowledge_graph.supersession_service import SupersessionChainService
from backend.app.services.knowledge_graph.compliance_connector import ComplianceConnectorService
from backend.app.services.knowledge_graph.path_explainer import PathExplainer


class KnowledgeGraphService:
    """Unified service interface for graph queries and relationship traversal."""

    def __init__(self, session: Session):
        self.session = session
        self.resolver = StandardReferenceResolver(session)
        self.traversal = GraphTraversalService(session)
        self.supersession = SupersessionChainService(session)
        self.compliance = ComplianceConnectorService(session)
        self.explainer = PathExplainer()

    def resolve_standard_reference(self, identifier_or_number: str) -> StandardResolutionResult:
        """Resolves a raw or canonical standard string to an exact, part, ambiguous, or unresolved match."""
        return self.resolver.resolve(identifier_or_number)

    def get_direct_relationships(
        self,
        standard_id: int,
        relationship_types: Optional[List[str]] = None,
        include_incoming: bool = True,
    ) -> List[GraphEdge]:
        """Returns direct (1-hop) edges connected to the standard."""
        return self.traversal.get_direct_relationships(
            standard_id=standard_id,
            relationship_types=relationship_types,
            include_incoming=include_incoming,
        )

    def find_related_standards(
        self,
        standard_id: int,
        relationship_types: Optional[List[str]] = None,
        max_depth: int = 3,
        direction: str = "both",
    ) -> TraversalResult:
        """Performs multi-hop graph traversal with cycle prevention."""
        return self.traversal.traverse(
            start_standard_id=standard_id,
            relationship_types=relationship_types,
            max_depth=max_depth,
            direction=direction,
        )

    def find_path(self, source_id: int, target_id: int, max_depth: int = 3) -> Optional[Dict[str, Any]]:
        """Finds shortest explainable path between two standards."""
        path = self.traversal.find_path(source_id=source_id, target_id=target_id, max_depth=max_depth)
        if not path:
            return None
        return self.explainer.explain_path(path)

    def get_testing_standards(self, standard_id: int) -> List[GraphEdge]:
        """Convenience method: retrieves only TESTING relationships."""
        return self.get_direct_relationships(standard_id, relationship_types=["TESTING"])

    def get_safety_standards(self, standard_id: int) -> List[GraphEdge]:
        """Convenience method: retrieves only SAFETY & SEISMIC_SAFETY relationships."""
        return self.get_direct_relationships(standard_id, relationship_types=["SAFETY", "SEISMIC_SAFETY", "FOOD_CONTACT_SAFETY"])

    def get_normative_references(self, standard_id: int) -> List[GraphEdge]:
        """Convenience method: retrieves only NORMATIVE_REFERENCE relationships."""
        return self.get_direct_relationships(standard_id, relationship_types=["NORMATIVE_REFERENCE"])

    def get_supersession_chain(self, standard_id: int) -> SupersessionChainResult:
        """Retrieves loop-free supersession history (supersedes and superseded_by)."""
        return self.supersession.get_supersession_chain(standard_id)

    def get_compliance_links(self, standard_id: int) -> ComplianceLinksResult:
        """Retrieves grounded certification, QCO, license, and ministerial mapping data."""
        return self.compliance.get_compliance_links(standard_id)
