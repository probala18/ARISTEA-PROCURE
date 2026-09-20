from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.main import app


def test_application_surface_is_deployable():
    with TestClient(app) as client:
        assert client.get("/api/health").status_code == 200
        assert client.get("/openapi.json").status_code == 200
        assert client.get("/api/health").headers["x-content-type-options"] == "nosniff"


def test_readiness_route_is_present():
    assert "/api/ready" in app.openapi()["paths"]


def test_deployment_files_and_no_secret_example():
    root = Path(__file__).resolve().parents[1]
    assert (root / "requirements.txt").exists()
    assert (root / "Dockerfile").exists()
    env_example = (root / ".env.example").read_text(encoding="utf-8")
    assert "<password>" in env_example
    assert "postgres" in env_example.lower()
    assert "postgres://postgres:postgres" not in env_example.lower()
