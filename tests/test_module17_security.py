import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.core.security import validate_dataset_path, validate_upload
from backend.app.main import app
from backend.app.services.job_schemas import job_response
from backend.app.services.jobs import JobRecord, JobStatus


def test_upload_rejects_empty_oversized_and_traversal_inputs():
    with pytest.raises(ValueError):
        validate_upload("../tender.txt", b"valid", {"txt"}, 100)
    with pytest.raises(ValueError):
        validate_upload("tender.txt", b"", {"txt"}, 100)
    with pytest.raises(ValueError):
        validate_upload("tender.txt", b"x" * 101, {"txt"}, 100)


def test_upload_accepts_supported_safe_filename():
    assert validate_upload("tender.txt", b"valid", {"txt"}, 100) == "tender.txt"


def test_evaluation_dataset_boundary_rejects_arbitrary_paths():
    validate_dataset_path(None)
    validate_dataset_path("csvfiles/query_dataset.json")
    with pytest.raises(ValueError):
        validate_dataset_path("../secrets.json")
    with pytest.raises(ValueError):
        validate_dataset_path("csvfiles/other.json")


def test_security_headers_and_evaluation_route_are_exposed():
    paths = set(app.openapi()["paths"])
    assert "/api/evaluations/run" in paths
    assert "/api/ready" in paths


def test_failed_job_response_does_not_expose_internal_exception():
    record = JobRecord("test")
    record.status = JobStatus.FAILED
    record.error = "postgres://user:password@example.invalid/database"
    response = job_response(record)
    assert response.error == "Asynchronous job failed."
    assert "password" not in response.model_dump_json()
