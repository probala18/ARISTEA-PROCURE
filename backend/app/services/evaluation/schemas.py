from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EvaluationMetric(BaseModel):
    value: Optional[float] = None
    numerator: Optional[int] = None
    denominator: Optional[int] = None
    status: str = "CALCULATED"
    note: Optional[str] = None


class EvaluationQueryResult(BaseModel):
    query_id: str
    expected_intent: str
    actual_intent: Optional[str] = None
    intent_match: Optional[bool] = None
    clarification_expected: bool
    clarification_actual: Optional[bool] = None
    clarification_match: Optional[bool] = None
    expected_out_of_scope: bool
    actual_out_of_scope: bool
    out_of_scope_match: Optional[bool] = None
    response_evidence_count: int = 0
    evidence_available: Optional[bool] = None
    latency_ms: float
    retrieved_standards: List[str] = Field(default_factory=list)
    error: Optional[str] = None


class EvaluationSummary(BaseModel):
    test_run_id: str
    dataset_path: str
    total_queries: int
    metrics: Dict[str, EvaluationMetric]
    results: List[EvaluationQueryResult] = Field(default_factory=list)
    disclaimer: str = (
        "Metrics are measured on the supplied benchmark dataset and actual "
        "system outputs. They are not probabilities, legal certainty, or "
        "official BIS performance claims."
    )


class EvaluationRunRequest(BaseModel):
    dataset_path: Optional[str] = None
    persist_results: bool = True
