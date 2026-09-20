"""Evidence-grounded Module 16 evaluation runner."""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from backend.app.models.evaluation import EvaluationQuery, EvaluationResult
from backend.app.services.recommendation import RecommendationEngine, RecommendationRequest
from backend.app.services.evaluation.schemas import (
    EvaluationMetric,
    EvaluationQueryResult,
    EvaluationSummary,
)
from backend.app.core.config import settings


REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_DATASET_PATH = REPO_ROOT / "csvfiles" / "query_dataset.json"


class EvaluationService:
    """Runs only metrics supported by explicit dataset labels and live outputs."""

    def __init__(self, session: Session):
        self.session = session
        self.recommendation_engine = RecommendationEngine(session)

    def run(
        self,
        dataset_path: Optional[str] = None,
        persist_results: bool = True,
    ) -> EvaluationSummary:
        path = self._resolve_dataset_path(dataset_path)
        dataset = self._load_dataset(path)
        if len(dataset) > settings.MAX_EVALUATION_QUERIES:
            raise ValueError("Evaluation dataset exceeds the configured query limit.")
        test_run_id = str(uuid4())
        results: List[EvaluationQueryResult] = []

        for item in dataset:
            result = self._evaluate_query(item)
            results.append(result)
            if persist_results:
                self._persist_result(item, result, test_run_id)

        if persist_results:
            self.session.commit()

        return EvaluationSummary(
            test_run_id=test_run_id,
            dataset_path=str(path),
            total_queries=len(results),
            metrics=self._metrics(results),
            results=results,
        )

    def _evaluate_query(self, item: Dict[str, Any]) -> EvaluationQueryResult:
        query_id = str(item.get("id", "UNKNOWN"))
        query_text = str(item.get("query", ""))
        expected_intent = str(item.get("expected_intent", "UNKNOWN"))
        clarification_expected = bool(item.get("clarification_expected", False))
        expected_out_of_scope = expected_intent == "OUT_OF_SCOPE"

        started = time.perf_counter()
        try:
            response = self.recommendation_engine.recommend(
                RecommendationRequest(query_text=query_text, include_allied=True)
            )
            latency_ms = (time.perf_counter() - started) * 1000
            actual_intent = response.detected_intent.value
            clarification_actual = response.is_ambiguous
            evidence_count = len(response.evidence_summary)
            retrieved = self._standard_ids(response)
            intent_match = actual_intent == expected_intent
            clarification_match = clarification_actual == clarification_expected
            out_of_scope_match = response.is_out_of_scope == expected_out_of_scope
            evidence_available = bool(evidence_count) if not expected_out_of_scope else not bool(evidence_count)
            return EvaluationQueryResult(
                query_id=query_id,
                expected_intent=expected_intent,
                actual_intent=actual_intent,
                intent_match=intent_match,
                clarification_expected=clarification_expected,
                clarification_actual=clarification_actual,
                clarification_match=clarification_match,
                expected_out_of_scope=expected_out_of_scope,
                actual_out_of_scope=response.is_out_of_scope,
                out_of_scope_match=out_of_scope_match,
                response_evidence_count=evidence_count,
                evidence_available=evidence_available,
                latency_ms=round(latency_ms, 3),
                retrieved_standards=retrieved,
            )
        except Exception as exc:
            return EvaluationQueryResult(
                query_id=query_id,
                expected_intent=expected_intent,
                clarification_expected=clarification_expected,
                expected_out_of_scope=expected_out_of_scope,
                actual_out_of_scope=False,
                latency_ms=round((time.perf_counter() - started) * 1000, 3),
                error=str(exc),
            )

    @staticmethod
    def _standard_ids(response: Any) -> List[str]:
        candidates = list(response.primary_standards)
        candidates.extend(response.candidate_spectrum)
        candidates.extend(response.superseded_standards)
        for group in response.allied_standards.values():
            candidates.extend(group)
        seen = set()
        identifiers = []
        for candidate in candidates:
            identifier = candidate.standard_id
            if identifier not in seen:
                seen.add(identifier)
                identifiers.append(identifier)
        return identifiers

    def _persist_result(
        self,
        item: Dict[str, Any],
        result: EvaluationQueryResult,
        test_run_id: str,
    ) -> None:
        query_id = str(item.get("id", "UNKNOWN"))
        query = self.session.query(EvaluationQuery).filter_by(query_id=query_id).first()
        if query is None:
            query = EvaluationQuery(
                query_id=query_id,
                query_text=str(item.get("query", "")),
                category=item.get("category"),
                expected_intent=str(item.get("expected_intent", "UNKNOWN")),
                clarification_expected=bool(item.get("clarification_expected", False)),
                expected_retrieval_operations=item.get("expected_retrieval_operations"),
                expected_evidence=item.get("expected_evidence"),
                answerable_with_current_data=bool(item.get("answerable_with_current_data", True)),
            )
            self.session.add(query)
            self.session.flush()

        self.session.add(
            EvaluationResult(
                evaluation_query_id=query.id,
                test_run_id=test_run_id,
                actual_intent=result.actual_intent,
                actual_retrieved_standards=result.retrieved_standards,
                latency_ms=result.latency_ms,
                pass_fail=bool(
                    result.intent_match
                    and result.clarification_match
                    and result.out_of_scope_match
                ) if result.error is None else False,
                error_details=result.error,
            )
        )

    @staticmethod
    def _metrics(results: List[EvaluationQueryResult]) -> Dict[str, EvaluationMetric]:
        total = len(results)
        successful = [r for r in results if r.error is None]

        def boolean_metric(name: str, values: List[Optional[bool]]) -> EvaluationMetric:
            known = [value for value in values if value is not None]
            if not known:
                return EvaluationMetric(status="UNKNOWN", note="No verified observations.")
            numerator = sum(1 for value in known if value)
            return EvaluationMetric(
                value=round(numerator / len(known), 4),
                numerator=numerator,
                denominator=len(known),
                status="CALCULATED",
                note=name,
            )

        metrics = {
            "intent_accuracy": boolean_metric("Exact expected_intent comparison.", [r.intent_match for r in successful]),
            "clarification_accuracy": boolean_metric("Exact clarification_expected comparison.", [r.clarification_match for r in successful]),
            "out_of_scope_accuracy": boolean_metric("Expected out-of-scope behavior comparison for every query.", [r.out_of_scope_match for r in successful]),
            "evidence_availability_rate": boolean_metric("Evidence presence measured from actual response.", [r.evidence_available for r in successful]),
        }
        if successful:
            latencies = [r.latency_ms for r in successful]
            metrics["mean_latency_ms"] = EvaluationMetric(
                value=round(sum(latencies) / len(latencies), 3),
                numerator=len(latencies),
                denominator=len(latencies),
                status="CALCULATED",
                note="Measured with perf_counter around the recommendation service.",
            )
        else:
            metrics["mean_latency_ms"] = EvaluationMetric(
                status="UNKNOWN",
                note="No successful system outputs were available.",
            )

        unsupported = (
            "query_dataset.json has no structured relevant-standard labels; "
            "precision, recall, and MRR are not calculated."
        )
        for name in ("precision_at_1", "precision_at_3", "recall_at_5", "mrr"):
            metrics[name] = EvaluationMetric(status="UNKNOWN", note=unsupported)
        return metrics

    @staticmethod
    def _resolve_dataset_path(dataset_path: Optional[str]) -> Path:
        path = Path(dataset_path) if dataset_path else DEFAULT_DATASET_PATH
        if not path.is_absolute():
            path = REPO_ROOT / path
        if not path.exists():
            raise FileNotFoundError(f"Evaluation dataset not found: {path}")
        return path.resolve()

    @staticmethod
    def _load_dataset(path: Path) -> List[Dict[str, Any]]:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, list):
            raise ValueError("Evaluation dataset must contain a JSON array.")
        return data
