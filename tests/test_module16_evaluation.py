import json
import sys
from pathlib import Path

import pytest
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.core.database import Base, get_engine
from backend.app.models import EvaluationQuery, EvaluationResult
from backend.app.services.evaluation import EvaluationService


@pytest.fixture()
def evaluation_session(tmp_path):
    engine = get_engine(f"sqlite:///{tmp_path / 'evaluation.db'}")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def test_evaluation_uses_dataset_and_marks_unsupported_metrics_unknown(evaluation_session):
    summary = EvaluationService(evaluation_session).run(persist_results=True)

    assert summary.total_queries == 14
    assert summary.metrics["intent_accuracy"].status == "CALCULATED"
    assert summary.metrics["mean_latency_ms"].status == "CALCULATED"
    assert summary.metrics["mrr"].status == "UNKNOWN"
    assert "no structured relevant-standard labels" in summary.metrics["mrr"].note.lower()
    assert evaluation_session.query(EvaluationQuery).count() == 14
    assert evaluation_session.query(EvaluationResult).count() == 14


def test_evaluation_does_not_use_legacy_hardcoded_targets(evaluation_session, tmp_path):
    dataset = [
        {
            "id": "CUSTOM-1",
            "query": "What is the weather in Delhi today?",
            "category": "custom",
            "expected_intent": "OUT_OF_SCOPE",
            "clarification_expected": False,
            "expected_retrieval_operations": [],
            "expected_evidence": "Out of scope response",
            "answerable_with_current_data": True,
        }
    ]
    path = tmp_path / "dataset.json"
    path.write_text(json.dumps(dataset), encoding="utf-8")

    summary = EvaluationService(evaluation_session).run(
        dataset_path=str(path),
        persist_results=False,
    )

    assert summary.total_queries == 1
    assert summary.results[0].query_id == "CUSTOM-1"
    assert summary.results[0].expected_out_of_scope is True
    assert summary.metrics["intent_accuracy"].denominator == 1


def test_evaluation_endpoint_is_exposed():
    from backend.app.main import app

    paths = set(app.openapi()["paths"])
    assert "/api/evaluations/run" in paths
