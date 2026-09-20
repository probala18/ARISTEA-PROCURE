"""
Recommendation Engine Facade for Module 6.
Orchestrates:
- Query analysis & Intent classification
- Semantic vector retrieval (Sentence Transformers + Dense Cosine Similarity)
- Role classification (PRIMARY as internal recommendation role)
- Supersession promotion strictly via Module 4 graph edges
- Knowledge Graph allied standard discovery (TESTING, SAFETY, etc.)
- Strict evidence packaging and provenance preservation
- Ambiguity handling (candidate spectrum + technical discriminators)
- Out-of-scope discipline (zero standards, zero hallucinations)
"""
import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.models.standard import Standard
from backend.app.services.retrieval.semantic_retriever import SemanticRetrievalEngine, RetrievalFilter
from backend.app.services.recommendation.schemas import (
    StandardRole,
    ConfidenceLevel,
    IntentType,
    EvidenceRecord,
    ExplainableScoreBreakdown,
    RecommendationCandidate,
    ClarificationPrompt,
    RecommendationRequest,
    RecommendationResponse,
)
from backend.app.services.recommendation.query_analyzer import QueryAnalyzer
from backend.app.services.recommendation.graph_enricher import GraphEnricher
from backend.app.services.recommendation.confidence_scorer import ConfidenceScorer
from backend.app.services.recommendation.explainer import Explainer


