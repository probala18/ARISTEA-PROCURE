"""Module 14 acceptance tests for FastAPI integration and asynchronous jobs."""
import os
import sys
import time
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.main import app
from backend.app.core.database import get_engine
import backend.app.api.jobs as jobs_api


client = TestClient(app)


@pytest.fixture(autouse=True)
def use_test_database(monkeypatch):
    """Run worker threads against the same SQLite database as the test suite."""
    test_session_local = sessionmaker(bind=get_engine("sqlite:///./sih_bis.db"))
    monkeypatch.setattr(jobs_api, "SessionLocal", test_session_local)


def _poll_job(job_id: str, timeout: float = 10.0):
    deadline = time.monotonic() + timeout
    response = None
    while time.monotonic() < deadline:
        response = client.get(f"/api/jobs/{job_id}")
        assert response.status_code == 200
        payload = response.json()
        if payload["status"] in {"COMPLETED", "FAILED"}:
            return payload
        time.sleep(0.05)
    raise AssertionError(f"Job did not finish: {response.json() if response else None}")


def test_health_reports_module14_and_async_jobs():
    response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["modules"]["module14"] == "operational"
    assert payload["async_jobs"]["status"] == "operational"
    assert payload["async_jobs"]["status_endpoint"] == "/api/jobs/{job_id}"


def test_validation_errors_have_stable_shape():
    response = client.post(
        "/api/jobs/specifications/generate",
        json={"generation_type": "not-a-supported-generation-type"},
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["error"] == "validation_error"
    assert payload["detail"] == "Request validation failed."
    assert isinstance(payload["fields"], list)


def test_unknown_job_returns_not_found():
    response = client.get("/api/jobs/not-a-real-job")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_async_tender_upload_rejects_unsupported_and_empty_files():
    unsupported = client.post(
        "/api/jobs/tenders/upload",
        files={"file": ("tender.csv", b"valid enough content", "text/csv")},
    )
    empty = client.post(
        "/api/jobs/tenders/upload",
        files={"file": ("tender.txt", b"short", "text/plain")},
    )

    assert unsupported.status_code == 400
    assert empty.status_code == 400


def test_async_tender_upload_persists_and_completes():
    tender_text = (
        "TENDER SPECIFICATION\n"
        "SECTION 1: TECHNICAL SPECIFICATIONS\n"
        "1.1 Equipment shall comply with IS 12615:2018.\n"
    )
    response = client.post(
        "/api/jobs/tenders/upload",
        files={"file": ("module14.txt", tender_text.encode("utf-8"), "text/plain")},
        data={"tender_number": f"M14-ASYNC-{uuid4().hex[:8]}", "title": "Module 14 Tender"},
    )

    assert response.status_code == 202
    submission = response.json()
    assert submission["job_type"] == "tender_upload"
    assert submission["status"] in {"QUEUED", "RUNNING", "COMPLETED"}

    result = _poll_job(submission["id"])
    assert result["status"] == "COMPLETED"
    assert result["result"]["status"] == "COMPLETED"
    assert result["result"]["tender_id"] > 0


def test_async_specification_generation_returns_pollable_job():
    response = client.post(
        "/api/jobs/specifications/generate",
        json={"query_text": "induction motor", "generation_type": "technical_specification"},
    )

    assert response.status_code == 202
    submission = response.json()
    assert submission["job_type"] == "specification_generation"
    assert submission["status_url"] == f"/api/jobs/{submission['id']}"

    result = _poll_job(submission["id"])
    assert result["status"] in {"COMPLETED", "FAILED"}
    if result["status"] == "FAILED":
        assert result["error"]
        assert result["result"] is None
