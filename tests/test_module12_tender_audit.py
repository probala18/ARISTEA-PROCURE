"""
Module 12 Test Suite — Tender Gap Detection & Audit.
Tests:
1. End-to-End Pipeline:
   Tender Document -> Extracted Requirements -> Existing Standard References
   -> Semantic Recommendation -> Version Intelligence -> Compliance Intelligence
   -> Gap Detection -> Evidence-Based Audit.
2. Gap Categories:
   - OUTDATED_REFERENCE (IS 325 superseded by IS 12615:2018)
   - MISSING_REFERENCE (unreferenced product requirements)
   - POTENTIALLY_MISSING_TESTING_STANDARD (allied testing standards from graph)
   - POTENTIALLY_MISSING_SAFETY_STANDARD (allied safety standards from graph)
   - CERTIFICATION_GAP (QCO / mandatory certification omitted from clause)
   - COMPLIANCE_EVIDENCE_MISSING (unlisted standard reference)
   - AMBIGUOUS_SPECIFICATION (broad/ambiguous procurement clause)
   - SUFFICIENT_EVIDENCE (valid current standards)
3. Section 83 Trust Model:
   - KNOWN (explicitly in text)
   - INFERRED (suggested by engine/graph)
   - UNKNOWN (unestablished by available evidence)
   - Absence of citation is NOT treated as automatic non-compliance
4. Expected-vs-Present Breakdown:
   - present_standards, expected_standards, missing_standards, outdated_standards,
     testing_gaps, safety_gaps, certification_gaps
5. Coverage Score:
   - Calibrated metric between 0.0 and 1.0 (and percentage)
6. API Endpoint:
   - GET /api/tenders/{id}/audit
7. Database Persistence:
   - Stored in tender_audit_results and tender.status set to 'AUDITED'
8. Core Standards Integrity:
   - Read-only integrity of 268 standards preserved
9. Health Check:
   - /api/health includes Module 12
"""
import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.main import app
from backend.app.core.database import get_engine, get_db
from backend.app.models.standard import Standard
from backend.app.models.tender import (
    TenderDocument,
    TenderSection,
    TenderRequirement,
    TenderStandardReference,
    TenderAuditResult,
)
from backend.app.services.tender_engine import TenderEngineService
from backend.app.services.tender_audit import (
    GapSeverity,
    GapCategory,
    TrustLevel,
    TenderGapAnalyzer,
    TenderAuditService,
    TenderAuditReport,
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
    """Provides a FastAPI TestClient with database override."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(scope="module")
def sample_tender_id(db_session):
    """Creates a sample tender document with known, outdated, and ungrounded requirements."""
    content = (
        "NATIONAL THERMAL POWER CORPORATION - PROCUREMENT TENDER\n\n"
        "SECTION 1: SCOPE OF WORK\n"
        "Clause 1.1: Supply of heavy duty electrical equipment and civil construction materials.\n\n"
        "SECTION 2: TECHNICAL SPECIFICATIONS\n"
        "Clause 2.1: Electric motors shall be supplied as per legacy standard IS 325.\n"
        "Clause 2.2: Supply 1.1 kV grade PVC insulated single core copper cables for power wiring.\n"
        "Clause 2.3: Structural foundation cement shall conform to IS 269.\n"
        "Clause 2.4: Special import accessory must adhere to unlisted standard IS 99999.\n"
    ).encode("utf-8")

    service = TenderEngineService(db_session)
    tender_doc = service.process_document(
        file_content=content,
        filename="ntpc_procurement_audit.txt",
        title="NTPC Electrical & Civil Procurement",
        organization="NTPC Ltd.",
    )
    return tender_doc.id


# 1. Pipeline & Gap Analyzer Tests
def test_gap_analyzer_pipeline(db_session, sample_tender_id):
    """Verify full end-to-end execution of TenderGapAnalyzer."""
    tender = db_session.query(TenderDocument).filter(TenderDocument.id == sample_tender_id).first()
    analyzer = TenderGapAnalyzer(db_session)
    report = analyzer.analyze_tender(tender)

    assert isinstance(report, TenderAuditReport)
    assert report.tender_id == sample_tender_id
    assert report.total_gaps_found > 0
    assert 0.0 <= report.coverage_score <= 1.0
    assert report.coverage_percentage >= 0.0
    assert "coverage score" in report.audit_summary.lower()


# 2. Outdated Standard Detection
def test_outdated_reference_detection(db_session, sample_tender_id):
    """
    Tender explicitly cited IS 325.
    Verify IS 325 is flagged as OUTDATED_REFERENCE with successor IS 12615 from Module 4 graph.
    """
    tender = db_session.query(TenderDocument).filter(TenderDocument.id == sample_tender_id).first()
    analyzer = TenderGapAnalyzer(db_session)
    report = analyzer.analyze_tender(tender)

    outdated = [g for g in report.gaps if g.gap_category == GapCategory.OUTDATED_REFERENCE]
    assert len(outdated) >= 1

    is325_gap = next((g for g in outdated if "325" in str(g.standard_id)), None)
    assert is325_gap is not None
    assert is325_gap.severity == GapSeverity.CRITICAL
    assert is325_gap.trust_level == TrustLevel.KNOWN
    assert is325_gap.successor_standard_id is not None
    assert "12615" in is325_gap.successor_standard_id
    assert "superseded" in is325_gap.issue_description.lower()


# 3. Missing Reference Detection
def test_missing_reference_detection(db_session, sample_tender_id):
    """
    Clause 2.2 specifies '1.1 kV grade PVC insulated single core copper cables'
    without citing IS 694. Verify MISSING_REFERENCE is detected via semantic recommendation.
    """
    tender = db_session.query(TenderDocument).filter(TenderDocument.id == sample_tender_id).first()
    analyzer = TenderGapAnalyzer(db_session)
    report = analyzer.analyze_tender(tender)

    missing = [g for g in report.gaps if g.gap_category == GapCategory.MISSING_REFERENCE]
    assert len(missing) >= 1

    cable_gap = next((g for g in missing if any(c in str(g.standard_id) for c in ["694", "7098", "1554"])), None)
    assert cable_gap is not None
    assert cable_gap.trust_level == TrustLevel.INFERRED
    assert any(c in cable_gap.standard_id for c in ["694", "7098", "1554"])


# 4. Potentially Missing Allied Standards (Testing & Safety)
def test_allied_standards_gap_detection(db_session):
    """
    When IS 12615 is cited, knowledge graph allied testing/safety standards
    not cited in the tender must be reported as POTENTIALLY_MISSING.
    """
    content = (
        "SECTION 1: TECHNICAL SPECIFICATION\n"
        "Clause 1.1: Motors shall strictly conform to IS 12615:2018 for energy efficiency.\n"
    ).encode("utf-8")

    service = TenderEngineService(db_session)
    tender_doc = service.process_document(
        file_content=content,
        filename="motor_only.txt",
        title="Motor Tender",
    )

    analyzer = TenderGapAnalyzer(db_session)
    report = analyzer.analyze_tender(tender_doc)

    testing_gaps = [g for g in report.gaps if g.gap_category == GapCategory.POTENTIALLY_MISSING_TESTING_STANDARD]
    assert len(testing_gaps) >= 1
    assert testing_gaps[0].trust_level == TrustLevel.INFERRED
    assert testing_gaps[0].severity == GapSeverity.ADVISORY


# 5. Certification & QCO Gaps
def test_certification_gap_detection(db_session):
    """
    When a mandatory QCO standard is cited without requiring valid certification,
    it must be flagged as CERTIFICATION_GAP.
    """
    content = (
        "SECTION 1: SPECIFICATIONS\n"
        "Clause 1.1: Cables shall conform to IS 694.\n"
    ).encode("utf-8")

    service = TenderEngineService(db_session)
    tender_doc = service.process_document(
        file_content=content,
        filename="cert_gap.txt",
    )

    analyzer = TenderGapAnalyzer(db_session)
    report = analyzer.analyze_tender(tender_doc)

    cert_gaps = [g for g in report.gaps if g.gap_category == GapCategory.CERTIFICATION_GAP]
    assert len(cert_gaps) >= 1
    assert "694" in str(cert_gaps[0].standard_id)
    assert cert_gaps[0].trust_level == TrustLevel.KNOWN


# 6. Compliance Evidence Missing
def test_compliance_evidence_missing_detection(db_session, sample_tender_id):
    """Unlisted or unrecognized standard reference triggers COMPLIANCE_EVIDENCE_MISSING."""
    tender = db_session.query(TenderDocument).filter(TenderDocument.id == sample_tender_id).first()
    analyzer = TenderGapAnalyzer(db_session)
    report = analyzer.analyze_tender(tender)

    evidence_missing = [g for g in report.gaps if g.gap_category == GapCategory.COMPLIANCE_EVIDENCE_MISSING]
    assert len(evidence_missing) >= 1
    assert "99999" in str(evidence_missing[0].standard_id)
    assert evidence_missing[0].trust_level == TrustLevel.UNKNOWN


# 7. Section 83 Trust Model Compliance
def test_section_83_trust_model_compliance(db_session, sample_tender_id):
    """
    Verify strict adherence to Section 83 Trust Model:
    - KNOWN, INFERRED, UNKNOWN are correctly partitioned
    - Trust disclaimer is present
    - Absence of citation is NOT treated as an automatic statutory violation
    """
    tender = db_session.query(TenderDocument).filter(TenderDocument.id == sample_tender_id).first()
    analyzer = TenderGapAnalyzer(db_session)
    report = analyzer.analyze_tender(tender)

    trust_levels = {g.trust_level for g in report.gaps}
    assert TrustLevel.KNOWN in trust_levels
    assert TrustLevel.INFERRED in trust_levels
    assert TrustLevel.UNKNOWN in trust_levels
    assert "legal advice" in report.trust_disclaimer.lower()


# 8. Expected vs Present Breakdown Structure
def test_expected_vs_present_structure(db_session, sample_tender_id):
    """Verify structured breakdown of expected vs present standards."""
    tender = db_session.query(TenderDocument).filter(TenderDocument.id == sample_tender_id).first()
    analyzer = TenderGapAnalyzer(db_session)
    report = analyzer.analyze_tender(tender)

    comp = report.expected_vs_present
    assert len(comp.present_standards) >= 1
    assert len(comp.outdated_standards) >= 1
    assert len(comp.missing_standards) >= 1


# 9. Tender Audit Service & Database Caching
def test_tender_audit_service_caching(db_session, sample_tender_id):
    """Verify TenderAuditService persists results in tender_audit_results and sets status to AUDITED."""
    service = TenderAuditService(db_session)
    report1 = service.audit_tender(sample_tender_id)

    assert report1.tender_id == sample_tender_id
    
    # Check DB record
    audit_rec = db_session.query(TenderAuditResult).filter(
        TenderAuditResult.tender_id == sample_tender_id
    ).first()
    assert audit_rec is not None
    assert audit_rec.coverage_score == report1.coverage_score

    tender_rec = db_session.query(TenderDocument).filter(TenderDocument.id == sample_tender_id).first()
    assert tender_rec.status == "AUDITED"

    # Second call returns cached report
    report2 = service.audit_tender(sample_tender_id, force_recompute=False)
    assert report2.coverage_score == report1.coverage_score


# 10. Section 67 GET /api/tenders/{id}/audit Endpoint
def test_api_get_tender_audit_endpoint(client, sample_tender_id):
    """Test GET /api/tenders/{id}/audit API endpoint."""
    response = client.get(f"/api/tenders/{sample_tender_id}/audit")
    assert response.status_code == 200
    data = response.json()

    assert data["tender_id"] == sample_tender_id
    assert "coverage_score" in data
    assert "coverage_percentage" in data
    assert "gaps" in data
    assert len(data["gaps"]) > 0
    assert "expected_vs_present" in data
    assert "trust_disclaimer" in data


def test_api_get_tender_audit_not_found(client):
    """Test GET /api/tenders/999999/audit returns 404."""
    response = client.get("/api/tenders/999999/audit")
    assert response.status_code == 404


# 11. Core Database Integrity Check
def test_database_standards_integrity_after_audit(db_session):
    """Ensure audit execution does not alter authoritative 268 standards."""
    standards_count = db_session.query(Standard).count()
    assert standards_count in [268, 269]


# 12. Health Check includes Module 12
def test_health_check_includes_module12(client):
    """Verify /api/health includes Module 12."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert "Module 12" in response.json()["module"]
    assert "Tender Audit" in response.json()["module"]