class RecommendationEngine:
    """Core recommendation orchestrator for PS 26108."""

    def __init__(self, session: Session, retrieval_engine: Optional[SemanticRetrievalEngine] = None):
        self.session = session
        self.retrieval_engine = retrieval_engine or SemanticRetrievalEngine(session)
        self.query_analyzer = QueryAnalyzer()
        self.graph_enricher = GraphEnricher(session)
        self.confidence_scorer = ConfidenceScorer()
        self.explainer = Explainer()

    def recommend(self, request: RecommendationRequest) -> RecommendationResponse:
        """Processes query and produces an explainable, evidence-backed recommendation."""
        analysis_id = str(uuid.uuid4())
        q_text = request.query_text.strip()

        # 1. Query & Intent Analysis
        analysis = self.query_analyzer.analyze(q_text)
        intent = analysis["intent"]
        lang = analysis["language"]
        attrs = analysis["attributes"]
        is_oos = analysis["is_out_of_scope"]
        is_ambig = analysis["is_ambiguous"]
        clarification_prompt = analysis["clarification_prompt"]

        # 2. Guard: Out-of-scope handling (zero standards, zero hallucinations)
        if is_oos:
            summary = self.explainer.generate_response_summary(
                query=q_text,
                intent=intent.value,
                primary_candidates=[],
                allied_dict={},
                is_ambiguous=False,
                is_out_of_scope=True,
            )
            return RecommendationResponse(
                analysis_id=analysis_id,
                query=q_text,
                detected_intent=intent,
                detected_language=lang,
                extracted_attributes=attrs,
                is_out_of_scope=True,
                is_ambiguous=False,
                overall_confidence_score=0.0,
                overall_confidence_level=ConfidenceLevel.UNKNOWN,
                primary_standards=[],
                allied_standards={},
                superseded_standards=[],
                candidate_spectrum=[],
                clarification_prompt=None,
                evidence_summary=[],
                explanation_summary=summary,
            )

        # 3. Candidate Retrieval via Module 5 Hybrid Engine
        retrieval_query = self.query_analyzer.normalize_multilingual_query(q_text) if lang != "en" else q_text
        retrieval_resp = self.retrieval_engine.retrieve(
            query=retrieval_query,
            filters=request.filters,
            top_k=10,
        )
        raw_recs = retrieval_resp.recommendations

        # 4. Guard: Ambiguity handling (candidate spectrum + missing discriminators)
        # Never select a single standard when the query is genuinely underspecified
        if is_ambig:
            spectrum: List[RecommendationCandidate] = []
            for r in raw_recs[:5]:
                std_db = self.session.get(Standard, r.id)
                if not std_db:
                    continue
                ev = self.explainer.build_primary_evidence(std_db, q_text)
                cand = RecommendationCandidate(
                    id=std_db.id,
                    standard_id=std_db.standard_id,
                    is_number=std_db.is_number,
                    title=std_db.title,
                    category=std_db.category,
                    status=std_db.status,
                    role=StandardRole.CONDITIONAL,
                    relevance_score=r.relevance_score,
                    confidence_score=round(r.relevance_score * 0.45, 3),
                    confidence_level=ConfidenceLevel.LOW,
                    score_breakdown=ExplainableScoreBreakdown(
                        semantic_similarity=r.signals.get("semantic_similarity", r.relevance_score),
                        bm25_score=0.0,
                        id_token_match=r.signals.get("id_match", 0.0),
                        category_match=r.signals.get("category_match", 0.0),
                        status_support=r.signals.get("status_support", 0.0),
                        relationship_support=0.0,
                        provenance_quality=1.0,
                        raw_relevance_score=r.relevance_score,
                        explanation=r.explanation,
                    ),
                    evidence=[ev],
                )
                spectrum.append(cand)

            summary = self.explainer.generate_response_summary(
                query=q_text,
                intent=intent.value,
                primary_candidates=[],
                allied_dict={},
                is_ambiguous=True,
                is_out_of_scope=False,
            )
            return RecommendationResponse(
                analysis_id=analysis_id,
                query=q_text,
                detected_intent=intent,
                detected_language=lang,
                extracted_attributes=attrs,
                is_out_of_scope=False,
                is_ambiguous=True,
                overall_confidence_score=0.40,
                overall_confidence_level=ConfidenceLevel.LOW,
                primary_standards=[],
                allied_standards={},
                superseded_standards=[],
                candidate_spectrum=spectrum,
                clarification_prompt=clarification_prompt,
                evidence_summary=[ev for c in spectrum for ev in c.evidence],
                explanation_summary=summary,
            )

        # 5. Non-ambiguous query: Primary standard selection & Supersession check
        if not raw_recs:
            return RecommendationResponse(
                analysis_id=analysis_id,
                query=q_text,
                detected_intent=intent,
                detected_language=lang,
                extracted_attributes=attrs,
                is_out_of_scope=False,
                is_ambiguous=False,
                overall_confidence_score=0.0,
                overall_confidence_level=ConfidenceLevel.UNKNOWN,
                primary_standards=[],
                allied_standards={},
                superseded_standards=[],
                candidate_spectrum=[],
                clarification_prompt=None,
                evidence_summary=[],
                explanation_summary=f"No matching Indian Standards found for query '{q_text}'.",
            )

        # Build candidate objects
        primary_candidates: List[RecommendationCandidate] = []
        superseded_candidates: List[RecommendationCandidate] = []
        all_evidence: List[EvidenceRecord] = []

        top_rec = raw_recs[0]
        top_std = self.session.get(Standard, top_rec.id)
        if not top_std:
            return RecommendationResponse(
                analysis_id=analysis_id, query=q_text, detected_intent=intent, detected_language=lang,
                overall_confidence_score=0.0, overall_confidence_level=ConfidenceLevel.UNKNOWN,
            )

        # Check supersession via Module 4 graph:
        # Promotion may occur only when the Module 4 graph explicitly establishes the supersession relationship.
        successor_std, supersession_msg = self.graph_enricher.get_supersession_lineage(top_std.id)

        target_primary_std = top_std
        supersession_note = None

        if successor_std:
            # Top candidate is superseded; promote explicit successor to PRIMARY
            supersession_note = (
                f"Queried standard {top_std.standard_id} is superseded. "
                f"{supersession_msg} Successor {successor_std.standard_id} selected as PRIMARY."
            )
            # Add historical standard to superseded list
            hist_ev = self.explainer.build_primary_evidence(top_std, q_text)
            all_evidence.append(hist_ev)
            superseded_candidates.append(
                RecommendationCandidate(
                    id=top_std.id,
                    standard_id=top_std.standard_id,
                    is_number=top_std.is_number,
                    title=top_std.title,
                    category=top_std.category,
                    status=top_std.status,
                    role=StandardRole.SUPERSEDED,
                    relevance_score=top_rec.relevance_score,
                    confidence_score=0.60,
                    confidence_level=ConfidenceLevel.MEDIUM,
                    score_breakdown=ExplainableScoreBreakdown(
                        semantic_similarity=top_rec.signals.get("semantic_similarity", top_rec.relevance_score),
                        bm25_score=0.0,
                        id_token_match=top_rec.signals.get("id_match", 0.0),
                        category_match=top_rec.signals.get("category_match", 0.0),
                        status_support=0.3,
                        raw_relevance_score=top_rec.relevance_score,
                        explanation=f"Historical superseded standard: {supersession_msg}",
                    ),
                    evidence=[hist_ev],
                    supersession_note=supersession_msg,
                )
            )
            target_primary_std = successor_std
        elif top_std.status == "SUPERSEDED":
            supersession_note = f"Warning: {top_std.standard_id} is marked SUPERSEDED in the BIS catalog."

        # Fetch compliance evidence for the primary standard
        compliance_note, comp_evidence = self.graph_enricher.get_compliance_evidence(target_primary_std.id)
        all_evidence.extend(comp_evidence)

        # Build Primary candidate
        pri_ev = self.explainer.build_primary_evidence(target_primary_std, q_text)
        all_evidence.append(pri_ev)

        top_rel = top_rec.relevance_score
        runner_up_rel = raw_recs[1].relevance_score if len(raw_recs) > 1 else None
        is_exact = retrieval_resp.is_exact_match_fast_path

        confidence = self.confidence_scorer.compute_confidence(
            top_relevance=top_rel,
            runner_up_relevance=runner_up_rel,
            retriever_agreement=False,
            is_exact_lookup=is_exact,
            is_ambiguous=False,
            is_out_of_scope=False,
        )
        conf_level = self.confidence_scorer.get_confidence_level(confidence)

        pri_cand = RecommendationCandidate(
            id=target_primary_std.id,
            standard_id=target_primary_std.standard_id,
            is_number=target_primary_std.is_number,
            title=target_primary_std.title,
            category=target_primary_std.category,
            status=target_primary_std.status,
            role=StandardRole.PRIMARY,
            relevance_score=top_rel,
            confidence_score=confidence,
            confidence_level=conf_level,
            score_breakdown=ExplainableScoreBreakdown(
                semantic_similarity=top_rec.signals.get("semantic_similarity", top_rel),
                bm25_score=0.0,
                id_token_match=top_rec.signals.get("id_match", 0.0),
                category_match=top_rec.signals.get("category_match", 0.0),
                status_support=top_rec.signals.get("status_support", 1.0),
                relationship_support=0.8,
                provenance_quality=1.0,
                raw_relevance_score=top_rel,
                explanation=top_rec.explanation,
            ),
            evidence=[pri_ev],
            supersession_note=supersession_note,
            compliance_note=compliance_note,
        )
        primary_candidates.append(pri_cand)

        # 6. Knowledge Graph Allied Standards (Module 4)
        allied_standards: Dict[str, List[RecommendationCandidate]] = {}
        if request.include_allied:
            allied_standards, allied_evidence = self.graph_enricher.get_allied_standards(target_primary_std.id)
            all_evidence.extend(allied_evidence)

        # 7. Secondary recommendations (remaining top candidates)
        for r in raw_recs[1:request.max_primary]:
            std_db = self.session.get(Standard, r.id)
            if not std_db or std_db.id == target_primary_std.id:
                continue
            sec_ev = self.explainer.build_primary_evidence(std_db, q_text)
            all_evidence.append(sec_ev)
            sec_cand = RecommendationCandidate(
                id=std_db.id,
                standard_id=std_db.standard_id,
                is_number=std_db.is_number,
                title=std_db.title,
                category=std_db.category,
                status=std_db.status,
                role=StandardRole.SECONDARY,
                relevance_score=r.relevance_score,
                confidence_score=round(r.relevance_score * 0.75, 3),
                confidence_level=self.confidence_scorer.get_confidence_level(r.relevance_score * 0.75),
                score_breakdown=ExplainableScoreBreakdown(
                    semantic_similarity=r.signals.get("semantic_similarity", r.relevance_score),
                    bm25_score=0.0,
                    id_token_match=r.signals.get("id_match", 0.0),
                    category_match=r.signals.get("category_match", 0.0),
                    status_support=r.signals.get("status_support", 1.0),
                    raw_relevance_score=r.relevance_score,
                    explanation=r.explanation,
                ),
                evidence=[sec_ev],
            )
            primary_candidates.append(sec_cand)

        # 8. Complete Response Summary
        summary = self.explainer.generate_response_summary(
            query=q_text,
            intent=intent.value,
            primary_candidates=primary_candidates,
            allied_dict=allied_standards,
            is_ambiguous=False,
            is_out_of_scope=False,
        )

        return RecommendationResponse(
            analysis_id=analysis_id,
            query=q_text,
            detected_intent=intent,
            detected_language=lang,
            extracted_attributes=attrs,
            is_out_of_scope=False,
            is_ambiguous=False,
            overall_confidence_score=confidence,
            overall_confidence_level=conf_level,
            primary_standards=primary_candidates,
            allied_standards=allied_standards,
            superseded_standards=superseded_candidates,
            candidate_spectrum=[],
            clarification_prompt=None,
            evidence_summary=all_evidence,
            explanation_summary=summary,
        )
