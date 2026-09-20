"""Module 19 end-to-end verification of the existing pipeline."""

import json
import os
import sys
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.api import jobs as jobs_api
from backend.app.core.database import get_db, get_engine
from backend.app.main import app
from backend.app.services.recommendation import RecommendationEngine, RecommendationRequest, StandardRole
from backend.app.services.specification_generator import SpecificationGenerator
from backend.app.services.tender_audit import TenderAuditService
from backend.app.services.tender_engine import TenderEngineService


CANONICAL_DB = "sqlite:///./sih_bis.db"
QUERY_DATASET = Path(__file__).resolve().parents[1] / "csvfiles" / "query_dataset.json"


def _session():
    return sessionmaker(bind=get_engine(CANONICAL_DB))()


def test_supplied_queries_cover_direct_semantic_and_ambiguous_paths():
    dataset = {item["id"]: item for item in json.loads(QUERY_DATASET.read_text(encoding="utf-8"))}
    assert {"Q01", "Q08", "Q11"} <= dataset.keys()

    session = _session()
    try:
        engine = RecommendationEngine(session)
        direct = engine.recommend(RecommendationRequest(query_text=dataset["Q01"]["query"]))
        semantic = engine.recommend(RecommendationRequest(query_text=dataset["Q11"]["query"]))
        ambiguous = engine.recommend(RecommendationRequest(query_text=dataset["Q08"]["query"]))

        assert direct.primary_standards[0].is_number == "IS 694"
        assert direct.primary_standards[0].evidence[0].source_dataset
        assert semantic.primary_standards[0].is_number == "IS 694"
        assert semantic.primary_standards[0].role == StandardRole.PRIMARY
        assert semantic.primary_standards[0].evidence
        assert ambiguous.is_ambiguous is True
        assert ambiguous.primary_standards == []
        assert ambiguous.clarification_prompt is not None
        assert all(candidate.role == StandardRole.CONDITIONAL for candidate in ambiguous.candidate_spectrum)
    finally:
        session.close()


def test_version_and_compliance_api_retain_verified_evidence():
    session = _session()
    app.dependency_overrides[get_db] = lambda: session
    client = TestClient(app)
    try:
        version_response = client.get("/api/standards/IS 694:2010/versions")
        compliance_response = client.get("/api/standards/IS 694:2010/compliance")

        assert version_response.status_code == 200
        version = version_response.json()
        assert version["status"] == "CURRENT"
        assert version["source_file"] == "standards.csv"
        assert version["supersession"]["superseded_by"] == []
        assert version["disclaimer"]

        assert compliance_response.status_code == 200
        compliance = compliance_response.json()
        assert compliance["requirement_level"] in {"MANDATORY", "VOLUNTARY", "CONDITIONAL", "UNKNOWN"}
        assert compliance["certification_records"] or compliance["qco_records"]
        assert all(record["source_dataset"] for record in compliance["certification_records"])
        assert all(record["source_dataset"] for record in compliance["qco_records"])
        assert "not a probability" in compliance["disclaimer"].lower()
    finally:
        app.dependency_overrides.pop(get_db, None)
        session.close()


def test_tender_audit_to_specification_preserves_evidence():
    session = _session()
    try:
        content = (
            "SECTION 1: TECHNICAL SPECIFICATIONS\n"
            "Clause 1.1: Motors shall comply with IS 325.\n"
            "Clause 1.2: Cables shall conform to IS 694.\n"
            "Clause 1.3: Supplier shall document the applicable requirements.\n"
        ).encode("utf-8")
        tender = TenderEngineService(session).process_document(
            file_content=content,
            filename="module19-tender.txt",
            tender_number=f"M19-{uuid4().hex[:10]}",
            title="Module 19 Verification Tender",
        )

        audit = TenderAuditService(session).audit_tender(tender.id)
        text, structured, provenance = SpecificationGenerator(session).generate_technical_specification(tender.id)

        assert audit.tender_id == tender.id
        assert "IS 12615" in text
        assert structured["applicable_standards"]
        assert provenance
        assert all(item.get("source_dataset") or item.get("source_file") for item in provenance)
        assert "Insufficient verified evidence" in text or "UNKNOWN" in text or "IS 12615" in text
    finally:
        session.close()


def test_operational_surface_and_openapi_are_exposed():
    session_factory = sessionmaker(bind=get_engine(CANONICAL_DB))
    original_session_local = jobs_api.SessionLocal
    jobs_api.SessionLocal = session_factory
    from backend.app import main as main_module

    original_main_session_local = main_module.SessionLocal
    main_module.SessionLocal = session_factory
    client = TestClient(app)
    try:
        health = client.get("/api/health")
        ready = client.get("/api/ready")
        openapi = client.get("/openapi.json")
        invalid = client.post("/api/jobs/specifications/generate", json={"generation_type": "invalid"})

        assert health.status_code == 200
        assert ready.status_code == 200
        assert ready.json()["status"] == "ready"
        assert openapi.status_code == 200
        paths = openapi.json()["paths"]
        assert len(paths) == 37
        assert "/api/health" in paths
        assert "/api/ready" in paths
        assert invalid.status_code == 422
        assert invalid.json()["error"] == "validation_error"
        assert health.headers["x-content-type-options"] == "nosniff"
        assert health.headers["x-frame-options"] == "DENY"
        assert health.headers["referrer-policy"] == "no-referrer"
    finally:
        main_module.SessionLocal = original_main_session_local
        jobs_api.SessionLocal = original_session_local
