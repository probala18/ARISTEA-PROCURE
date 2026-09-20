# Module 16 Scope — Evidence-Grounded Evaluation and Metrics

## Objective

Evaluate the current system against the supplied `csvfiles/query_dataset.json`
and actual service outputs without fabricating relevance labels or benchmark
results.

## Evidence available

- The supplied dataset contains 14 queries.
- It explicitly labels expected intent, clarification behavior, expected
  retrieval operations, expected evidence descriptions, and answerability.
- Existing recommendation outputs expose detected intent, ambiguity,
  out-of-scope status, evidence records, returned standards, and confidence
  labels.
- The dataset does **not** contain structured relevant-standard IDs or
  graded relevance judgments.

## Exact scope

- Run every supplied query through the existing `RecommendationEngine`.
- Measure exact intent agreement.
- Measure exact clarification agreement.
- Measure out-of-scope agreement.
- Measure whether actual response evidence is present.
- Measure mean latency around the live recommendation call.
- Persist per-query outputs using the existing evaluation tables.
- Expose a synchronous evaluation API.

## Explicitly unavailable metrics

Precision@1, Precision@3, Recall@5, and MRR are returned as
`UNKNOWN` because the supplied dataset does not provide structured
relevant-standard labels. Existing scripts with hard-coded standard targets are
not used as Module 16 ground truth.

## Out of scope

- Inventing standard relevance targets from prose.
- Claiming probability, legal certainty, or official BIS performance.
- External datasets, web data, scraping, or fabricated tender labels.
- Module 17 or any subsequent module.
