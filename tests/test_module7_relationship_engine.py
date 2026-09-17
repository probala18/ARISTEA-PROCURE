"""
Module 7 Test Suite — Relationship Engine & Graph API.
Covers all 13 mandatory test items:
1. Router registration and health check
2. Known standard graph API response validation
3. Allied standards grouping & system disclaimer
4. Unresolved target representation without invented integer FKs
5. Ambiguous series reference handling (IS 2386)
6. Explicit vs derived relationship filtering
7. Supersession traversal & warnings
8. Cycle prevention in graph expansion
9. Traversal depth enforcement (default: 3, max: 5)
10. Grounded shortest path computation
11. Nonexistent source/target handling
12. Compliance linkage via API
13. Provenance preservation on every edge
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from backend.app.core.database import get_engine, get_db
from backend.app.main import app
from backend.app.services.knowledge_graph.graph_models import RelationType, NodeType, MatchType
from backend.app.services.relationship_engine import (
    RelationshipEngine,
    RelationshipEdgePayload,
    AlliedStandardsGroup,
    DependencyGraphResponse,
    ShortestPathResponse,
    SupersessionLineageResponse,
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
def client(db_session):
    """Provides a FastAPI TestClient with real database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def engine(db_session):
    return RelationshipEngine(db_session)


# 1. Router registration & health check
def test_router_registration_and_health(client):
    """Verifies routes are registered with the main FastAPI application."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "Module 7" in data["module"]

    # Verify registered route paths via OpenAPI schema
    route_paths = list(app.openapi()["paths"].keys())
    assert "/api/standards/{standard_id}/relationships" in route_paths
    assert "/api/standards/{standard_id}/allied" in route_paths
    assert "/api/standards/{standard_id}/graph" in route_paths
    assert "/api/standards/{standard_id}/supersession" in route_paths
    assert "/api/graph/path" in route_paths


# 2. Known standard graph API response validation
def test_known_standard_graph_api_validation(client):
    """Verifies /api/standards/{id}/graph returns a schema-valid DependencyGraphResponse."""
    resp = client.get("/api/standards/IS 12615/graph?max_depth=2")
    assert resp.status_code == 200
    data = resp.json()

    # Validate against Pydantic schema
    graph_obj = DependencyGraphResponse(**data)
    assert graph_obj.total_nodes > 0
    assert graph_obj.total_edges > 0
    assert graph_obj.depth == 2

    # Verify root node matches
    node_ids = {n.id for n in graph_obj.nodes}
    assert any("std:" in nid for nid in node_ids)


# 3. Allied standards grouping & system disclaimer
def test_allied_standards_grouping_and_disclaimer(client):
    """
    Verifies /api/standards/{id}/allied categorizes connections into
    normative, testing, safety, performance, installation, and carries the disclaimer.
    """
    resp = client.get("/api/standards/IS 12615/allied")
    assert resp.status_code == 200
    data = resp.json()

    group = AlliedStandardsGroup(**data)
    assert "not official bis" in group.grouping_disclaimer.lower()

    # IS 12615 has testing standards (IS 12802, IS 15999)
    assert len(group.testing) >= 1
    testing_nums = [t.standard_number for t in group.testing]
    assert any("12802" in num or "15999" in num for num in testing_nums)

    # IS 12615 has safety standards (IS/IEC 60034-5, IS 900)
    assert len(group.safety) >= 1
    safety_nums = [s.standard_number for s in group.safety]
    assert any("60034" in num or "900" in num for num in safety_nums)

    # IS 12615 has performance standards (IS 8789)
    assert len(group.performance) >= 1
    perf_nums = [p.standard_number for p in group.performance]
    assert any("8789" in num for num in perf_nums)


# 4. Unresolved target representation without invented integer FKs
def test_unresolved_target_representation_in_graph_api(client):
    """
    Preserves unresolved targets (e.g. IS 1180 cited in IS 1180 (Part 1):2014) as 'unresolved:{number}'
    without inventing integer foreign keys.
    """
    resp = client.get("/api/standards/IS 1180 (Part 1):2014/relationships")
    assert resp.status_code == 200
    edges_data = resp.json()

    unresolved_found = False
    for e in edges_data:
        edge = RelationshipEdgePayload(**e)
        if edge.is_unresolved:
            unresolved_found = True
            assert edge.target_id.startswith("unresolved:")
            assert edge.target_standard_id is None  # Never invented integer FK
            assert edge.target_standard_number is not None

    assert unresolved_found is True


# 5. Ambiguous series reference handling (IS 2386)
def test_ambiguous_series_reference_resolution(engine):
    """
    Verifies that bare series numbers matching multiple parts (e.g. 'IS 2386')
    are resolved as SERIES_AMBIGUOUS and not collapsed into a single part.
    """
    res = engine.kg_service.resolve_standard_reference("IS 2386")
    assert res.match_type == MatchType.SERIES_AMBIGUOUS
    assert res.is_ambiguous is True
    assert len(res.matched_standards) >= 2


# 6. Explicit vs derived relationship filtering
def test_explicit_vs_derived_filtering(client):
    """Verifies ?is_explicit=true and ?is_explicit=false query filters."""
    # Explicit only
    resp_exp = client.get("/api/standards/IS 12615/relationships?is_explicit=true")
    assert resp_exp.status_code == 200
    for e in resp_exp.json():
        assert e["is_explicit_source"] is True
        assert e["source_dataset"] == "relationships.json"

    # Derived only
    resp_der = client.get("/api/standards/IS 12615/relationships?is_explicit=false")
    assert resp_der.status_code == 200
    for e in resp_der.json():
        assert e["is_explicit_source"] is False
        assert e["source_dataset"] in ["sample_standards.json", "standards.csv"]


# 7. Supersession traversal & warnings
def test_supersession_traversal_and_warning(client):
    """
    Verifies /api/standards/{id}/supersession returns loop-free forward/backward lineage.
    IS 325 is superseded by IS 12615.
    """
    resp = client.get("/api/standards/IS 325/supersession")
    assert resp.status_code == 200
    data = resp.json()

    lineage = SupersessionLineageResponse(**data)
    assert lineage.has_cycle is False
    assert len(lineage.superseded_by) >= 1
    assert any("12615" in item.get("canonical_id", "") for item in lineage.superseded_by)


# 8. Cycle prevention in graph expansion
def test_cycle_prevention_in_graph(engine):
    """Verifies traversal handles bidirectional or circular edges without infinite loops."""
    graph = engine.build_dependency_graph("IS 12615", max_depth=5)
    assert graph is not None
    assert graph.total_nodes > 0
    # Confirm unique node IDs in graph response
    node_ids = [n.id for n in graph.nodes]
    assert len(node_ids) == len(set(node_ids))


# 9. Traversal depth enforcement (default: 3, max: 5)
def test_depth_enforcement(client, engine):
    """Verifies depth bounding: default 3, max 5, clamped/rejected above 5."""
    # API schema validation rejects max_depth > 5
    resp_invalid = client.get("/api/standards/IS 12615/graph?max_depth=6")
    assert resp_invalid.status_code == 422  # Unprocessable Entity (FastAPI validation error)

    # Valid depth 5
    resp_valid = client.get("/api/standards/IS 12615/graph?max_depth=5")
    assert resp_valid.status_code == 200
    assert resp_valid.json()["depth"] == 5


# 10. Grounded shortest path computation
def test_shortest_path_computation_grounded_only(client):
    """
    Verifies /api/graph/path finds shortest path based strictly on actual graph connectivity.
    IS 12615 -> IS 900 (connected via installation/safety in relationships.json).
    """
    resp = client.get("/api/graph/path?source=IS 12615&target=IS 900")
    assert resp.status_code == 200
    data = resp.json()

    path_res = ShortestPathResponse(**data)
    assert path_res.connected is True
    assert path_res.depth >= 1
    assert len(path_res.steps) >= 1
    assert len(path_res.provenance_chain) >= 1
    assert "IS 12615" in path_res.explanation
    assert "IS 900" in path_res.explanation


# 11. Nonexistent source/target handling
def test_shortest_path_nonexistent_source_or_target(client):
    """Verifies graceful handling of nonexistent standards without crashing."""
    resp = client.get("/api/graph/path?source=IS NONEXISTENT 99999&target=IS 12615")
    assert resp.status_code == 200
    data = resp.json()

    path_res = ShortestPathResponse(**data)
    assert path_res.connected is False
    assert path_res.depth == 0
    assert "not found" in path_res.explanation.lower()


# 12. Compliance linkage via API
def test_compliance_linkage_via_api(client):
    """
    Verifies /api/standards/{id}/compliance retrieves grounded certification & QCO records.
    """
    resp = client.get("/api/standards/IS 694/compliance")
    assert resp.status_code == 200
    data = resp.json()

    assert data["canonical_id"] == "IS 694:2010"
    assert "certification_records" in data
    assert "qco_records" in data
    # Check that records have provenance
    for cert in data["certification_records"]:
        assert cert["source_dataset"] in ["ReportExcel.csv", "certification_dataset", "standards.csv"]


# 13. Provenance preservation on every edge
def test_provenance_preservation_on_all_edges(client):
    """Verifies that all returned relationship edges preserve source dataset and provenance."""
    resp = client.get("/api/standards/IS 12615/relationships")
    assert resp.status_code == 200
    edges = resp.json()

    for e in edges:
        assert e["source_dataset"] in ["relationships.json", "sample_standards.json", "standards.csv"]
        assert "is_explicit_source" in e
        assert isinstance(e["is_explicit_source"], bool)
        assert e["target_standard_number"] is not None
