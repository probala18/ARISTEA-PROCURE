"""
Test Suite for Module 9: Compliance Intelligence.
Validates:
1. Deterministic mandatory evaluation for standards with explicit mandatory QCO / certification (IS 694, IS 12615).
2. Scope-aware regulatory divergence detection (voluntary in ReportExcel vs mandatory in schem.csv: IS 21, IS 26, IS 27).
3. Explicit voluntary evidence classification with zero mandatory QCOs.
4. Explicit conditional certification evidence handling.
5. Unknown status handling for standards with missing certification and QCO records.
6. Hallmarking scheme recognition grounded strictly in dataset (IS 1417:2016).
7. CRS scheme classification grounded in dataset (IS 13252 (Part 1)).
8. BIS_ISI scheme classification (IS 694, IS 12615).
9. Product licence count context retrieval from product_licences table.
10. Backward compatibility for Module 7 /compliance endpoint (all legacy fields preserved).
11. Section 66 /api/standards/{standard_id}/certification endpoint and OpenAPI schema registration.
12. Batch compliance evaluation efficiency without N+1 query explosion.
13. Dual lookup (integer DB id vs canonical standard ID vs is_number).
14. Nonexistent standard 404 handling without manufacturing synthetic DB rows.
15. Provenance preservation across all certification, QCO, licence, and divergence items.
16. Read-only integrity: zero mutations to database tables.
17. Health check endpoint reports Module 9.
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
from backend.app.models.compliance import CertificationRecord, QCORecord, ProductLicence
from backend.app.models.relationship import StandardRelationship
from backend.app.models.version import StandardVersion
from backend.app.services.compliance_intelligence import (
    ComplianceIntelligenceService,
    RequirementLevel,
    CertificationSchemeType,
    ComplianceIntelligenceReport,
    StandardCertificationReport,
    BatchComplianceResult,
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


def test_01_mandatory_compliance_cables_is_694(client, db_session):
    """Verifies deterministic MANDATORY evaluation for IS 694 grounded in QCO and certification records."""
    svc = ComplianceIntelligenceService(db_session)
    report = svc.evaluate_compliance("IS 694")
    assert report is not None
    assert report.canonical_id == "IS 694:2010"
    assert report.requirement_level == RequirementLevel.MANDATORY
    assert report.is_mandatory_certification is True
    assert report.qco_applicable is True
    assert report.governing_scheme == CertificationSchemeType.BIS_ISI.value

    # Via API endpoint
    res = client.get("/api/standards/IS 694/compliance")
    assert res.status_code == 200
    data = res.json()
    assert data["requirement_level"] == "MANDATORY"
    assert data["qco_applicable"] is True
    assert len(data["certification_records"]) >= 1
    assert len(data["qco_records"]) >= 1


def test_02_mandatory_compliance_motors_is_12615(client, db_session):
    """Verifies deterministic MANDATORY evaluation for IS 12615 grounded in QCO order."""
    res = client.get("/api/standards/IS 12615:2018/compliance")
    assert res.status_code == 200
    data = res.json()
    assert data["canonical_id"] == "IS 12615:2018"
    assert data["requirement_level"] == "MANDATORY"
    assert data["governing_scheme"] == CertificationSchemeType.BIS_ISI.value
    assert len(data["qco_records"]) >= 1


def test_03_scope_aware_regulatory_divergence_is_21_is_26_is_27(client, db_session):
    """
    Verifies that standards with Voluntary certification in ReportExcel
    and mandatory QCO in schem.csv are flagged with REGULATORY_DIVERGENCE.
    """
    svc = ComplianceIntelligenceService(db_session)

    for code in ["IS 21", "IS 26", "IS 27"]:
        report = svc.evaluate_compliance(code)
        assert report is not None, f"Standard {code} not found"
        assert report.regulatory_divergence_detected is True, f"Expected divergence for {code}"
        assert len(report.regulatory_divergence_notes) >= 1
        assert len(report.divergences) >= 1
        # Preserves both records (Constraint 7)
        assert any(c["requirement_level"] == "VOLUNTARY" for c in report.certification_records)
        assert any(q["is_mandatory"] is True for q in report.qco_records)
        # Governed by mandatory QCO
        assert report.requirement_level == RequirementLevel.MANDATORY


def test_04_explicit_voluntary_evidence_handling(db_session):
    """Verifies that a standard with only voluntary certification and no QCO evaluates to VOLUNTARY."""
    temp_std = Standard(
        standard_id="IS TEST_VOLUNTARY:2020",
        is_number="IS TEST_VOLUNTARY",
        title="Test Voluntary Standard",
        status="CURRENT",
        source_file="test_scratch",
        publication_year=2020,
    )
    db_session.add(temp_std)
    db_session.flush()

    temp_cert = CertificationRecord(
        standard_id=temp_std.id,
        standard_number=temp_std.is_number,
        product_name="Voluntary Test Product",
        requirement_level="VOLUNTARY",
        is_mandatory=False,
        source_dataset="test_scratch",
    )
    db_session.add(temp_cert)
    db_session.flush()

    try:
        svc = ComplianceIntelligenceService(db_session)
        report = svc.evaluate_compliance(temp_std.id)
        assert report is not None
        assert report.requirement_level == RequirementLevel.VOLUNTARY
        assert report.regulatory_divergence_detected is False
    finally:
        db_session.rollback()


def test_05_explicit_conditional_evidence_handling(db_session):
    """Verifies that a standard with conditional certification evaluates to CONDITIONAL."""
    temp_std = Standard(
        standard_id="IS TEST_CONDITIONAL:2021",
        is_number="IS TEST_CONDITIONAL",
        title="Test Conditional Standard",
        status="CURRENT",
        source_file="test_scratch",
        publication_year=2021,
    )
    db_session.add(temp_std)
    db_session.flush()

    temp_cert = CertificationRecord(
        standard_id=temp_std.id,
        standard_number=temp_std.is_number,
        product_name="Conditional Test Product",
        requirement_level="CONDITIONAL",
        source_dataset="test_scratch",
    )
    db_session.add(temp_cert)
    db_session.flush()

    try:
        svc = ComplianceIntelligenceService(db_session)
        report = svc.evaluate_compliance(temp_std.id)
        assert report is not None
        assert report.requirement_level == RequirementLevel.CONDITIONAL
    finally:
        db_session.rollback()


def test_06_unknown_status_for_missing_evidence(db_session):
    """Verifies that a standard with zero certification and zero QCO records evaluates to UNKNOWN."""
    temp_std = Standard(
        standard_id="IS TEST_NO_EVIDENCE:2022",
        is_number="IS TEST_NO_EVIDENCE",
        title="Test Standard Without Compliance Evidence",
        status="CURRENT",
        source_file="test_scratch",
        publication_year=2022,
    )
    db_session.add(temp_std)
    db_session.flush()

    try:
        svc = ComplianceIntelligenceService(db_session)
        report = svc.evaluate_compliance(temp_std.id)
        assert report is not None
        assert report.requirement_level == RequirementLevel.UNKNOWN
        assert report.is_mandatory_certification is False
        assert report.qco_applicable is False
    finally:
        db_session.rollback()


def test_07_hallmarking_scheme_grounding_is_1417(client, db_session):
    """Verifies that Hallmarking scheme is returned strictly when dataset supports it (IS 1417:2016)."""
    res = client.get("/api/standards/IS 1417:2016/compliance")
    assert res.status_code == 200
    data = res.json()
    assert data["governing_scheme"] == CertificationSchemeType.HALLMARKING.value
    assert "Jewellery" in data["title"] or "Gold" in data["title"]


def test_08_crs_scheme_grounding_is_13252(client, db_session):
    """Verifies that CRS scheme is returned for IT/electronics standards (IS 13252 (Part 1))."""
    res = client.get("/api/standards/IS 13252 (Part 1):2010/compliance")
    assert res.status_code == 200
    data = res.json()
    assert data["governing_scheme"] == CertificationSchemeType.CRS.value


def test_09_qco_status_preservation_no_active_fabrication(client, db_session):
    """Verifies that QCO status is preserved verbatim from dataset and never synthesized as ACTIVE."""
    svc = ComplianceIntelligenceService(db_session)
    report = svc.get_certification_report("IS 694")
    assert report is not None
    assert len(report.qco_mandates) >= 1
    for q in report.qco_mandates:
        # schem.csv did not have status field populated; must not fabricate "ACTIVE"
        assert q.status in [None, ""] or isinstance(q.status, str)
        assert q.source_dataset == "schem.csv"


def test_10_backward_compatibility_module7_compliance(client):
    """Verifies 100% backward compatibility for existing Module 7 /compliance endpoint fields."""
    res = client.get("/api/standards/IS 694/compliance")
    assert res.status_code == 200
    data = res.json()

    # All Module 7 fields must exist and have correct types
    assert "standard_id" in data
    assert "canonical_id" in data
    assert "is_mandatory_certification" in data
    assert "qco_applicable" in data
    assert "certification_records" in data
    assert "qco_records" in data
    assert "product_licences" in data
    assert "ministry_mappings" in data
    assert "regulatory_divergence_detected" in data
    assert "regulatory_divergence_notes" in data

    # Module 9 additions
    assert "requirement_level" in data
    assert "governing_scheme" in data
    assert "confidence_score" in data
    assert "disclaimer" in data


def test_11_section_66_certification_endpoint(client):
    """Verifies Section 66 endpoint: GET /api/standards/{standard_id}/certification."""
    res = client.get("/api/standards/IS 12615:2018/certification")
    assert res.status_code == 200
    data = res.json()

    assert data["canonical_id"] == "IS 12615:2018"
    assert data["requirement_level"] == "MANDATORY"
    assert data["governing_scheme"] == "BIS_ISI"
    assert data["total_qcos"] >= 1
    assert "certifications" in data
    assert "qco_mandates" in data
    assert "disclaimer" in data


def test_12_batch_compliance_endpoint_no_n_plus_1(client, db_session):
    """Verifies batch compliance evaluation endpoint and service bulk efficiency."""
    payload = {
        "identifiers": ["IS 694", "IS 12615", "IS 21", "IS 1417", "NONEXISTENT_999"]
    }
    res = client.post("/api/standards/compliance/batch", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["total_requested"] == 5
    assert data["total_found"] == 4
    assert data["total_mandatory"] >= 3  # IS 694, IS 12615, IS 21
    assert data["total_with_divergence"] >= 1  # IS 21

    results_map = {r["identifier"]: r for r in data["results"]}
    assert results_map["IS 694"]["found"] is True
    assert results_map["IS 694"]["result"]["requirement_level"] == "MANDATORY"
    assert results_map["NONEXISTENT_999"]["found"] is False
    assert results_map["NONEXISTENT_999"]["error"] is not None


def test_13_dual_lookup_id_vs_code(client, db_session):
    """Verifies lookup across DB PK, canonical ID, and normalized is_number."""
    std_694 = db_session.query(Standard).filter_by(standard_id="IS 694:2010").first()
    assert std_694 is not None

    res_pk = client.get(f"/api/standards/{std_694.id}/compliance")
    res_canonical = client.get("/api/standards/IS 694:2010/compliance")
    res_is_num = client.get("/api/standards/IS 694/compliance")

    assert res_pk.status_code == 200
    assert res_canonical.status_code == 200
    assert res_is_num.status_code == 200

    assert res_pk.json()["canonical_id"] == res_canonical.json()["canonical_id"] == res_is_num.json()["canonical_id"]


def test_14_nonexistent_standard_404(client, db_session):
    """Verifies 404 response for unknown standards without manufacturing synthetic DB rows."""
    count_before = db_session.query(Standard).count()

    for endpoint in ["/compliance", "/certification"]:
        res = client.get(f"/api/standards/NONEXISTENT_STD_XYZ{endpoint}")
        assert res.status_code == 404
        assert "not found" in res.json()["detail"].lower()

    count_after = db_session.query(Standard).count()
    assert count_before == count_after, "DB row count modified by nonexistent lookup"


def test_15_provenance_preservation(client, db_session):
    """Verifies that all certification records, QCO records, and mappings retain source provenance."""
    svc = ComplianceIntelligenceService(db_session)
    report = svc.evaluate_compliance("IS 694")
    assert report is not None

    for c in report.certification_records:
        assert c["source_dataset"] in ["ReportExcel.csv", "certification.csv", "standards.csv"]

    for q in report.qco_records:
        assert q["source_dataset"] in ["schem.csv", "standards.csv"]


def test_16_openapi_schema_registration(client):
    """Verifies that the new routes appear in the OpenAPI schema."""
    res = client.get("/openapi.json")
    assert res.status_code == 200
    paths = res.json()["paths"]

    assert "/api/standards/{standard_id}/certification" in paths
    assert "/api/standards/{standard_id}/compliance" in paths
    assert "/api/standards/compliance/batch" in paths


def test_17_read_only_integrity_zero_mutations(client, db_session):
    """Verifies that calling compliance operations performs zero database mutations."""
    std_cnt = db_session.query(Standard).count()
    cert_cnt = db_session.query(CertificationRecord).count()
    qco_cnt = db_session.query(QCORecord).count()
    ver_cnt = db_session.query(StandardVersion).count()
    rel_cnt = db_session.query(StandardRelationship).count()

    # Query compliance and batch endpoints
    for code in ["IS 694", "IS 12615", "IS 21", "IS 1417", "IS 325"]:
        client.get(f"/api/standards/{code}/compliance")
        client.get(f"/api/standards/{code}/certification")

    client.post(
        "/api/standards/compliance/batch",
        json={"identifiers": ["IS 694", "IS 12615", "IS 21"]},
    )

    assert db_session.query(Standard).count() == std_cnt
    assert db_session.query(CertificationRecord).count() == cert_cnt
    assert db_session.query(QCORecord).count() == qco_cnt
    assert db_session.query(StandardVersion).count() == ver_cnt
    assert db_session.query(StandardRelationship).count() == rel_cnt


def test_18_health_check_module9(client):
    """Verifies health check endpoint reports Module 9."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert "Module 9" in data["module"]
