"""
Graph Traversal Service for Module 4.
Supports:
- Direct 1-hop relationship discovery (outgoing and incoming)
- Typed relationship filtering (TESTING, SAFETY, NORMATIVE_REFERENCE, etc.)
- Multi-hop traversal with depth limiting (default: 3, max: 5)
- Cycle prevention via visited path tracking
- Explicit vs Derived edge segregation
- Representation of unresolved targets as UNRESOLVED_STANDARD_REFERENCE nodes
"""
from typing import List, Dict, Set, Optional, Any
from sqlalchemy.orm import Session

from backend.app.models.standard import Standard
from backend.app.models.relationship import StandardRelationship
from backend.app.services.knowledge_graph.graph_models import (
    NodeType,
    RelationType,
    GraphNode,
    GraphEdge,
    TraversalResult,
    TraversalPath,
    TraversalStep,
    MatchType,
)
from backend.app.services.knowledge_graph.relationship_resolver import StandardReferenceResolver


class GraphTraversalService:
    """Core traversal engine operating over the PS 26108 relational knowledge graph."""

    DEFAULT_MAX_DEPTH = 3
    ABSOLUTE_MAX_DEPTH = 5

    def __init__(self, session: Session):
        self.session = session
        self.resolver = StandardReferenceResolver(session)

    def get_direct_relationships(
        self,
        standard_id: int,
        relationship_types: Optional[List[str]] = None,
        include_incoming: bool = True,
    ) -> List[GraphEdge]:
        """Returns direct (1-hop) edges connected to the specified standard."""
        std = self.session.query(Standard).get(standard_id)
        if not std:
            return []

        q_out = self.session.query(StandardRelationship).filter_by(source_standard_id=standard_id)
        if relationship_types:
            q_out = q_out.filter(StandardRelationship.relationship_type.in_(relationship_types))
        out_rels = q_out.all()

        edges: List[GraphEdge] = []
        for r in out_rels:
            target_id = f"std:{r.target_standard_id}" if r.target_standard_id else f"unresolved:{r.target_standard_number}"
            edges.append(self._to_graph_edge(r, f"std:{standard_id}", target_id))

        if include_incoming:
            q_in = self.session.query(StandardRelationship).filter_by(target_standard_id=standard_id)
            if relationship_types:
                q_in = q_in.filter(StandardRelationship.relationship_type.in_(relationship_types))
            in_rels = q_in.all()
            for r in in_rels:
                edges.append(self._to_graph_edge(r, f"std:{r.source_standard_id}", f"std:{standard_id}"))

        return edges

    def traverse(
        self,
        start_standard_id: int,
        relationship_types: Optional[List[str]] = None,
        max_depth: int = DEFAULT_MAX_DEPTH,
        direction: str = "both",  # "outgoing", "incoming", "both"
    ) -> TraversalResult:
        """
        Traverses the knowledge graph starting from start_standard_id up to max_depth.
        Guarantees cycle prevention and caps depth at ABSOLUTE_MAX_DEPTH.
        """
        clamped_depth = max(1, min(max_depth, self.ABSOLUTE_MAX_DEPTH))
        root_std = self.session.query(Standard).get(start_standard_id)
        if not root_std:
            return TraversalResult(root_node_id=str(start_standard_id), max_depth=clamped_depth)

        root_node_id = f"std:{root_std.id}"
        nodes: Dict[str, GraphNode] = {root_node_id: self._create_standard_node(root_std)}
        edges: List[GraphEdge] = []
        paths: List[TraversalPath] = []

        # Queue items: (current_node_id, current_db_id, current_depth, current_path_steps, visited_in_path)
        queue = [(root_node_id, root_std.id, 0, [], {root_node_id})]

        while queue:
            curr_node_id, curr_db_id, curr_depth, curr_steps, path_visited = queue.pop(0)

            if curr_depth >= clamped_depth or curr_db_id is None:
                continue

            # Fetch outgoing
            if direction in ("outgoing", "both"):
                q_out = self.session.query(StandardRelationship).filter_by(source_standard_id=curr_db_id)
                if relationship_types:
                    q_out = q_out.filter(StandardRelationship.relationship_type.in_(relationship_types))
                
                for r in q_out.all():
                    if r.target_standard_id:
                        tgt_node_id = f"std:{r.target_standard_id}"
                        tgt_std = self.session.query(Standard).get(r.target_standard_id)
                        if tgt_std and tgt_node_id not in nodes:
                            nodes[tgt_node_id] = self._create_standard_node(tgt_std)
                        next_db_id = r.target_standard_id
                        res_type = MatchType.EXACT
                    else:
                        tgt_node_id = f"unresolved:{r.target_standard_number}"
                        if tgt_node_id not in nodes:
                            nodes[tgt_node_id] = self._create_unresolved_node(r.target_standard_number, r.target_standard_title)
                        next_db_id = None
                        # Check resolution via resolver
                        res = self.resolver.resolve(r.target_standard_number)
                        res_type = res.match_type

                    edge = self._to_graph_edge(r, curr_node_id, tgt_node_id)
                    edges.append(edge)

                    step = TraversalStep(
                        source=curr_node_id,
                        relationship=edge.relationship_type,
                        target=tgt_node_id,
                        is_explicit_source=edge.is_explicit_source,
                        source_dataset=edge.source_dataset,
                        depth=curr_depth + 1,
                        resolution=res_type,
                        provenance=edge.source_provenance,
                    )
                    new_steps = curr_steps + [step]
                    paths.append(TraversalPath(start_node=root_node_id, end_node=tgt_node_id, depth=curr_depth + 1, steps=new_steps))

                    # Cycle check along current branch
                    if tgt_node_id not in path_visited and next_db_id is not None:
                        queue.append((tgt_node_id, next_db_id, curr_depth + 1, new_steps, path_visited | {tgt_node_id}))

            # Fetch incoming
            if direction in ("incoming", "both"):
                q_in = self.session.query(StandardRelationship).filter_by(target_standard_id=curr_db_id)
                if relationship_types:
                    q_in = q_in.filter(StandardRelationship.relationship_type.in_(relationship_types))

                for r in q_in.all():
                    src_node_id = f"std:{r.source_standard_id}"
                    src_std = self.session.query(Standard).get(r.source_standard_id)
                    if src_std and src_node_id not in nodes:
                        nodes[src_node_id] = self._create_standard_node(src_std)

                    edge = self._to_graph_edge(r, src_node_id, curr_node_id)
                    edges.append(edge)

                    step = TraversalStep(
                        source=src_node_id,
                        relationship=edge.relationship_type,
                        target=curr_node_id,
                        is_explicit_source=edge.is_explicit_source,
                        source_dataset=edge.source_dataset,
                        depth=curr_depth + 1,
                        resolution=MatchType.EXACT,
                        provenance=edge.source_provenance,
                    )
                    new_steps = curr_steps + [step]
                    paths.append(TraversalPath(start_node=root_node_id, end_node=src_node_id, depth=curr_depth + 1, steps=new_steps))

                    if src_node_id not in path_visited:
                        queue.append((src_node_id, r.source_standard_id, curr_depth + 1, new_steps, path_visited | {src_node_id}))

        # Deduplicate edges
        dedup_edges = []
        seen_edges = set()
        for e in edges:
            k = (e.source_id, e.target_id, e.relationship_type, e.is_explicit_source)
            if k not in seen_edges:
                seen_edges.add(k)
                dedup_edges.append(e)

        return TraversalResult(
            root_node_id=root_node_id,
            max_depth=clamped_depth,
            nodes=nodes,
            edges=dedup_edges,
            paths=paths,
            total_nodes=len(nodes),
            total_edges=len(dedup_edges),
        )

    def find_path(self, source_id: int, target_id: int, max_depth: int = DEFAULT_MAX_DEPTH) -> Optional[TraversalPath]:
        """Finds shortest explainable graph path between two standards."""
        res = self.traverse(start_standard_id=source_id, max_depth=max_depth, direction="outgoing")
        tgt_key = f"std:{target_id}"
        matching_paths = [p for p in res.paths if p.end_node == tgt_key]
        if not matching_paths:
            return None
        # Sort by shortest depth
        matching_paths.sort(key=lambda p: p.depth)
        return matching_paths[0]

    def _create_standard_node(self, s: Standard) -> GraphNode:
        return GraphNode(
            id=f"std:{s.id}",
            node_type=NodeType.STANDARD,
            label=s.standard_id,
            standard_id=s.standard_id,
            is_number=s.is_number,
            title=s.title,
            properties={
                "status": s.status,
                "publication_year": s.publication_year,
                "category": s.category,
                "is_mandatory_certification": s.is_mandatory_certification,
                "qco_applicable": s.qco_applicable,
            },
        )

    def _create_unresolved_node(self, target_num: str, title: Optional[str] = None) -> GraphNode:
        return GraphNode(
            id=f"unresolved:{target_num}",
            node_type=NodeType.UNRESOLVED_STANDARD_REFERENCE,
            label=target_num,
            standard_id=target_num,
            is_number=target_num,
            title=title or f"Unresolved Reference: {target_num}",
            properties={
                "is_unresolved": True,
                "notice": "Target preserved verbatim as raw reference from source dataset without external data fabrication.",
            },
        )

    def _to_graph_edge(self, r: StandardRelationship, src_id: str, tgt_id: str) -> GraphEdge:
        rel_type_str = r.relationship_type.upper().replace(" ", "_")
        try:
            rel_type = RelationType(rel_type_str)
        except ValueError:
            rel_type = RelationType.OTHER

        return GraphEdge(
            source_id=src_id,
            target_id=tgt_id,
            relationship_type=rel_type,
            source_relationship_label=r.relationship_type,
            is_explicit_source=r.is_explicit_source,
            source_dataset=r.source_dataset,
            source_provenance=r.source_provenance,
            confidence=r.confidence,
            properties={
                "relationship_category": r.relationship_category,
                "description": r.relationship_description,
            },
        )
