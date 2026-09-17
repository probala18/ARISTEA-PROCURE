"""
Knowledge Graph Enricher for Module 6 — Recommendation Engine.
Extracts allied standards and compliance evidence strictly from Module 4 services.
Strictly uses normalized RelationType values only.
"""
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from backend.app.models.standard import Standard
from backend.app.models.relationship import StandardRelationship
from backend.app.services.knowledge_graph.traversal_service import GraphTraversalService
from backend.app.services.knowledge_graph.supersession_service import SupersessionChainService
from backend.app.services.knowledge_graph.compliance_connector import ComplianceConnectorService
from backend.app.services.knowledge_graph.graph_models import RelationType
from backend.app.services.recommendation.schemas import (
    StandardRole,
    RecommendationCandidate,
    EvidenceRecord,
    ExplainableScoreBreakdown,
    ConfidenceLevel,
)


class GraphEnricher:
    """Enriches primary standard candidates with graph-derived allied standards and compliance context."""

    RELATION_ROLE_MAP = {
        RelationType.TESTING.value: StandardRole.TESTING,
        RelationType.SAFETY.value: StandardRole.SAFETY,
        RelationType.PERFORMANCE.value: StandardRole.PERFORMANCE,
        RelationType.INSTALLATION.value: StandardRole.INSTALLATION,
        RelationType.TERMINOLOGY.value: StandardRole.TERMINOLOGY,
        RelationType.NORMATIVE_REFERENCE.value: StandardRole.NORMATIVE_REFERENCE,
        RelationType.RELATED_PRODUCT.value: StandardRole.RELATED_PRODUCT,
        RelationType.SUPERSEDES.value: StandardRole.SUPERSEDED,
        RelationType.SUPERSEDED_BY.value: StandardRole.SUPERSEDED,
    }

    def __init__(self, session: Session):
        self.session = session
        self.traversal_service = GraphTraversalService(session)
        self.supersession_service = SupersessionChainService(session)
        self.compliance_service = ComplianceConnectorService(session)

    def get_supersession_lineage(self, standard_id: int) -> Tuple[Optional[Standard], Optional[str]]:
        """
        Queries Module 4 SupersessionService.
        Returns (active_successor_standard, explanation) only if the graph explicitly establishes it.
        Never infers successors from title similarity.
        """
        chain = self.supersession_service.get_supersession_chain(standard_id)
        if not chain.superseded_by:
            return None, None

        # Look for explicit resolved successor in chain
        for item in chain.superseded_by:
            target_id = item.get("standard_id")
            if target_id is not None:
                try:
                    raw_id = int(str(target_id).replace("std:", ""))
                    successor = self.session.get(Standard, raw_id)
                    if successor and successor.status == "CURRENT":
                        return successor, f"Explicitly superseded by current standard {successor.standard_id} in BIS dataset."
                except (ValueError, TypeError):
                    pass

        # Target might be uncataloged or historical
        first_successor = chain.superseded_by[0].get("standard_number")
        return None, f"Marked superseded by uncataloged standard {first_successor}."

    def get_allied_standards(
        self, primary_standard_id: int
    ) -> Tuple[Dict[str, List[RecommendationCandidate]], List[EvidenceRecord]]:
        """
        Discovers 1-hop connected standards strictly using normalized RelationType values.
        Returns grouped candidates and evidence records.
        """
        edges = self.traversal_service.get_direct_relationships(
            standard_id=primary_standard_id,
            include_incoming=False,
        )

        allied_by_role: Dict[str, List[RecommendationCandidate]] = {
            RelationType.TESTING.value: [],
            RelationType.SAFETY.value: [],
            RelationType.PERFORMANCE.value: [],
            RelationType.INSTALLATION.value: [],
            RelationType.NORMATIVE_REFERENCE.value: [],
            RelationType.RELATED_PRODUCT.value: [],
            RelationType.TERMINOLOGY.value: [],
            RelationType.SUPERSEDES.value: [],
        }
        evidence_list: List[EvidenceRecord] = []
        seen_stds = set()

        for edge in edges:
            rel_type = edge.relationship_type.value
            target_node_id = edge.target_id

            # Parse target node
            is_resolved = target_node_id.startswith("std:")
            std_obj: Optional[Standard] = None
            if is_resolved:
                raw_id = int(target_node_id.replace("std:", ""))
                std_obj = self.session.get(Standard, raw_id)

            target_std_num = std_obj.is_number if std_obj else target_node_id.replace("unresolved:", "")
            target_title = std_obj.title if std_obj else "Uncataloged standard reference in dataset"
            std_pk = std_obj.id if std_obj else -1
            std_id_str = std_obj.standard_id if std_obj else target_std_num

            # Determine role strictly from RelationType
            role = self.RELATION_ROLE_MAP.get(rel_type, StandardRole.NORMATIVE_REFERENCE)

            # Build evidence record
            ev = EvidenceRecord(
                source_type="RELATIONSHIP_EDGE",
                standard_id=std_id_str,
                standard_number=target_std_num,
                title=target_title,
                relationship_type=rel_type,
                is_explicit_source=edge.is_explicit_source,
                source_dataset=edge.source_dataset,
                record_identifier=f"edge:{edge.source_id}->{edge.target_id}",
                details=(
                    f"Grounded edge of type {rel_type} from {edge.source_dataset} "
                    f"({'explicit' if edge.is_explicit_source else 'derived reference'})."
                ),
            )
            evidence_list.append(ev)

            # Skip duplicate standards in same group
            group_key = rel_type if rel_type in allied_by_role else RelationType.NORMATIVE_REFERENCE.value
            dedup_key = (group_key, target_std_num)
            if dedup_key in seen_stds:
                continue
            seen_stds.add(dedup_key)

            candidate = RecommendationCandidate(
                id=std_pk,
                standard_id=std_id_str,
                is_number=target_std_num,
                title=target_title,
                category=std_obj.category if std_obj else None,
                status=std_obj.status if std_obj else "HISTORICAL_OR_UNCATALOGED",
                role=role,
                relevance_score=0.85 if edge.is_explicit_source else 0.70,
                confidence_score=0.85 if edge.is_explicit_source else 0.70,
                confidence_level=ConfidenceLevel.HIGH if edge.is_explicit_source else ConfidenceLevel.MEDIUM,
                score_breakdown=ExplainableScoreBreakdown(
                    semantic_similarity=0.0,
                    bm25_score=0.0,
                    id_token_match=1.0,
                    category_match=1.0,
                    status_support=1.0 if (std_obj and std_obj.status == "CURRENT") else 0.5,
                    relationship_support=1.0,
                    provenance_quality=1.0 if edge.is_explicit_source else 0.8,
                    raw_relevance_score=0.85 if edge.is_explicit_source else 0.70,
                    explanation=f"Allied standard connected via {rel_type} in {edge.source_dataset}.",
                ),
                evidence=[ev],
                relationship_type=rel_type,
            )
            allied_by_role[group_key].append(candidate)

        # Remove empty groups
        clean_allied = {k: v for k, v in allied_by_role.items() if v}
        return clean_allied, evidence_list

    def get_compliance_evidence(self, standard_id: int) -> Tuple[Optional[str], List[EvidenceRecord]]:
        """
        Retrieves grounded compliance evidence for standard.
        Distinguishes 'evidence found' from 'legally mandatory'.
        """
        comp = self.compliance_service.get_compliance_links(standard_id)
        evidence_list: List[EvidenceRecord] = []
        notes = []

        # Certifications
        if comp.certification_records:
            for c in comp.certification_records:
                scheme = c.get("certification_type", "Standard")
                mand = c.get("is_mandatory")
                src = c.get("source_dataset", "certification_dataset")
                req_level = c.get("requirement_level", "Unknown")

                if mand is True:
                    notes.append(f"Mandatory certification under {scheme} (Requirement level: {req_level}).")
                elif mand is False:
                    notes.append(f"Voluntary certification recorded under {scheme}.")
                else:
                    notes.append(f"Certification record exists under {scheme} (Mandatory status: {req_level}).")

                evidence_list.append(
                    EvidenceRecord(
                        source_type="CERTIFICATION_RECORD",
                        standard_number=comp.canonical_id,
                        relationship_type=RelationType.CERTIFICATION_SCHEME.value,
                        source_dataset=src,
                        record_identifier=f"cert:{c.get('id')}",
                        details=f"Certification scheme: {scheme}, mandatory: {mand}, level: {req_level}.",
                    )
                )

        # QCOs
        if comp.qco_records:
            for q in comp.qco_records:
                q_name = q.get("order_name", "Quality Control Order")
                minis = q.get("ministry", "Relevant Ministry")
                notes.append(f"Covered by QCO: '{q_name}' enforced by {minis}.")
                evidence_list.append(
                    EvidenceRecord(
                        source_type="QCO_ORDER",
                        standard_number=comp.canonical_id,
                        relationship_type=RelationType.QCO_REFERENCE.value,
                        source_dataset="qco_dataset",
                        record_identifier=f"qco:{q.get('id')}",
                        details=f"QCO Order: {q_name}, Ministry: {minis}.",
                    )
                )

        # Divergence
        if comp.regulatory_divergence_detected:
            notes.append(f"Note on regulatory discrepancy: {'; '.join(comp.regulatory_divergence_notes)}")

        compliance_summary = " ".join(notes) if notes else "No specific mandatory certification or QCO order found in supplied records."
        return compliance_summary, evidence_list
