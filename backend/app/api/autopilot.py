"""
FastAPI Router for ARISTEA Autopilot.
- POST /api/autopilot/run     Streams pipeline progress as Server-Sent Events, ending with the tender package.
- POST /api/autopilot/export  Renders a finished tender package as DOCX.
"""
import json
from typing import Any, Dict, Iterator, Optional

from fastapi import APIRouter, Body
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field

from backend.app.core.database import SessionLocal
from backend.app.services.autopilot import AutopilotOrchestrator, build_tender_docx

router = APIRouter(tags=["Autopilot API"])
autopilot_router = router


class AutopilotRunRequest(BaseModel):
    need: str = Field(..., min_length=3, max_length=2000, description="Procurement need in natural language")
    language: Optional[str] = None


def _stream(need: str, language: Optional[str]) -> Iterator[str]:
    db = SessionLocal()
    try:
        for event in AutopilotOrchestrator(db).run(need, language):
            yield f"data: {json.dumps(event, default=str)}\n\n"
    except Exception as exc:
        yield f"data: {json.dumps({'type': 'error', 'detail': str(exc)})}\n\n"
    finally:
        db.close()


@router.post("/autopilot/run")
def run_autopilot(payload: AutopilotRunRequest):
    return StreamingResponse(
        _stream(payload.need.strip(), payload.language),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/autopilot/export")
def export_autopilot(result: Dict[str, Any] = Body(...)):
    content = build_tender_docx(result)
    run_id = str(result.get("run_id") or "tender").replace('"', "")
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="ARISTEA-{run_id}.docx"'},
    )
