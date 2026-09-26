"""
Relationship Engine Service for Module 7.
Builds upon Module 4 KnowledgeGraphService as the single source of truth.
Enforces:
1. Zero synthetic edges: all graph relations reflect verified Module 3/4 database edges.
2. Preservation of all 36 unresolved target references (unresolved:{number}).
3. System-generated grouping disclaimers for allied standards.
4. Traversal depth bounding (default: 3, max: 5) and cycle prevention.
5. Grounded shortest path computation based on actual graph connectivity only.
"""
from typing import List, Dict, Any, Optional, Union
from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from backend.app.models.standard import Standard
from backend.app.services.knowledge_graph.graph_models import RelationType, NodeType, MatchType
from backend.app.services.knowledge_graph.graph_service import KnowledgeGraphService
from backend.app.services.relationship_engine.schemas import (
    RelationshipEdgePayload,
    AlliedStandardItem,
    AlliedStandardsGroup,
    GraphNodePayload,
    DependencyGraphResponse,
    ShortestPathResponse,
    SupersessionLineageResponse,
)


class RelationshipEngine:
    """Expansion service layer over Module 4 for relationship classification and graph API."""

    DEFAULT_DEPTH = 3
    MAX_DEPTH = 5

    def __init__(self, session: Session):
        self.session = session
        self.kg_service = KnowledgeGraphService(session)

    def resolve_standard(self, identifier_or_id: Union[int, str]) -> Optional[Standard]:
        """Resolves an integer ID or string standard identifier to canonical Standard entity."""
        # 1. Direct integer DB PK lookup
        if isinstance(identifier_or_id, int):
            return self.session.get(Standard, identifier_or_id)

        ident_str = str(identifier_or_id).strip()
        if ident_str.isdigit():
            std = self.session.get(Standard, int(ident_str))
            if std:
                return std

        # 2. Match standard_id or is_number directly (case-insensitive)
        ident_upper = ident_str.upper()
        std = self.session.query(Standard).filter(
            or_(
                func.upper(Standard.standard_id) == ident_upper,
                func.upper(Standard.is_number) == ident_upper,
            )
        ).first()
        if std:
            return std

        # 3. Use Module 4 reference resolver
        res = self.kg_service.resolve_standard_reference(ident_str)
        if res.standard_id:
            raw_id_str = res.standard_id.replace("std:", "").strip()
            if raw_id_str.isdigit():
                std = self.session.get(Standard, int(raw_id_str))
                if std:
                    return std

        if res.canonical_id:
            std = self.session.query(Standard).filter(
                func.upper(Standard.standard_id) == res.canonical_id.strip().upper()
            ).first()
            if std:
                return std

        # 4. Delimiter-aware prefix match (e.g. 'IS 2029' matches 'IS 2029:1998' or 'IS 2029 (Part 1)', but 'IS 21' must NOT match 'IS 2185')
        std = self.session.query(Standard).filter(
            or_(
                Standard.standard_id.ilike(f"{ident_str}:%"),
                Standard.standard_id.ilike(f"{ident_str} %"),
                Standard.standard_id.ilike(f"{ident_str}(%"),
                Standard.standard_id.ilike(f"{ident_str}-%"),
                Standard.is_number.ilike(f"{ident_str}:%"),
                Standard.is_number.ilike(f"{ident_str} %"),
                Standard.is_number.ilike(f"{ident_str}(%"),
                Standard.is_number.ilike(f"{ident_str}-%"),
            )
        ).first()
        if std:
            return std

        return None

    def get_relationships(
        self,
        standard_id_or_number: Union[int, str],
        relationship_types: Optional[List[str]] = None,
        is_explicit: Optional[bool] = None,
    ) -> List[RelationshipEdgePayload]:
        """
        Retrieves direct relationship edges connected to standard.
        Preserves 36 unresolved target standard references with full provenance.
        """
        std = self.resolve_standard(standard_id_or_number)
        if not std:
            return []

        edges = self.kg_service.get_direct_relationships(
            standard_id=std.id,
            relationship_types=relationship_types,
            include_incoming=True,
        )

        payloads: List[RelationshipEdgePayload] = []
        for e in edges:
            if is_explicit is not None and e.is_explicit_source != is_explicit:
                continue

            is_unres = e.target_id.startswith("unresolved:")
            tgt_std_id = None
            tgt_title = None
            tgt_std_num = e.target_id.replace("unresolved:", "")

            if not is_unres and e.target_id.startswith("std:"):
                raw_target_id = int(e.target_id.replace("std:", ""))
                tgt_obj = self.session.get(Standard, raw_target_id)
                if tgt_obj:
                    tgt_std_id = tgt_obj.standard_id
                    tgt_title = tgt_obj.title
                    tgt_std_num = tgt_obj.is_number

            payloads.append(
                RelationshipEdgePayload(
                    source_id=e.source_id,
                    target_id=e.target_id,
                    source_standard_number=std.is_number,
                    target_standard_number=tgt_std_num,
                    target_standard_id=tgt_std_id,
                    target_title=tgt_title,
                    relationship_type=e.relationship_type.value,
                    relationship_category=e.properties.get("relationship_category"),
                    is_explicit_source=e.is_explicit_source,
                    source_dataset=e.source_dataset,
                    source_provenance=e.source_provenance,
                    confidence=e.confidence,
                    is_unresolved=is_unres,
                    properties=e.properties,
                )
            )

        return payloads

    def get_allied_standards(self, standard_id_or_number: Union[int, str]) -> Optional[AlliedStandardsGroup]:
        """
        Classifies direct connections into system-generated allied groupings:
        normative, testing, safety, performance, installation, related_products, terminology, superseded.
        """
        std = self.resolve_standard(standard_id_or_number)
        if not std:
            return None

        edges = self.kg_service.get_direct_relationships(
            standard_id=std.id,
            include_incoming=False,
        )

        group = AlliedStandardsGroup(
            standard_id=str(std.id),
            canonical_id=std.standard_id,
            title=std.title,
        )

        for e in edges:
            rel_type = e.relationship_type.value
            is_unres = e.target_id.startswith("unresolved:")
            tgt_std_id = None
            tgt_title = None
            tgt_std_num = e.target_id.replace("unresolved:", "")

            if not is_unres and e.target_id.startswith("std:"):
                raw_target_id = int(e.target_id.replace("std:", ""))
                tgt_obj = self.session.get(Standard, raw_target_id)
                if tgt_obj:
                    tgt_std_id = tgt_obj.standard_id
                    tgt_title = tgt_obj.title
                    tgt_std_num = tgt_obj.is_number

            item = AlliedStandardItem(
                standard_id=tgt_std_id,
                standard_number=tgt_std_num,
                title=tgt_title,
                relationship_type=rel_type,
                relationship_category=e.properties.get("relationship_category"),
                is_explicit_source=e.is_explicit_source,
                source_dataset=e.source_dataset,
                is_unresolved=is_unres,
                provenance=e.source_provenance,
            )

            # Categorize by Module 4 normalized RelationType
            if rel_type == RelationType.TESTING.value:
                group.testing.append(item)
            elif rel_type in {RelationType.SAFETY.value, RelationType.SEISMIC_SAFETY.value, RelationType.FOOD_CONTACT_SAFETY.value}:
                group.safety.append(item)
            elif rel_type == RelationType.PERFORMANCE.value:
                group.performance.append(item)
            elif rel_type == RelationType.INSTALLATION.value:
                group.installation.append(item)
            elif rel_type in {RelationType.RELATED_PRODUCT.value, RelationType.PRODUCT_MAPPING.value}:
                group.related_products.append(item)
            elif rel_type == RelationType.NORMATIVE_REFERENCE.value:
                group.normative.append(item)
            elif rel_type == RelationType.TERMINOLOGY.value:
                group.terminology.append(item)
            elif rel_type in {RelationType.SUPERSEDES.value, RelationType.SUPERSEDED_BY.value}:
                group.superseded.append(item)
            else:
                group.other.append(item)

        group.total_allied = (
            len(group.normative) + len(group.testing) + len(group.safety) +
            len(group.performance) + len(group.installation) + len(group.related_products) +
            len(group.terminology) + len(group.superseded) + len(group.other)
        )
        return group

    def build_dependency_graph(
        self,
        standard_id_or_number: Union[int, str],
        max_depth: int = 3,
        direction: str = "both",
    ) -> Optional[DependencyGraphResponse]:
        """
        Builds multi-hop dependency graph with depth bounding (clamped to max 5) and cycle prevention.
        Preserves unresolved target nodes without inventing integer FKs.
        """
        std = self.resolve_standard(standard_id_or_number)
        if not std:
            return None

        # Enforce Module 4 depth limits
        clamped_depth = max(1, min(max_depth, self.MAX_DEPTH))

        trav_res = self.kg_service.find_related_standards(
            standard_id=std.id,
            max_depth=clamped_depth,
            direction=direction,
        )

        nodes: List[GraphNodePayload] = []
        for n_id, n in trav_res.nodes.items():
            nodes.append(
                GraphNodePayload(
                    id=n.id,
                    node_type=n.node_type.value,
                    label=n.label,
                    standard_id=n.standard_id,
                    is_number=n.is_number,
                    title=n.title,
                    is_unresolved=(n.node_type == NodeType.UNRESOLVED_STANDARD_REFERENCE),
                    properties=n.properties,
                )
            )

        edges: List[RelationshipEdgePayload] = []
        for e in trav_res.edges:
            is_unres = e.target_id.startswith("unresolved:")
            tgt_std_id = None
            tgt_title = None
            tgt_std_num = e.target_id.replace("unresolved:", "")

            if not is_unres and e.target_id.startswith("std:"):
                raw_target_id = int(e.target_id.replace("std:", ""))
                tgt_obj = self.session.get(Standard, raw_target_id)
                if tgt_obj:
                    tgt_std_id = tgt_obj.standard_id
                    tgt_title = tgt_obj.title
                    tgt_std_num = tgt_obj.is_number

            edges.append(
                RelationshipEdgePayload(
                    source_id=e.source_id,
                    target_id=e.target_id,
                    target_standard_number=tgt_std_num,
                    target_standard_id=tgt_std_id,
                    target_title=tgt_title,
                    relationship_type=e.relationship_type.value,
                    relationship_category=e.properties.get("relationship_category"),
                    is_explicit_source=e.is_explicit_source,
                    source_dataset=e.source_dataset,
                    source_provenance=e.source_provenance,
                    confidence=e.confidence,
                    is_unresolved=is_unres,
                    properties=e.properties,
                )
            )

        return DependencyGraphResponse(
            root_node_id=trav_res.root_node_id,
            depth=clamped_depth,
            nodes=nodes,
            edges=edges,
            total_nodes=len(nodes),
            total_edges=len(edges),
        )

    def find_shortest_path(
        self,
        source_id_or_num: Union[int, str],
        target_id_or_num: Union[int, str],
        max_depth: int = 3,
    ) -> ShortestPathResponse:
        """
        Computes shortest path between two standards grounded strictly in actual graph connectivity.
        Never invents paths from semantic similarity or title keywords.
        """
        src_std = self.resolve_standard(source_id_or_num)
        tgt_std = self.resolve_standard(target_id_or_num)

        src_label = src_std.standard_id if src_std else str(source_id_or_num)
        tgt_label = tgt_std.standard_id if tgt_std else str(target_id_or_num)

        if not src_std or not tgt_std:
            missing = []
            if not src_std:
                missing.append(f"source '{source_id_or_num}'")
            if not tgt_std:
                missing.append(f"target '{target_id_or_num}'")
            return ShortestPathResponse(
                source_standard=src_label,
                target_standard=tgt_label,
                connected=False,
                depth=0,
                path_nodes=[],
                steps=[],
                explanation=f"Cannot compute path: {', '.join(missing)} was not found in database.",
                provenance_chain=[],
            )

        clamped_depth = max(1, min(max_depth, self.MAX_DEPTH))

        explained = self.kg_service.find_path(
            source_id=src_std.id,
            target_id=tgt_std.id,
            max_depth=clamped_depth,
        )

        if not explained:
            return ShortestPathResponse(
                source_standard=src_std.standard_id,
                target_standard=tgt_std.standard_id,
                connected=False,
                depth=0,
                path_nodes=[],
                steps=[],
                explanation=f"No graph relationship path exists between {src_std.standard_id} and {tgt_std.standard_id} within depth {clamped_depth}.",
                provenance_chain=[],
            )

        steps = explained.get("steps", [])
        path_nodes = [explained.get("start_node", "")] + [s.get("target", "") for s in steps]
        prov_chain = [s.get("provenance") for s in steps if s.get("provenance")]
        depth = explained.get("total_depth", 0)

        explanation = (
            f"Path from {src_std.standard_id} to {tgt_std.standard_id} (Depth {depth}): "
            + " -> ".join([f"[{s.get('relationship')}]-> {s.get('target')}" for s in steps])
        )

        return ShortestPathResponse(
            source_standard=src_std.standard_id,
            target_standard=tgt_std.standard_id,
            connected=True,
            depth=depth,
            path_nodes=path_nodes,
            steps=steps,
            explanation=explanation,
            provenance_chain=prov_chain,
        )

    def get_supersession_lineage(self, standard_id_or_number: Union[int, str]) -> Optional[SupersessionLineageResponse]:
        """Navigates historical supersession evolution with cycle prevention."""
        std = self.resolve_standard(standard_id_or_number)
        if not std:
            return None

        chain = self.kg_service.get_supersession_chain(std.id)
        warning = None
        if chain.has_cycle:
            warning = "Circular reference detected and safely severed in supersession chain."
        elif std.status == "SUPERSEDED" and not chain.superseded_by:
            warning = f"Standard {std.standard_id} is marked SUPERSEDED, but successor standard is not in database."

        return SupersessionLineageResponse(
            standard_id=str(std.id),
            canonical_id=std.standard_id,
            current_status=std.status,
            supersedes=chain.supersedes,
            superseded_by=chain.superseded_by,
            has_cycle=chain.has_cycle,
            warning=warning,
        )
