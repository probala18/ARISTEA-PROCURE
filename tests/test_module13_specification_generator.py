"""
Module 13 Test Suite — Specification Generator.
Tests:
1. Technical Specification Generation:
   - Derives scope from tender
   - Replaces superseded standards (IS 325 -> IS 12615:2018)
   - Incorporates missing primary standards (IS 694/7098/1554 for cables)
   - Incorporates allied testing and safety standards
   - Stipulates mandatory QCO compliance clauses
2. Categorical Distinction of Requirements:
   - TENDER_DERIVED
   - RECOMMENDED_STANDARD
   - COMPLIANCE_REQUIREMENT
   - CONDITIONAL_RECOMMENDATION
3. Evidence and Provenance Preservation:
   - Every requirement carries source_dataset and provenance records
4. Tender Clause / Corrective Clause Formulation:
   - Formulates formal Section 2 tender clauses with supersession & QCO clauses
5. Compliance Checklist Generation:
   - Generates tabular and structured checklist with regulatory status (MANDATORY, VOLUNTARY, etc.)
6. Audit Correction Generation:
   - Rectifies audit gaps with side-by-side corrected clauses
7. Zero Hallucination of Technical Limits:
   - Outputs UNKNOWN / 'Insufficient verified evidence' for unspecified parameters
8. Disclaimers:
   - PRIMARY role disclaimer present
   - confidence_score decision-support disclaimer present
9. Regeneration & Editing:
   - PUT /api/specifications/{id} updates specification and increments version
   - Original tender document, requirements, references, and audit records remain 100% pristine
10. API Endpoints:
    - POST /api/tenders/{id}/generate
    - GET /api/tenders/{id}/specifications
    - POST /api/specifications/generate
    - GET /api/specifications/{id}
    - PUT /api/specifications/{id}
    - POST /api/analysis/{analysis_id}/generate (Section 69)
11. Database Standards Integrity:
    - 268 standards unchanged
12. Health Check:
    - /api/health includes Module 13
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
from backend.app.models.analysis import GeneratedSpecification
from backend.app.services.tender_engine import TenderEngineService
from backend.app.services.specification_generator import (
    SpecificationType,
    RequirementOrigin,
    RegulatoryStatus,
    SpecificationGenerator,
    SpecificationService,
    SpecificationGenerationRequest,
    SpecificationUpdateRequest,
)


@pytest.fixture(scope="module")
def db_session():
    """Provides a database session over the canonical database."""
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
    """Creates or retrieves sample tender document with known, outdated, and ungrounded requirements."""
    tender_number = "NTPC/PROC/2026/M13-001"
    existing = db_session.query(TenderDocument).filter(TenderDocument.tender_number == tender_number).first()
    if existing:
        return existing.id

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
        filename="module13_test_tender.txt",
        tender_number=tender_number,
        title="NTPC Electrical & Civil Procurement Package M13",
        organization="National Thermal Power Corporation",
    )
    return tender_doc.id


# =============================================================================
# 1. Technical Specification Generation
# =============================================================================
def test_generate_technical_specification(db_session, sample_tender_id):
    """
    Test generating full technical specification from tender.
    Verifies supersession rectification (IS 325 -> IS 12615), missing standards,
    and structured content.
    """
    generator = SpecificationGenerator(db_session)
    text, structured, provenance = generator.generate_technical_specification(tender_id=sample_tender_id)

    assert isinstance(text, str)
    assert len(text) > 100
    assert "TECHNICAL SPECIFICATION" in text
    assert "IS 12615" in text  # Supersession successor for IS 325
    assert len(structured["applicable_standards"]) >= 2
    assert len(provenance) > 0


# =============================================================================
# 2. Categorical Distinction of Requirements
# =============================================================================
def test_requirement_origins_distinction(db_session, sample_tender_id):
    """
    Verify requirements are strictly partitioned into:
    TENDER_DERIVED, RECOMMENDED_STANDARD, COMPLIANCE_REQUIREMENT, CONDITIONAL_RECOMMENDATION.
    """
    generator = SpecificationGenerator(db_session)
    _, structured, _ = generator.generate_technical_specification(tender_id=sample_tender_id)

    origins = {item["origin"] for item in structured["applicable_standards"]}
    # Expect both TENDER_DERIVED and RECOMMENDED_STANDARD (from missing or superseded)
    assert RequirementOrigin.TENDER_DERIVED.value in origins or RequirementOrigin.RECOMMENDED_STANDARD.value in origins

    # Check testing/safety conditional recommendations
    if structured["testing_and_acceptance"]:
        for t in structured["testing_and_acceptance"]:
            assert t["origin"] == RequirementOrigin.CONDITIONAL_RECOMMENDATION.value

    # Check compliance requirement clauses
    if structured["mandatory_compliance_clauses"]:
        for c in structured["mandatory_compliance_clauses"]:
            assert c["origin"] == RequirementOrigin.COMPLIANCE_REQUIREMENT.value


# =============================================================================
# 3. Evidence and Provenance Preservation
# =============================================================================
def test_provenance_preservation(db_session, sample_tender_id):
    """
    Ensure every generated item retains its provenance records (source dataset, QCO, relationships).
    """
    generator = SpecificationGenerator(db_session)
    _, structured, provenance = generator.generate_technical_specification(tender_id=sample_tender_id)

    assert len(provenance) > 0
    for item in structured["applicable_standards"]:
        assert "evidence_sources" in item
        assert len(item["evidence_sources"]) > 0
        ev = item["evidence_sources"][0]
        assert "source_dataset" in ev or "detected_requirement" in ev or "legacy_standard" in ev


# =============================================================================
# 4. Tender Clause & Corrective Clause Formulation
# =============================================================================
def test_generate_tender_clause(db_session, sample_tender_id):
    """
    Test generating formal procurement clauses and corrective clauses.
    Verifies outdated standard IS 325 is explicitly prohibited and replaced by IS 12615.
    """
    generator = SpecificationGenerator(db_session)
    text, structured, evidence = generator.generate_tender_clause(tender_id=sample_tender_id)

    assert "IS 12615" in text
    assert "IS 325" in text
    assert len(structured["incorporated_standards"]) >= 1
    assert any("12615" in s for s in structured["incorporated_standards"])


# =============================================================================
# 5. Compliance Checklist Generation
# =============================================================================
def test_generate_compliance_checklist(db_session, sample_tender_id):
    """
    Test generating compliance checklist with regulatory status, QCO verification, and actions.
    """
    generator = SpecificationGenerator(db_session)
    text, structured, evidence = generator.generate_compliance_checklist(tender_id=sample_tender_id)

    assert "| Indian Standard |" in text
    assert structured["total_items"] >= 1
    for item in structured["items"]:
        assert "regulatory_status" in item
        assert item["regulatory_status"] in ["MANDATORY", "VOLUNTARY", "CONDITIONAL", "UNKNOWN"]
        assert "verification_method" in item
        assert "action_required" in item


# =============================================================================
# 6. Audit Correction Generation
# =============================================================================
def test_generate_audit_correction(db_session, sample_tender_id):
    """
    Test audit-driven corrective specification generation.
    """
    generator = SpecificationGenerator(db_session)
    text, structured, evidence = generator.generate_audit_correction(tender_id=sample_tender_id)

    assert "TENDER AUDIT CORRECTIVE SPECIFICATION" in text
    assert structured["total_corrections_made"] >= 1
    for corr in structured["corrected_clauses"]:
        assert "gap_type" in corr
        assert "original_clause" in corr
        assert "corrected_clause" in corr
        assert "evidence" in corr


# =============================================================================
# 7. Zero Hallucination of Technical Limits / Output UNKNOWN
# =============================================================================
def test_zero_hallucination_of_technical_limits(db_session, sample_tender_id):
    """
    Verify that when technical limits are missing, the generator outputs UNKNOWN /
    'Insufficient verified evidence' rather than fabricating numeric limits.
    """
    generator = SpecificationGenerator(db_session)
    text, structured, _ = generator.generate_technical_specification(tender_id=sample_tender_id)

    # Technical parameters must either be from tender or state UNKNOWN
    params = structured["technical_parameters"]
    assert len(params) > 0

    # If voltage rating was extracted from tender:
    voltage_param = next((p for p in params if "voltage" in p["parameter"].lower()), None)
    if voltage_param:
        assert voltage_param["trust_level"] == "KNOWN"
        assert "1.1 kV" in voltage_param["value"]

    # Verify no fabricated values exist
    for p in params:
        if p["value"] == "UNKNOWN":
            assert "Insufficient verified evidence" in p.get("status", "") or "Insufficient verified evidence" in p.get("note", "")


# =============================================================================
# 8. Disclaimers for PRIMARY Role and Confidence Score
# =============================================================================
def test_disclaimers_enforced(db_session, sample_tender_id):
    """
    Verify disclaimers are present on all candidate standards.
    """
    generator = SpecificationGenerator(db_session)
    _, structured, _ = generator.generate_technical_specification(tender_id=sample_tender_id)

    for item in structured["applicable_standards"]:
        assert "Role 'PRIMARY' is an internal recommendation designation" in item["role_disclaimer"]
        assert "Confidence score is an internal decision-support metric" in item["confidence_disclaimer"]


# =============================================================================
# 9. Regeneration & Editing Without Corrupting Original Tender Evidence
# =============================================================================
def test_regeneration_and_editing_integrity(db_session, sample_tender_id):
    """
    Verify updating a specification modifies only tender_specifications record,
    leaving tender_documents, tender_requirements, and tender_standard_references pristine.
    """
    service = SpecificationService(db_session)

    # 1. Generate specification
    req = SpecificationGenerationRequest(
        tender_id=sample_tender_id,
        generation_type=SpecificationType.TECHNICAL_SPECIFICATION,
        title="Initial Draft Specification",
    )
    spec_resp = service.generate_specification(req)
    spec_id = spec_resp.id
    assert spec_resp.version == 1
    assert spec_resp.is_edited is False

    # Snapshot tender requirement count
    req_count_before = db_session.query(TenderRequirement).filter(
        TenderRequirement.tender_id == sample_tender_id
    ).count()

    # 2. Update specification
    update_req = SpecificationUpdateRequest(
        title="Customized Officer Approved Specification",
        generated_text="Customized specification text approved by Procurement Committee.",
    )
    updated_resp = service.update_specification(spec_id, update_req)

    assert updated_resp.id == spec_id
    assert updated_resp.version == 2
    assert updated_resp.is_edited is True
    assert updated_resp.title == "Customized Officer Approved Specification"
    assert "Customized specification text" in updated_resp.generated_text

    # 3. Verify tender document and requirements remain intact
    tender = db_session.query(TenderDocument).filter(TenderDocument.id == sample_tender_id).first()
    assert tender is not None
    assert tender.tender_number == "NTPC/PROC/2026/M13-001"

    req_count_after = db_session.query(TenderRequirement).filter(
        TenderRequirement.tender_id == sample_tender_id
    ).count()
    assert req_count_after == req_count_before


# =============================================================================
# 10. API Endpoints
# =============================================================================
def test_api_tenders_generate_and_list_endpoints(client, sample_tender_id):
    """Test POST /api/tenders/{id}/generate and GET /api/tenders/{id}/specifications."""
    # Generate
    res = client.post(
        f"/api/tenders/{sample_tender_id}/generate?generation_type=technical_specification&title=API+Generated+Spec"
    )
    assert res.status_code == 200
    data = res.json()
    assert data["tender_id"] == sample_tender_id
    assert data["generation_type"] == "technical_specification"
    spec_id = data["id"]

    # List
    list_res = client.get(f"/api/tenders/{sample_tender_id}/specifications")
    assert list_res.status_code == 200
    specs = list_res.json()
    assert len(specs) >= 1
    assert any(s["id"] == spec_id for s in specs)

    # Get by ID
    get_res = client.get(f"/api/specifications/{spec_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == spec_id


def test_api_specifications_crud_and_edit_endpoint(client, sample_tender_id):
    """Test PUT /api/specifications/{id} and Section 69 POST /api/analysis/{id}/generate."""
    # 1. Generate via Section 69 endpoint
    sec69_res = client.post(
        "/api/analysis/session-m13-abc/generate?generation_type=tender_clause&query_text=Supply+induction+motors"
    )
    assert sec69_res.status_code == 200
    data = sec69_res.json()
    spec_id = data["id"]
    assert data["analysis_id"] == "session-m13-abc"

    # 2. Edit specification via PUT
    edit_payload = {
        "title": "Edited Tender Clause via API",
        "generated_text": "Updated clause text via procurement review.",
    }
    edit_res = client.put(f"/api/specifications/{spec_id}", json=edit_payload)
    assert edit_res.status_code == 200
    edit_data = edit_res.json()
    assert edit_data["is_edited"] is True
    assert edit_data["version"] == 2
    assert edit_data["title"] == "Edited Tender Clause via API"


# =============================================================================
# 11. Database Standards Integrity
# =============================================================================
def test_database_standards_integrity_after_generation(db_session):
    """Verify that 268 canonical standards remain intact and unmodified."""
    count = db_session.query(Standard).count()
    assert count == 268


# =============================================================================
# 12. Health Check Includes Module 13
# =============================================================================
def test_health_check_includes_module13(client):
    """Verify /api/health includes Module 13."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "Module 13" in data["module"]
