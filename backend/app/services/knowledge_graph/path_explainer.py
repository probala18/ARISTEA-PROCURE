"""
Path Explainer for Module 4.
Transforms graph traversal paths into transparent, audit-ready explanations:
- Step-by-step navigation
- Explicit vs Derived status
- Source dataset evidence & provenance
- Clear representation of series ambiguities and unresolved targets
"""
from typing import Dict, Any, List
from backend.app.services.knowledge_graph.graph_models import (
    TraversalPath,
    TraversalResult,
    MatchType,
)


class PathExplainer:
    """Generates structured, human-readable explanations for traversed relationship chains."""

    @staticmethod
    def explain_path(path: TraversalPath) -> Dict[str, Any]:
        """Explains a single traversal path from start node to end node."""
        steps_explained = []
        for s in path.steps:
            origin_type = "EXPLICIT (directly from dataset)" if s.is_explicit_source else "DERIVED (synthesized from normative_references/supersedes)"
            resolution_note = ""
            if s.resolution == MatchType.SERIES_AMBIGUOUS:
                resolution_note = " [AMBIGUOUS SERIES: base standard cites multiple parts]"
            elif s.resolution == MatchType.UNRESOLVED:
                resolution_note = " [UNRESOLVED TARGET: standard uncataloged in active dataset]"

            steps_explained.append({
                "step_depth": s.depth,
                "source": s.source,
                "relationship": s.relationship.value,
                "target": s.target,
                "edge_nature": origin_type,
                "source_dataset": s.source_dataset,
                "resolution": s.resolution.value if s.resolution else None,
                "resolution_note": resolution_note,
                "provenance": s.provenance,
            })

        narrative = f"Path from {path.start_node} to {path.end_node} (Depth {path.depth}): " + " -> ".join(
            [f"[{s.relationship.value}]-> {s.target}" for s in path.steps]
        )

        return {
            "start_node": path.start_node,
            "end_node": path.end_node,
            "total_depth": path.depth,
            "narrative": narrative,
            "steps": steps_explained,
        }

    @staticmethod
    def summarize_traversal(res: TraversalResult) -> Dict[str, Any]:
        """Provides an executive audit summary of traversed graph subgraph."""
        explicit_edges = sum(1 for e in res.edges if e.is_explicit_source)
        derived_edges = sum(1 for e in res.edges if not e.is_explicit_source)

        unresolved_nodes = [
            n.label for n in res.nodes.values()
            if n.node_type.value == "UNRESOLVED_STANDARD_REFERENCE"
        ]

        return {
            "root_node": res.root_node_id,
            "total_nodes_discovered": res.total_nodes,
            "total_edges_traversed": res.total_edges,
            "explicit_edges_count": explicit_edges,
            "derived_edges_count": derived_edges,
            "unresolved_targets_count": len(unresolved_nodes),
            "unresolved_targets": unresolved_nodes,
            "total_paths_generated": len(res.paths),
        }
