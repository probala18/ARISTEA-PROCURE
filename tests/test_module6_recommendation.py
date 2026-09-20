"""
Module 6 Test Suite — Recommendation Engine.
Tests:
1. Primary Standard Selection:
   - Evaluates procurement queries (e.g. motors -> IS 12615; PVC cables -> IS 694; Cement -> IS 269)
   - Verifies PRIMARY is marked as an internal recommendation role only
2. Allied Standards & Knowledge Graph Enrichment:
   - Strictly verifies normalized RelationTypes (TESTING, SAFETY, PERFORMANCE, etc.)
   - Ensures forbidden alternate labels (TESTED_UNDER, TEST_METHOD, etc.) are NOT used
   - Preserves complete provenance for every allied standard
3. Supersession Intelligence & Promotion:
   - Querying a superseded standard (e.g. IS 325) flags superseded status
   - Promotes explicit Module 4 graph successor (IS 12615) to PRIMARY
   - Confirms successors are NEVER inferred from title similarity alone
4. Ambiguity Handling & Technical Discriminators:
   - Broad queries ("Which BIS standard do I need for cables?", "What testing is required?")
   - Returns candidate spectrum instead of guessing a single primary standard
   - Provides structured missing discriminators
5. Out-of-Scope Handling:
   - Queries outside standards domain ("weather in Delhi") return 0 standards and 0 fabricated evidence
6. Relevance & Confidence Scoring:
   - Internal RELEVANCE SCORE (0.0 to 1.0) with explainable signals breakdown
   - Decision-support CONFIDENCE SCORE with mandatory legal disclaimers
7. Compliance Intelligence:
   - Grounded in certification and QCO records
   - Distinguishes evidence found from legal mandates
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from sqlalchemy.orm import sessionmaker

from backend.app.core.database import get_engine
from backend.app.models.standard import Standard
from backend.app.services.knowledge_graph.graph_models import RelationType
from backend.app.services.recommendation import (
    StandardRole,
    ConfidenceLevel,
    IntentType,
    RecommendationRequest,
    RecommendationResponse,
    RecommendationEngine,
    QueryAnalyzer,
    GraphEnricher,
    ConfidenceScorer,
    Explainer,
)


@pytest.fixture(scope="module")
def db_session():
    """Provides a database session over the real canonical database."""
    engine = get_engine("sqlite:///./sih_bis.db")
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture(scope="module")
def recommendation_engine(db_session):
    """Initializes the RecommendationEngine."""
    return RecommendationEngine(db_session)


def test_primary_standard_selection_motors(recommendation_engine):
    """Test that motor procurement queries correctly recommend IS 12615 as PRIMARY."""
    req = RecommendationRequest(
        query_text="energy efficient three phase induction motors for industrial pumps",
        max_primary=3,
        include_allied=True,
    )
    resp = recommendation_engine.recommend(req)

    assert not resp.is_out_of_scope
    assert not resp.is_ambiguous
    assert len(resp.primary_standards) >= 1

    top = resp.primary_standards[0]
    assert "12615" in top.standard_id or "12615" in top.is_number
    assert top.role == StandardRole.PRIMARY

    # Correction 2: Verify role is internal only
    assert "internal recommendation" in top.role_disclaimer.lower()
    assert "not an official bis" in top.role_disclaimer.lower()

    # Correction 3: Verify confidence is decision-support only
    assert top.confidence_score >= 0.50
    assert "decision-support" in top.confidence_disclaimer.lower()
    assert "not a probability" in top.confidence_disclaimer.lower()

    # Correction 7: Complete provenance
    assert len(top.evidence) >= 1
    assert top.evidence[0].source_dataset is not None
    assert top.evidence[0].record_identifier is not None


def test_allied_standards_use_only_module4_normalized_relation_types(recommendation_engine):
    """
    Correction 1: Use only normalized relationship types actually established by Module 4:
    TESTING, SAFETY, PERFORMANCE, INSTALLATION, NORMATIVE_REFERENCE, etc.
    Do not invent alternate relationship labels such as TESTED_UNDER, TEST_METHOD, etc.
    """
    req = RecommendationRequest(
        query_text="energy efficient induction motors IS 12615",
        include_allied=True,
    )
    resp = recommendation_engine.recommend(req)

    assert len(resp.allied_standards) > 0

    valid_relation_values = {r.value for r in RelationType}
    forbidden_labels = {"TESTED_UNDER", "TEST_METHOD", "SAFETY_CODE", "PERFORMANCE_STANDARD"}

    for group_rel_type, allied_list in resp.allied_standards.items():
        assert group_rel_type in valid_relation_values, f"Invalid relationship type: {group_rel_type}"
        assert group_rel_type not in forbidden_labels, f"Forbidden label used: {group_rel_type}"

        for cand in allied_list:
            assert cand.relationship_type in valid_relation_values
            assert cand.relationship_type not in forbidden_labels
            # Correction 7: Complete provenance on allied standards
            assert len(cand.evidence) >= 1
            assert cand.evidence[0].source_dataset in ["relationships.json", "sample_standards.json", "standards.csv"]


def test_supersession_promotion_explicit_module4_graph_only(recommendation_engine):
    """
    Correction 4: Supersession promotion may occur only when the Module 4 graph
    explicitly establishes the supersession relationship. Never infer successors from title similarity.
    IS 325 is explicitly superseded by IS 12615 in the database relationships.
    """
    req = RecommendationRequest(
        query_text="Three-phase induction motors IS 325",
        include_allied=True,
    )
    resp = recommendation_engine.recommend(req)

    assert not resp.is_out_of_scope
    assert not resp.is_ambiguous

    # IS 12615 must be promoted to PRIMARY
    assert len(resp.primary_standards) >= 1
    pri = resp.primary_standards[0]
    assert "12615" in pri.standard_id or "12615" in pri.is_number
    assert pri.role == StandardRole.PRIMARY
    assert "superseded" in (pri.supersession_note or "").lower()

    # IS 325 must be cataloged in superseded standards
    assert len(resp.superseded_standards) >= 1
    hist = resp.superseded_standards[0]
    assert "325" in hist.standard_id or "325" in hist.is_number
    assert hist.role == StandardRole.SUPERSEDED


def test_ambiguous_query_returns_candidate_spectrum_and_discriminators(recommendation_engine):
    """
    Correction 8: For ambiguous queries, do not select a single standard merely because
    it has the highest retrieval score. Return candidate spectrum and missing discriminators.
    """
    req = RecommendationRequest(
        query_text="Which BIS standard do I need for cables?",
    )
    resp = recommendation_engine.recommend(req)

    assert resp.is_ambiguous is True
    # Zero single primary declared
    assert len(resp.primary_standards) == 0

    # Candidate spectrum returned with multiple candidates
    assert len(resp.candidate_spectrum) >= 2
    for cand in resp.candidate_spectrum:
        assert cand.role == StandardRole.CONDITIONAL

    # Clarification prompt present with missing discriminators
    assert resp.clarification_prompt is not None
    assert resp.clarification_prompt.is_ambiguous is True
    assert len(resp.clarification_prompt.missing_discriminators) >= 3
    # Verify discriminators cover voltage, insulation/materials, and application
    disc_text = " ".join(resp.clarification_prompt.missing_discriminators).lower()
    assert "voltage" in disc_text
    assert "insulation" in disc_text or "material" in disc_text


def test_out_of_scope_discipline(recommendation_engine):
    """
    Correction 9: For OUT_OF_SCOPE queries, return zero standards and zero fabricated evidence.
    """
    req = RecommendationRequest(
        query_text="What is the weather in Delhi today?",
    )
    resp = recommendation_engine.recommend(req)

    assert resp.is_out_of_scope is True
    assert resp.detected_intent == IntentType.OUT_OF_SCOPE
    assert len(resp.primary_standards) == 0
    assert len(resp.allied_standards) == 0
    assert len(resp.superseded_standards) == 0
    assert len(resp.candidate_spectrum) == 0
    assert len(resp.evidence_summary) == 0
    assert resp.overall_confidence_score == 0.0
    assert resp.overall_confidence_level == ConfidenceLevel.UNKNOWN
    assert "outside the scope" in resp.explanation_summary.lower()


def test_relevance_score_and_breakdown_transparency(recommendation_engine):
    """
    Tests that internal RELEVANCE SCORE is between 0.0 and 1.0 and provides explainable signals.
    """
    req = RecommendationRequest(
        query_text="PVC Insulated Cables For Working Voltages Up To 1100 V",
    )
    resp = recommendation_engine.recommend(req)

    assert len(resp.primary_standards) >= 1
    top = resp.primary_standards[0]

    assert 0.0 <= top.relevance_score <= 1.0
    sb = top.score_breakdown
    assert sb.semantic_similarity > 0.0
    assert sb.bm25_score == 0.0  # Lexical scoring eliminated in semantic-only architecture
    assert sb.provenance_quality == 1.0
    assert len(sb.explanation) > 0


def test_compliance_intelligence_grounding(recommendation_engine):
    """
    Correction 5: Compliance conclusions must be grounded strictly in supplied records.
    Distinguish 'evidence found' from 'legally mandatory'.
    """
    req = RecommendationRequest(
        query_text="Is BIS certification mandatory for cables under IS 694?",
    )
    resp = recommendation_engine.recommend(req)

    assert len(resp.primary_standards) >= 1
    top = resp.primary_standards[0]
    assert "694" in top.standard_id or "694" in top.is_number

    # Compliance note should mention Scheme-I and QCO if present
    if top.compliance_note:
        assert ("Scheme" in top.compliance_note or "QCO" in top.compliance_note or "voluntary" in top.compliance_note.lower())

    # Compliance evidence records must reference real certification records
    comp_evs = [ev for ev in resp.evidence_summary if ev.source_type in {"CERTIFICATION_RECORD", "QCO_ORDER"}]
    for ev in comp_evs:
        assert ev.relationship_type in {RelationType.CERTIFICATION_SCHEME.value, RelationType.QCO_REFERENCE.value}
        assert ev.source_dataset in {
            "certification_dataset", "qco_dataset", "bis_mandatory_standards.json",
            "ReportExcel.csv", "schem.csv", "standards_dataset.json"
        }


def test_multilingual_language_detection(recommendation_engine):
    """Verifies multilingual language detection for Hindi localized queries."""
    req = RecommendationRequest(
        query_text="क्या केबल के लिए BIS सर्टिफिकेशन जरूरी है?",
    )
    resp = recommendation_engine.recommend(req)

    assert resp.detected_language == "hi"
    assert resp.detected_intent in {IntentType.CERTIFICATION_REQUIREMENT, IntentType.PRODUCT_STANDARD_RECOMMENDATION}
