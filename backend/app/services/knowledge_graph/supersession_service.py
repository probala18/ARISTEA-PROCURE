"""
Supersession Chain Service for Module 4.
Navigates forward (SUPERSEDED_BY) and backward (SUPERSEDES) standard evolution chains.
Safely represents uncataloged historical standards as unresolved strings.
Prevents circular loops in supersession paths.
"""
from typing import List, Dict, Set, Any, Optional
from sqlalchemy.orm import Session

from backend.app.models.standard import Standard
from backend.app.models.relationship import StandardRelationship
from backend.app.services.knowledge_graph.graph_models import SupersessionChainResult
from backend.app.services.knowledge_graph.relationship_resolver import StandardReferenceResolver


class SupersessionChainService:
    """Computes explainable, loop-free standard supersession lineages."""

    def __init__(self, session: Session):
        self.session = session
        self.resolver = StandardReferenceResolver(session)

    def get_supersession_chain(self, standard_id: int) -> SupersessionChainResult:
        """
        Retrieves the complete supersession history for a standard:
        - Standards superseded by this standard (older versions)
        - Standards that supersede this standard (newer successors)
        - Unresolved historical strings preserved accurately
        - Cycle detection
        """
        std = self.session.query(Standard).get(standard_id)
        if not std:
            return SupersessionChainResult(
                standard_id=str(standard_id),
                canonical_id="UNKNOWN",
                current_status="UNKNOWN",
            )

        supersedes_list: List[Dict[str, Any]] = []
        superseded_by_list: List[Dict[str, Any]] = []
        has_cycle = False

        # 1. Backward chain: Standards superseded by this standard
        visited_backward: Set[str] = {f"std:{std.id}"}
        curr_queue = [(std.id, 1)]

        while curr_queue:
            curr_id, depth = curr_queue.pop(0)
            if depth > 5:
                break

            # Find relationships where source supersedes target
            rels = (
                self.session.query(StandardRelationship)
                .filter_by(source_standard_id=curr_id, relationship_type="SUPERSEDES")
                .all()
            )

            for r in rels:
                if r.target_standard_id:
                    node_key = f"std:{r.target_standard_id}"
                    if node_key in visited_backward:
                        has_cycle = True
                        continue
                    visited_backward.add(node_key)

                    target_std = self.session.query(Standard).get(r.target_standard_id)
                    supersedes_list.append({
                        "standard_id": r.target_standard_id,
                        "canonical_id": target_std.standard_id if target_std else r.target_standard_number,
                        "is_number": target_std.is_number if target_std else r.target_standard_number,
                        "status": target_std.status if target_std else "SUPERSEDED",
                        "depth": depth,
                        "resolved": True,
                        "source_dataset": r.source_dataset,
                        "provenance": r.source_provenance,
                    })
                    curr_queue.append((r.target_standard_id, depth + 1))
                else:
                    # Unresolved historical string (e.g., 'IS 1180:1989' or 'IS 780')
                    supersedes_list.append({
                        "standard_id": None,
                        "canonical_id": r.target_standard_number,
                        "is_number": r.target_standard_number,
                        "status": "SUPERSEDED",
                        "depth": depth,
                        "resolved": False,
                        "notice": "Historical standard uncataloged in active supplied dataset; preserved as string.",
                        "source_dataset": r.source_dataset,
                        "provenance": r.source_provenance,
                    })

        # Also check standard.supersedes text column if not already in relationships
        if std.supersedes:
            already_covered = {s["canonical_id"] for s in supersedes_list}
            if std.supersedes not in already_covered:
                res = self.resolver.resolve(std.supersedes)
                resolved_id = int(res.standard_id) if (res.standard_id and int(res.standard_id) != std.id) else None
                supersedes_list.append({
                    "standard_id": resolved_id,
                    "canonical_id": res.canonical_id or std.supersedes,
                    "is_number": std.supersedes,
                    "status": "SUPERSEDED",
                    "depth": 1,
                    "resolved": (resolved_id is not None),
                    "match_type": res.match_type.value if resolved_id else "HISTORICAL_UNRESOLVED",
                    "source_dataset": "standards.csv",
                    "provenance": {"raw_field": "supersedes", "value": std.supersedes},
                })

        # 2. Forward chain: Successor standards that supersede this standard
        visited_forward: Set[str] = {f"std:{std.id}"}
        fwd_queue = [(std.id, 1)]

        while fwd_queue:
            curr_id, depth = fwd_queue.pop(0)
            if depth > 5:
                break

            # Find standards where curr_id was the target of a SUPERSEDES relationship
            succ_rels = (
                self.session.query(StandardRelationship)
                .filter_by(target_standard_id=curr_id, relationship_type="SUPERSEDES")
                .all()
            )

            for r in succ_rels:
                node_key = f"std:{r.source_standard_id}"
                if node_key in visited_forward:
                    has_cycle = True
                    continue
                visited_forward.add(node_key)

                succ_std = self.session.query(Standard).get(r.source_standard_id)
                superseded_by_list.append({
                    "standard_id": r.source_standard_id,
                    "canonical_id": succ_std.standard_id if succ_std else r.source_standard_number,
                    "status": succ_std.status if succ_std else "CURRENT",
                    "depth": depth,
                    "resolved": True,
                    "relationship_type": "SUPERSEDED_BY",
                    "is_explicit_source": False,  # Reverse edge is DERIVED
                    "source_dataset": r.source_dataset,
                    "provenance": {"derived_from_supersedes_id": r.id},
                })
                fwd_queue.append((r.source_standard_id, depth + 1))

        return SupersessionChainResult(
            standard_id=str(std.id),
            canonical_id=std.standard_id,
            current_status=std.status,
            supersedes=supersedes_list,
            superseded_by=superseded_by_list,
            has_cycle=has_cycle,
        )
