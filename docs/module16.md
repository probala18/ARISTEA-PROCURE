# Module 16 — Evaluation and Metrics

## Status

Complete. Metrics are calculated only from the supplied
`csvfiles/query_dataset.json` and actual `RecommendationEngine` outputs.

## Implementation

- `backend/app/services/evaluation/service.py` runs the complete dataset.
- `backend/app/services/evaluation/schemas.py` defines transparent metric and
  per-query result contracts.
- `backend/app/api/evaluations.py` exposes `POST /api/evaluations/run`.
- Existing `EvaluationQuery` and `EvaluationResult` tables store benchmark
  metadata and observed results.
- `tests/test_module16_evaluation.py` protects dataset usage, persistence,
  unsupported-metric handling, and route registration.

## Calculated metrics

- Exact intent accuracy.
- Exact clarification accuracy.
- Out-of-scope accuracy.
- Evidence availability rate based on actual response evidence.
- Mean recommendation latency measured with `perf_counter`.

Each metric reports numerator, denominator, status, and a note.

## Unknown metrics

Precision@1, Precision@3, Recall@5, and MRR are `UNKNOWN`. The supplied
dataset has no structured relevant-standard labels or graded relevance
judgments. The legacy evaluation scripts contain hard-coded standard targets;
those targets are deliberately not treated as Module 16 ground truth.

## Data integrity and uncertainty

The runner reuses the existing recommendation service and does not modify
canonical standards, relationships, versions, compliance records, tender
evidence, or specifications. `PRIMARY` and `confidence_score` retain their
existing internal-only meanings. Evaluation metrics describe this benchmark
run; they are not probabilities, legal certainty, correctness percentages, or
official BIS claims.

## API

`POST /api/evaluations/run`

Request:

```json
{"dataset_path": "csvfiles/query_dataset.json", "persist_results": true}
```

The path is optional and defaults to the supplied repository dataset. The
response includes the run ID, resolved dataset path, metrics, and one observed
result per query.

## Limitations

- Evaluation is synchronous and process-local at request time.
- Latency depends on the local runtime and database.
- Standard-level retrieval metrics require a future structured relevance
  annotation set; no such annotation is invented here.

## Verification Results

The actual benchmark run used the repository database and all 14 records in
`csvfiles/query_dataset.json`:

| Metric | Actual result |
|---|---:|
| Exact intent accuracy | 9/14 (64.29%) |
| Clarification accuracy | 14/14 (100%) |
| Out-of-scope behavior agreement | 14/14 (100%) |
| Evidence availability rate | 14/14 (100%) |
| Mean recommendation latency | 8.713 ms |
| Precision@1 | UNKNOWN |
| Precision@3 | UNKNOWN |
| Recall@5 | UNKNOWN |
| MRR | UNKNOWN |

Focused Module 16 tests: **3 passed, 0 failed**.  
Full cumulative regression: **191 passed, 0 failed** with 463 warnings.  
Ingestion/provenance validation: **all checks passed**.
