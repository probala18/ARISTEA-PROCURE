"""API schemas for asynchronous Module 14 jobs."""
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel

from backend.app.services.jobs import JobStatus


class JobResponse(BaseModel):
    id: str
    job_type: str
    status: JobStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class JobSubmissionResponse(BaseModel):
    id: str
    job_type: str
    status: JobStatus
    status_url: str
    created_at: datetime


def job_response(record: Any) -> JobResponse:
    return JobResponse(
        id=record.id,
        job_type=record.job_type,
        status=record.status,
        result=record.result,
        error=record.error,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )
