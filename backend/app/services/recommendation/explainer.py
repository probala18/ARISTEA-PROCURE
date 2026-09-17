"""
Evidence & Explainability Generator for Module 6 — Recommendation Engine.
Produces transparent, evidence-grounded explanations and complete provenance packaging.
"""
from typing import List, Dict, Any, Optional
from backend.app.models.standard import Standard
from backend.app.services.recommendation.schemas import (
    StandardRole,
    RecommendationCandidate,
    EvidenceRecord,
    ExplainableScoreBreakdown,
    ConfidenceLevel,
)


class Explainer:
    """Generates human-readable, auditable explanations grounded strictly in database facts."""

    def build_primary_evidence(self, standard: Standard, query: str) -> EvidenceRecord:
        """Constructs authoritative provenance record for primary standard."""
        return EvidenceRecord(
            source_type="STANDARD_RECORD",
            standard_id=standard.standard_id,
            standard_number=standard.is_number,
            title=standard.title,
            relationship_type=None,
            is_explicit_source=True,
            source_dataset=standard.source_file or "standards_dataset.json",
            record_identifier=f"std_id:{standard.id}",
            details=(
                f"Authoritative record for {standard.standard_id} ('{standard.title}') "
                f"ingested from {standard.source_file} (Category: {standard.category}, Status: {standard.status})."
            ),
        )

    def generate_candidate_explanation(
        self,
        candidate: RecommendationCandidate,
        query: str,
        extracted_attrs: Dict[str, Any],
    ) -> str:
        """Builds human-readable 'why recommended' explanation for a single candidate."""
        reasons = []

        # Role context
        if candidate.role == StandardRole.PRIMARY:
            reasons.append(
                f"Selected as primary standard because it directly specifies requirements for '{candidate.title}'."
            )
        elif candidate.role == StandardRole.SUPERSEDED:
            reasons.append(
                f"Historical standard '{candidate.standard_id}'. Warning: This standard is superseded."
            )
        elif candidate.role == StandardRole.SECONDARY:
            reasons.append(
                f"Relevant alternative standard in domain '{candidate.category}'."
            )

        # Matched attributes
        matched = []
        if "voltage" in extracted_attrs and "volt" in candidate.title.lower():
            matched.append(f"operating voltage ({extracted_attrs['voltage']})")
        if "materials" in extracted_attrs:
            m_matches = [m for m in extracted_attrs["materials"] if m.lower() in candidate.title.lower()]
            if m_matches:
                matched.append(f"material specification ({', '.join(m_matches)})")
        if matched:
            reasons.append(f"Directly matches specified {', '.join(matched)}.")

        # Status & Provenance
        if candidate.status == "CURRENT":
            reasons.append("Authoritative active standard in BIS catalog.")
        elif candidate.status == "SUPERSEDED":
            reasons.append("Standard is marked superseded; see allied successor.")

        # Relevance breakdown summary
        sb = candidate.score_breakdown
        reasons.append(
            f"Internal Relevance Score: {candidate.relevance_score:.2f} "
            f"(Semantic: {sb.semantic_similarity:.2f}, BM25: {sb.bm25_score:.2f}, Status: {sb.status_support:.2f})."
        )

        return " ".join(reasons)

    def generate_response_summary(
        self,
        query: str,
        intent: str,
        primary_candidates: List[RecommendationCandidate],
        allied_dict: Dict[str, List[RecommendationCandidate]],
        is_ambiguous: bool,
        is_out_of_scope: bool,
    ) -> str:
        """Generates executive summary for the complete recommendation response."""
        if is_out_of_scope:
            return (
                f"The query '{query}' falls outside the scope of Indian Standards and public procurement specifications. "
                "No Indian Standards were retrieved or recommended."
            )

        if is_ambiguous:
            return (
                f"The query '{query}' is underspecified. Multiple Indian Standards apply depending on operating parameters. "
                "A candidate spectrum and missing technical discriminators have been provided to refine selection."
            )

        if not primary_candidates:
            return f"No matching Indian Standards were identified for query '{query}' in the current knowledge base."

        top = primary_candidates[0]
        parts = [
            f"For query '{query}', primary recommendation is {top.standard_id} ('{top.title}').",
            f"Internal Relevance Score is {top.relevance_score:.2f} (Confidence: {top.confidence_level.value}).",
        ]

        if top.supersession_note:
            parts.append(top.supersession_note)

        allied_counts = []
        for rel_type, candidates in allied_dict.items():
            allied_counts.append(f"{len(candidates)} {rel_type.lower()} standard(s)")
        if allied_counts:
            parts.append(f"Knowledge Graph identified: {', '.join(allied_counts)}.")

        if top.compliance_note:
            parts.append(f"Compliance: {top.compliance_note}")

        return " ".join(parts)
