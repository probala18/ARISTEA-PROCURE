"""
Module 4 Test Suite — Knowledge Graph & Relationship Engine.
Tests all requirements:
1. Standard Resolution: exact, normalized, part, series-ambiguous, unresolved
2. Direct and Typed Relationships: testing, safety, normative refs, explicit vs derived separation
3. Traversal: 1-hop, multi-hop, max-depth enforcement, cycle prevention
4. Supersession: current -> historical unresolved, reverse superseded-by, cycle-free
5. Compliance Linkages: standard -> certification, QCO, product licence, ministry mapping, divergence
6. Path Explanations: structured audit trail with provenance
7. Edge cases: empty/malformed IDs, uncataloged standards
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from sqlalchemy.orm import sessionmaker

from backend.app.core.database import get_engine
from backend.app.models import Standard, StandardRelationship
from backend.app.services.knowledge_graph import (
    KnowledgeGraphService,
    StandardReferenceResolver,
    GraphTraversalService,
    SupersessionChainService,
    ComplianceConnectorService,
    PathExplainer,
    MatchType,
    NodeType,
    RelationType,
)


@pytest.fixture(scope="module")
def db_session():
    engine = get_engine("sqlite:///./sih_bis.db")
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture(scope="module")
def kg_service(db_session):
    return KnowledgeGraphService(db_session)


# ==========================================
# 1. STANDARD REFERENCE RESOLVER TESTS
# ==========================================

def test_resolve_exact_canonical_match(kg_service):
    """Exact canonical standard ID match (e.g. 'IS 694:2010')."""
    res = kg_service.resolve_standard_reference("IS 694:2010")
    assert res.match_type == MatchType.EXACT
    assert res.canonical_id == "IS 694:2010"
    assert res.is_ambiguous is False
    assert len(res.matched_standards) == 1


def test_resolve_normalized_whitespace_and_case(kg_service):
    """Normalized match with spacing or casing differences."""
    res1 = kg_service.resolve_standard_reference("is694")
    assert res1.match_type in (MatchType.EXACT, MatchType.PART)
    assert res1.canonical_id == "IS 694:2010"

    res2 = kg_service.resolve_standard_reference("IS 1293")
    assert res2.match_type in (MatchType.EXACT, MatchType.PART)
    assert "IS 1293" in res2.canonical_id


def test_resolve_part_level_match(kg_service):
    """Unambiguous part-level match (e.g. 'IS 1554 (Part 1)')."""
    res = kg_service.resolve_standard_reference("IS 1554 (Part 1):1988")
    assert res.match_type == MatchType.EXACT
    assert res.canonical_id == "IS 1554 (Part 1):1988"


def test_resolve_series_ambiguous_reference(kg_service):
    """
    Base IS number citing a multi-part series where multiple parts exist in DB:
    e.g., 'IS 2386' matches 'IS 2386 (Part 1):1963' and 'IS 2386 (Part 4):1963'.
    Must preserve ambiguity and NEVER collapse to single part.
    """
    res = kg_service.resolve_standard_reference("IS 2386")
    assert res.match_type == MatchType.SERIES_AMBIGUOUS
    assert res.is_ambiguous is True
    assert len(res.matched_standards) >= 2
    matched_ids = [s["standard_id"] for s in res.matched_standards]
    assert "IS 2386 (Part 1):1963" in matched_ids
    assert "IS 2386 (Part 4):1963" in matched_ids


def test_resolve_fasteners_series_ambiguous(kg_service):
    """'IS 1367' has multiple parts in DB (Part 1 and Part 3)."""
    res = kg_service.resolve_standard_reference("IS 1367")
    assert res.match_type == MatchType.SERIES_AMBIGUOUS
    assert res.is_ambiguous is True
    assert len(res.matched_standards) >= 2


def test_resolve_unresolved_reference(kg_service):
    """Standards genuinely absent from supplied datasets return UNRESOLVED."""
    res1 = kg_service.resolve_standard_reference("IS 1599")
    assert res1.match_type == MatchType.UNRESOLVED
    assert res1.canonical_id is None

    res2 = kg_service.resolve_standard_reference("IS 999999")
    assert res2.match_type == MatchType.UNRESOLVED


def test_resolve_empty_and_malformed(kg_service):
    """Handles empty or malformed strings gracefully."""
    res1 = kg_service.resolve_standard_reference("")
    assert res1.match_type == MatchType.UNRESOLVED

    res2 = kg_service.resolve_standard_reference("   ")
    assert res2.match_type == MatchType.UNRESOLVED


# ==========================================
# 2. DIRECT & TYPED RELATIONSHIP TESTS
# ==========================================

def test_direct_relationships_explicit_vs_derived(kg_service, db_session):
    """Verifies that direct relationships segregate explicit vs derived sources."""
    # Find a standard with explicit relationships from relationships.json
    motor_std = db_session.query(Standard).filter(Standard.standard_id.like("%12615%")).first()
    assert motor_std is not None

    rels = kg_service.get_direct_relationships(motor_std.id)
    assert len(rels) > 0

    explicit_edges = [r for r in rels if r.is_explicit_source]
    for e in explicit_edges:
        assert e.source_dataset == "relationships.json"
        assert e.source_provenance is not None


def test_typed_relationship_filtering(kg_service, db_session):
    """Retrieves specific relationship types (TESTING, SAFETY, NORMATIVE_REFERENCE)."""
    tmt_std = db_session.query(Standard).filter(Standard.standard_id.like("%1786%")).first()
    assert tmt_std is not None

    testing_rels = kg_service.get_testing_standards(tmt_std.id)
    assert len(testing_rels) > 0
    for r in testing_rels:
        assert r.relationship_type.value == "TESTING"

    safety_rels = kg_service.get_safety_standards(tmt_std.id)
    assert any(r.relationship_type.value in ("SAFETY", "SEISMIC_SAFETY") for r in safety_rels)


def test_unresolved_target_preservation_in_edges(kg_service, db_session):
    """Asserts that targets with target_standard_id = NULL retain verbatim target string."""
    tmt_std = db_session.query(Standard).filter(Standard.standard_id.like("%1786%")).first()
    testing_rels = kg_service.get_testing_standards(tmt_std.id)

    unresolved_targets = [e for e in testing_rels if e.target_id.startswith("unresolved:")]
    assert len(unresolved_targets) > 0
    target_numbers = [e.target_id.replace("unresolved:", "") for e in unresolved_targets]
    assert any("IS 1608" in t or "IS 1599" in t for t in target_numbers)


# ==========================================
# 3. TRAVERSAL & CYCLE PREVENTION TESTS
# ==========================================

def test_traversal_depth_enforcement(kg_service, db_session):
    """Enforces max_depth limits (default 3, clamped max 5)."""
    cement_std = db_session.query(Standard).filter(Standard.standard_id.like("%269%")).first()
    assert cement_std is not None

    res_d1 = kg_service.find_related_standards(cement_std.id, max_depth=1)
    res_d2 = kg_service.find_related_standards(cement_std.id, max_depth=2)

    assert res_d1.max_depth == 1
    assert res_d2.max_depth == 2
    # Deeper traversal explores more or equal paths
    assert len(res_d2.paths) >= len(res_d1.paths)


def test_traversal_cycle_prevention(kg_service, db_session):
    """Verifies that traversal terminates cleanly without infinite loops."""
    std = db_session.query(Standard).first()
    # Run with maximum allowed depth
    res = kg_service.find_related_standards(std.id, max_depth=5)
    assert res.max_depth == 5
    # Must terminate and return finite node set
    assert res.total_nodes > 0


def test_find_shortest_path_explanation(kg_service, db_session):
    """Finds path between related standards and returns explainable audit output."""
    # Find two standards that are directly or indirectly related
    rel = db_session.query(StandardRelationship).filter(StandardRelationship.target_standard_id.isnot(None)).first()
    assert rel is not None

    path_explanation = kg_service.find_path(rel.source_standard_id, rel.target_standard_id, max_depth=3)
    assert path_explanation is not None
    assert "narrative" in path_explanation
    assert len(path_explanation["steps"]) >= 1
    assert path_explanation["steps"][0]["relationship"] == rel.relationship_type.upper()


# ==========================================
# 4. SUPERSESSION CHAIN TESTS
# ==========================================

def test_supersession_chain_with_historical_unresolved(kg_service, db_session):
    """
    Tests supersession chain where current standard supersedes an older unparted standard:
    e.g., 'IS 1180 (Part 1):2014' supersedes historical 'IS 1180:1989'.
    """
    dist_trans = db_session.query(Standard).filter(Standard.standard_id.like("%1180%")).first()
    assert dist_trans is not None

    chain = kg_service.get_supersession_chain(dist_trans.id)
    assert len(chain.supersedes) > 0
    assert chain.has_cycle is False

    historical_entry = chain.supersedes[0]
    assert "IS 1180" in historical_entry["canonical_id"]
    assert historical_entry["status"] == "SUPERSEDED"


def test_supersession_no_circular_self_link(kg_service, db_session):
    """Verifies that no standard is marked as superseding itself."""
    for s in db_session.query(Standard).filter(Standard.supersedes.isnot(None)).all():
        chain = kg_service.get_supersession_chain(s.id)
        for prev in chain.supersedes:
            # Prev standard ID must not be the standard itself
            if prev["standard_id"] is not None:
                assert prev["standard_id"] != s.id


# ==========================================
# 5. COMPLIANCE CONNECTOR TESTS
# ==========================================

def test_compliance_links_standard_to_cert_and_qco(kg_service, db_session):
    """Connects standard to Certification, QCO, and Product Licences."""
    cable_std = db_session.query(Standard).filter(Standard.standard_id.like("%694%")).first()
    assert cable_std is not None

    comp = kg_service.get_compliance_links(cable_std.id)
    assert comp.canonical_id == cable_std.standard_id
    assert len(comp.certification_records) > 0
    assert len(comp.product_licences) > 0


def test_compliance_divergence_detection(kg_service, db_session):
    """Verifies identification of standards with voluntary certification in ReportExcel but under QCO."""
    # Find a standard known to have regulatory divergence
    qco_std_nums = [q[0] for q in db_session.query(Standard.is_number).filter(Standard.qco_applicable.is_(True)).all()]
    assert len(qco_std_nums) > 0

    tested = False
    for num in qco_std_nums[:10]:
        std = db_session.query(Standard).filter_by(is_number=num).first()
        if std:
            comp = kg_service.get_compliance_links(std.id)
            if comp.regulatory_divergence_detected:
                assert len(comp.regulatory_divergence_notes) > 0
                tested = True
                break
    assert tested is True


# ==========================================
# 6. PATH EXPLAINER AUDIT SUMMARY TESTS
# ==========================================

def test_path_explainer_audit_summary(kg_service, db_session):
    """Asserts that PathExplainer produces accurate traversal metrics."""
    std = db_session.query(Standard).first()
    traversal_res = kg_service.find_related_standards(std.id, max_depth=2)

    summary = PathExplainer.summarize_traversal(traversal_res)
    assert summary["root_node"] == f"std:{std.id}"
    assert summary["total_nodes_discovered"] == traversal_res.total_nodes
    assert summary["total_edges_traversed"] == traversal_res.total_edges
    assert (summary["explicit_edges_count"] + summary["derived_edges_count"]) == traversal_res.total_edges
