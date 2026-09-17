"""
Test Suite for Module 8: Version and Amendment Intelligence.
Validates:
1. Version report retrieval for known canonical standards (IS 12615, IS 694, IS 325).
2. Clean separation of amendments from revisions/supersessions.
3. Superseded standard detection with explicit successor from Module 4 graph (IS 325 -> IS 12615).
4. Current standard verification (Standard.status as primary signal).
5. Missing version record handling emitting UNKNOWN_VERSION_STATUS warning.
6. Year interval gap detection emitting VERSION_GAP (never OUTDATED_VERSION_WARNING).
7. Provenance preservation on version records, amendments, and warnings.
8. Dual lookup (integer DB id vs canonical standard code vs normalized number).
9. Nonexistent standard 404 error handling without manufacturing synthetic rows.
10. Dataset-backed disclaimer presence distinguishing dataset intelligence from legal currency.
11. Batch currency check efficiency and safe handling of mixed valid/invalid inputs.
12. OpenAPI schema registration for all three Section 66 endpoints.
13. Module 8 health check verification.
14. Read-only integrity: zero mutation to underlying tables.
"""
import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import get_engine, get_db
from backend.app.main import app
from backend.app.models.standard import Standard
from backend.app.models.version import StandardVersion
from backend.app.models.relationship import StandardRelationship
from backend.app.services.version_intelligence import (
    VersionIntelligenceService,
    WarningType,
    CurrencyCheckResult,
    VersionIntelligenceReport,
)


