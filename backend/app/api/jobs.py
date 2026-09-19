"""FastAPI endpoints for bounded asynchronous API jobs (Module 14)."""
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.app.core.database import SessionLocal, get_db
from backend.app.services.job_schemas import (
    JobResponse,
    JobSubmissionResponse,
    job_response,
)
from backend.app.services.jobs import job_registry
from backend.app.services.specification_generator import (
    SpecificationGenerationRequest,
    SpecificationService,
)
from backend.app.services.tender_engine import TenderEngineService

router = APIRouter(prefix="/jobs", tags=["Asynchronous Jobs API"])
jobs_router = router


def _submission(record: object) -> JobSubmissionResponse:
    return JobSubmissionResponse(
        id=record.id,
        job_type=record.job_type,
        status=record.status,
        status_url=f"/api/jobs/{record.id}",
        created_at=record.created_at,
    )


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: str):
    record = job_registry.get(job_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return job_response(record)


@router.post("/tenders/upload", response_model=JobSubmissionResponse, status_code=202)
async def submit_tender_upload(
    file: UploadFile = File(..., description="Tender document file (PDF, DOCX, TXT)"),
    tender_number: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    organization: Optional[str] = Form(None),
):
    filename = file.filename or "tender.txt"
    extension = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if extension not in {"pdf", "docx", "txt"}:
        raise HTTPException(status_code=400, detail="Supported tender formats are PDF, DOCX, and TXT.")
    content = await file.read()
    if len(content) < 10:
        raise HTTPException(status_code=400, detail="Uploaded tender file is empty or corrupted.")

    def work():
        db = SessionLocal()
        try:
            tender = TenderEngineService(db).process_document(
                file_content=content,
                filename=filename,
                tender_number=tender_number,
                title=title,
                organization=organization,
            )
            return {"tender_id": tender.id, "status": tender.status}
        finally:
            db.close()

    try:
        return _submission(job_registry.submit("tender_upload", work))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.post("/specifications/generate", response_model=JobSubmissionResponse, status_code=202)
def submit_specification_generation(request: SpecificationGenerationRequest):
    def work():
        db = SessionLocal()
        try:
            return SpecificationService(db).generate_specification(request).model_dump(mode="json")
        finally:
            db.close()

    try:
        return _submission(job_registry.submit("specification_generation", work))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
