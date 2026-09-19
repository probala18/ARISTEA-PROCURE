"""Module 15 acceptance tests for lifecycle and readiness reliability."""
import os
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import backend.app.main as main_module
from backend.app.main import app
from backend.app.services.jobs import JobRegistry


class _HealthySession:
    def execute(self, statement):
        return 1

    def close(self):
        pass


class _UnavailableSession:
    def execute(self, statement):
        raise RuntimeError("database unavailable")

    def close(self):
        pass


def test_readiness_reports_database_ready(monkeypatch):
    monkeypatch.setattr(main_module, "SessionLocal", lambda: _HealthySession())

    response = TestClient(app).get("/api/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "database": "ready",
        "async_jobs": "available",
    }


def test_readiness_reports_database_unavailable(monkeypatch):
    monkeypatch.setattr(main_module, "SessionLocal", lambda: _UnavailableSession())

    response = TestClient(app).get("/api/ready")

    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "not_ready"
    assert payload["database"] == "unavailable"
    assert payload["async_jobs"] == "available"
    assert "database unavailable" in payload["detail"]


def test_readiness_is_exposed_in_openapi():
    response = TestClient(app).get("/openapi.json")

    assert response.status_code == 200
    assert "/api/ready" in response.json()["paths"]


def test_job_registry_shutdown_is_idempotent_and_rejects_new_work():
    registry = JobRegistry(max_workers=1, max_jobs=2)

    registry.shutdown()
    registry.shutdown()

    try:
        registry.submit("test", lambda: None)
    except RuntimeError as exc:
        assert "shut down" in str(exc)
    else:
        raise AssertionError("A shut-down registry accepted new work")


def test_application_lifespan_shuts_down_shared_registry(monkeypatch):
    calls = []

    class _Registry:
        def shutdown(self):
            calls.append("shutdown")

    monkeypatch.setattr(main_module, "job_registry", _Registry())

    with TestClient(app):
        pass

    assert calls == ["shutdown"]
