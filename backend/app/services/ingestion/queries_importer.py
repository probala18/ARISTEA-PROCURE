"""
Benchmark Evaluation Queries Importer for PS 26108.
Imports query_dataset.json into evaluation_queries table.
"""
import os
import json
import logging
from backend.app.models.evaluation import EvaluationQuery
from backend.app.services.ingestion.context import IngestionContext
from backend.app.core.normalizers import clean_text

logger = logging.getLogger("ingestion.queries")

def import_evaluation_queries(file_path: str, ctx: IngestionContext) -> int:
    """Import query_dataset.json benchmark queries."""
    if not os.path.exists(file_path):
        logger.warning(f"query_dataset.json not found at: {file_path}")
        return 0

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    count = 0
    for item in data:
        qid = clean_text(item.get("id"))
        qtext = clean_text(item.get("query"))
        if not qid or not qtext:
            continue

        existing = ctx.session.query(EvaluationQuery).filter_by(query_id=qid).first()
        if existing:
            existing.query_text = qtext
            existing.category = clean_text(item.get("category"))
            existing.expected_intent = clean_text(item.get("expected_intent")) or "UNKNOWN"
            existing.clarification_expected = bool(item.get("clarification_expected", False))
            existing.expected_retrieval_operations = item.get("expected_retrieval_operations")
            existing.expected_evidence = clean_text(item.get("expected_evidence"))
            existing.answerable_with_current_data = bool(item.get("answerable_with_current_data", True))
        else:
            eq = EvaluationQuery(
                query_id=qid,
                query_text=qtext,
                category=clean_text(item.get("category")),
                expected_intent=clean_text(item.get("expected_intent")) or "UNKNOWN",
                clarification_expected=bool(item.get("clarification_expected", False)),
                expected_retrieval_operations=item.get("expected_retrieval_operations"),
                expected_evidence=clean_text(item.get("expected_evidence")),
                answerable_with_current_data=bool(item.get("answerable_with_current_data", True)),
            )
            ctx.session.add(eq)
            count += 1
            ctx.stats.queries_created += 1

    ctx.stats.files_processed["query_dataset.json"] = len(data)
    logger.info(f"Imported {count} evaluation benchmark queries from query_dataset.json")
    return count
