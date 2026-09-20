from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import validate_dataset_path
from backend.app.services.evaluation import EvaluationService
from backend.app.services.evaluation.schemas import EvaluationRunRequest, EvaluationSummary

evaluations_router = APIRouter(prefix="/evaluations", tags=["Evaluation & Metrics"])


@evaluations_router.post("/run", response_model=EvaluationSummary)
def run_evaluation(
    payload: EvaluationRunRequest,
    db: Session = Depends(get_db),
) -> EvaluationSummary:
    """Run the supplied benchmark dataset against current recommendation outputs."""
    try:
        validate_dataset_path(payload.dataset_path)
    except ValueError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(exc))
    return EvaluationService(db).run(
        dataset_path=payload.dataset_path,
        persist_results=payload.persist_results,
    )