@pytest.fixture(scope="module")
def db_session():
    """Provides a database session over the real canonical sqlite database."""
    engine = get_engine("sqlite:///./sih_bis.db")
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture(scope="module")
def client(db_session):
    """Provides a FastAPI TestClient with real database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c


def test_01_version_report_known_standard_is_12615(client, db_session):
    """Verifies complete version report for known standard IS 12615."""
    response = client.get("/api/standards/IS 12615:2018/versions")
    assert response.status_code == 200, f"Failed: {response.text}"
    data = response.json()

    assert data["standard_id"] == "IS 12615:2018"
    assert data["is_number"] == "IS 12615"
    assert data["status"] == "CURRENT"
    assert data["publication_year"] == 2018
    assert len(data["version_records"]) >= 1
    assert "disclaimer" in data
    assert "dataset-backed" in data["disclaimer"].lower() or "supplied dataset" in data["disclaimer"].lower()

    # Predecessor lineage check: IS 12615 supersedes IS 325
    supersession = data["supersession"]
    assert supersession["current_status"] == "CURRENT"
    supersedes = [s["canonical_id"] for s in supersession.get("supersedes", [])]
    assert any("325" in s for s in supersedes), f"Expected IS 325 in supersedes list, got {supersedes}"


def test_02_amendment_separation_and_provenance(client, db_session):
    """Verifies amendment records are cleanly separated and preserve source provenance."""
    # Find a standard that has amendment records (e.g., IS 456 or IS 13252)
    svc = VersionIntelligenceService(db_session)
    # IS 456 has 2 amendments in sample_standards.json
    amends = svc.get_amendments("IS 456")
    assert len(amends) >= 1, "Expected at least 1 amendment for IS 456"

    for a in amends:
        assert a.is_number == "IS 456"
        assert a.source_dataset in ["sample_standards.json", "standards.csv"]
        assert a.amendment_year is not None or a.amendment_number is not None

    # Via API endpoint
    res = client.get("/api/standards/IS 456/amendments")
    assert res.status_code == 200
    api_data = res.json()
    assert len(api_data) >= 1
    assert api_data[0]["source_dataset"] is not None


def test_03_superseded_detection_with_successor_is_325(client, db_session):
    """Verifies superseded detection with explicit successor from Module 4 graph for IS 325."""
    response = client.get("/api/standards/IS 325/currency")
    assert response.status_code == 200
    data = response.json()

    assert data["is_number"] == "IS 325"
    assert data["status"] == "SUPERSEDED"
    assert data["is_current"] is False

    # Must contain SUPERSEDED_WARNING
    warning_types = [w["warning_type"] for w in data["warnings"]]
    assert "SUPERSEDED_WARNING" in warning_types

    # Successor information must be grounded in Module 4 graph: IS 12615 supersedes IS 325
    sup_warning = next(w for w in data["warnings"] if w["warning_type"] == "SUPERSEDED_WARNING")
    assert sup_warning["severity"] == "CRITICAL"
    successors = sup_warning["evidence"].get("successors", [])
    assert len(successors) >= 1
    successor_ids = [s.get("canonical_id") for s in successors]
    assert any("12615" in s for s in successor_ids), f"Expected IS 12615 as successor, got {successor_ids}"


def test_04_current_standard_verification_is_694(client, db_session):
    """Verifies that CURRENT standard IS 694 evaluates to is_current=True without superseded warnings."""
    response = client.get("/api/standards/IS 694/currency")
    assert response.status_code == 200
    data = response.json()

    assert data["is_number"] == "IS 694"
    assert data["status"] == "CURRENT"
    assert data["is_current"] is True

    # Ensure no SUPERSEDED_WARNING
    warning_types = [w["warning_type"] for w in data["warnings"]]
    assert "SUPERSEDED_WARNING" not in warning_types


def test_05_missing_version_handling_unknown_version_status(db_session):
    """Verifies that a standard with zero version records emits UNKNOWN_VERSION_STATUS."""
    # Create temporary standard in a nested transaction
    temp_std = Standard(
        standard_id="IS TEST_UNKNOWN:2025",
        is_number="IS TEST_UNKNOWN",
        title="Test Standard Without Version History",
        status="CURRENT",
        source_file="test_scratch",
        publication_year=2025,
    )
    db_session.add(temp_std)
    db_session.flush()

    try:
        svc = VersionIntelligenceService(db_session)
        res = svc.check_currency(temp_std.id)
        assert res is not None
        warning_types = [w.warning_type.value for w in res.warnings]
        assert WarningType.UNKNOWN_VERSION_STATUS.value in warning_types

        w = next(w for w in res.warnings if w.warning_type == WarningType.UNKNOWN_VERSION_STATUS)
        assert "No version records were ingested" in w.message
    finally:
        db_session.rollback()


def test_06_year_interval_reporting_version_gap(db_session):
    """
    Verifies that a year interval mismatch emits VERSION_GAP,
    and NEVER emits OUTDATED_VERSION_WARNING (Constraint #4 and #5).
    """
    temp_std = Standard(
        standard_id="IS TEST_GAP:2010",
        is_number="IS TEST_GAP",
        title="Test Standard With Later Revision Year",
        status="CURRENT",
        source_file="test_scratch",
        publication_year=2010,
    )
    db_session.add(temp_std)
    db_session.flush()

    temp_ver = StandardVersion(
        standard_id=temp_std.id,
        is_number=temp_std.is_number,
        version_year=2010,
        latest_year=2018,  # Different year
        source_dataset="test_scratch",
    )
    db_session.add(temp_ver)
    db_session.flush()

    try:
        svc = VersionIntelligenceService(db_session)
        res = svc.check_currency(temp_std.id)
        assert res is not None

        warning_types = [w.warning_type.value for w in res.warnings]
        assert "OUTDATED_VERSION_WARNING" not in warning_types
        assert WarningType.VERSION_GAP.value in warning_types

        gap_w = next(w for w in res.warnings if w.warning_type == WarningType.VERSION_GAP)
        assert gap_w.evidence["publication_year"] == 2010
        assert gap_w.evidence["latest_year"] == 2018
    finally:
        db_session.rollback()


def test_07_provenance_preservation(client, db_session):
    """Verifies that all version records, amendments, and warnings preserve source provenance."""
    svc = VersionIntelligenceService(db_session)
    report = svc.get_version_report("IS 12615")
    assert report is not None

    for v in report.version_records:
        assert "source_dataset" in v
        assert v["source_dataset"] in ["standards.csv", "sample_standards.json"]

    for w in report.warnings:
        assert w.source_dataset is not None


def test_08_dual_lookup_id_vs_code(client, db_session):
    """Verifies that lookup works uniformly across integer DB ID, canonical standard ID, and is_number."""
    std_12615 = db_session.query(Standard).filter_by(standard_id="IS 12615:2018").first()
    assert std_12615 is not None

    # Lookup by DB PK
    res_pk = client.get(f"/api/standards/{std_12615.id}/currency")
    assert res_pk.status_code == 200

    # Lookup by canonical standard_id
    res_canonical = client.get("/api/standards/IS 12615:2018/currency")
    assert res_canonical.status_code == 200

    # Lookup by is_number
    res_is_num = client.get("/api/standards/IS 12615/currency")
    assert res_is_num.status_code == 200

    assert res_pk.json()["canonical_id"] == res_canonical.json()["canonical_id"] == res_is_num.json()["canonical_id"]


def test_09_nonexistent_standard_404(client, db_session):
    """Verifies 404 response for unknown standards without manufacturing synthetic DB rows."""
    count_before = db_session.query(Standard).count()

    for endpoint in ["/versions", "/amendments", "/currency"]:
        res = client.get(f"/api/standards/NONEXISTENT_STANDARD_99999{endpoint}")
        assert res.status_code == 404
        assert "not found" in res.json()["detail"].lower()

    count_after = db_session.query(Standard).count()
    assert count_before == count_after, "Standard count altered by nonexistent lookup"


def test_10_disclaimer_presence_and_legal_currency_distinction(client):
    """Verifies that disclaimer distinguishes dataset intelligence from legal currency determination."""
    res = client.get("/api/standards/IS 12615/currency")
    assert res.status_code == 200
    data = res.json()

    assert "disclaimer" in data
    disclaimer = data["disclaimer"]
    assert "dataset-backed" in disclaimer.lower() or "dataset" in disclaimer.lower()
    assert "legal" in disclaimer.lower() or "regulatory" in disclaimer.lower()


def test_11_batch_version_check(db_session):
    """Verifies batch check operation with mixed valid, superseded, and nonexistent standards."""
    svc = VersionIntelligenceService(db_session)
    batch_result = svc.batch_version_check(["IS 12615", "IS 325", "IS 694", "NONEXISTENT_XYZ"])

    assert batch_result.total_requested == 4
    assert batch_result.total_found == 3
    assert batch_result.total_current >= 2  # IS 12615 and IS 694 are CURRENT
    assert batch_result.total_with_warnings >= 1  # IS 325 has SUPERSEDED_WARNING

    found_map = {r.identifier: r for r in batch_result.results}
    assert found_map["IS 12615"].found is True
    assert found_map["IS 325"].found is True
    assert found_map["IS 325"].result.is_current is False
    assert found_map["NONEXISTENT_XYZ"].found is False
    assert found_map["NONEXISTENT_XYZ"].error is not None


def test_12_openapi_schema_registration(client):
    """Verifies that the three Section 66 endpoints appear in the OpenAPI schema."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]

    assert "/api/standards/{standard_id}/versions" in paths
    assert "/api/standards/{standard_id}/amendments" in paths
    assert "/api/standards/{standard_id}/currency" in paths

    # Verify method is GET
    assert "get" in paths["/api/standards/{standard_id}/versions"]
    assert "get" in paths["/api/standards/{standard_id}/amendments"]
    assert "get" in paths["/api/standards/{standard_id}/currency"]


def test_13_health_endpoint_module8(client):
    """Verifies health check endpoint reports Module 8."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "Module 8" in data["module"]


def test_14_read_only_integrity_zero_mutations(db_session, client):
    """Verifies that Module 8 operations cause zero mutations on core database tables."""
    std_cnt_init = db_session.query(Standard).count()
    ver_cnt_init = db_session.query(StandardVersion).count()
    rel_cnt_init = db_session.query(StandardRelationship).count()

    # Call all endpoints for multiple standards
    for code in ["IS 12615", "IS 325", "IS 694", "IS 456"]:
        client.get(f"/api/standards/{code}/versions")
        client.get(f"/api/standards/{code}/amendments")
        client.get(f"/api/standards/{code}/currency")

    # Check counts remain identical
    assert db_session.query(Standard).count() == std_cnt_init
    assert db_session.query(StandardVersion).count() == ver_cnt_init
    assert db_session.query(StandardRelationship).count() == rel_cnt_init
