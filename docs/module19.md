# Module 19 — Final End-to-End Verification & Demo Readiness

## Scope

Module 19 verifies the existing ARISTEA-PROCURE pipeline without changing
domain logic, supplied datasets, evaluation labels, retrieval behavior, or
deployment architecture. It covers the supported:

`UNDERSTAND -> RECOMMEND -> CONNECT -> VERIFY -> AUDIT -> GENERATE`

flow using the canonical SQLite database and the supplied project datasets.

## Verified flows

### Recommendation scenarios

The supplied `csvfiles/query_dataset.json` records were used for:

- Q01 direct lookup: `IS 694:2010` resolves to `IS 694` with standards
  provenance.
- Q11 semantic product wording: flexible domestic wiring resolves to `IS 694`
  as the internal `PRIMARY` recommendation with evidence.
- Q08 ambiguous cable query: no unjustified primary is selected; conditional
  candidates and a clarification prompt are returned.

`PRIMARY` and `confidence_score` retain their existing internal-only
disclaimers.

### Version and compliance

The standards API was verified for `IS 694:2010`:

- Version state: `CURRENT`.
- Version provenance: `standards.csv`.
- Supersession output is relationship/data based; no title-similarity
  successor was inferred.
- Compliance returned dataset-backed certification/QCO evidence and a
  bounded requirement level.
- Compliance output retained its disclaimer that confidence is not a
  probability or legal certainty.

### Tender, audit, and specification generation

A supported plain-text tender was processed through:

1. Tender parsing and section/requirement extraction.
2. Standard-reference extraction.
3. Tender audit.
4. Version and compliance-aware specification generation.

The superseded `IS 325` reference resolved through the verified relationship
to `IS 12615`. Generated output retained provenance and used existing
uncertainty behavior rather than inventing unsupported limits or mandates.
Existing Module 12 and Module 13 tests additionally verify that missing
citations are not automatically treated as statutory non-compliance and that
unlisted standards remain evidence gaps.

### Speech and asynchronous jobs

Existing Module 10 tests verify the offline benchmark WAV STT provider,
shared text/voice recommendation logic, TTS behavior, and the read-only
database property of voice queries.

Existing Module 14 tests verify job submission, polling, completion/failure
states, bounded in-process execution, validation errors, and safe job
responses. No distributed queue was introduced.

### Operational surface

Verified locally:

- `GET /api/health`
- `GET /api/ready` with the SQLite test database override
- `GET /openapi.json`
- security headers
- stable request-validation responses
- registered API routes

The configured default readiness check uses PostgreSQL. A live PostgreSQL
server was not available in this environment, so no live PostgreSQL readiness
claim is made.

## Test results

### Module 19 focused tests

- **4 passed**
- **0 failed**

### Full regression

- **203 passed**
- **0 failed**
- **487 warnings**

### Modules 14–19 integration tests

- **26 passed**
- **0 failed**
- **30 warnings**

The Module 19 suite adds four cross-stage tests to the existing 22-test
Modules 14–18 integration selection.

### Ingestion and provenance

`scripts/validate_ingestion.py` passed:

| Dataset/entity | Count |
|---|---:|
| Standards | 268 |
| Relationships | 111 |
| Versions | 275 |
| QCO records | 710 |
| Certifications | 1,573 |
| Product licences | 75 |
| Ministry mappings | 28 |
| Evaluation queries | 14 |
| Core provenance coverage | 100% |

Explicit and derived relationships remained separated, and unlinked
relationship targets remained preserved as string references.

## Benchmark results

Module 16 methodology and labels were not changed. The recorded benchmark
remains:

- Intent accuracy: **9/14 (64.29%)**
- Clarification accuracy: **14/14 (100%)**
- Out-of-scope agreement: **14/14 (100%)**
- Evidence availability: **14/14 (100%)**
- Mean recommendation latency: **8.285 ms** in this verification run
- Precision@1: **UNKNOWN**
- Precision@3: **UNKNOWN**
- Recall@5: **UNKNOWN**
- MRR: **UNKNOWN**

The retrieval metrics remain `UNKNOWN` because the supplied dataset does not
contain structured relevant-standard labels.

The measured latency is an execution-time observation and differs from the
previous recorded 8.713 ms baseline; no benchmark labels or system tuning was
changed.

## API and security verification

The OpenAPI document was available at `/openapi.json` and exposed **33 API
paths**, including the health and readiness routes.

Security verification confirmed the existing headers:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: no-referrer`

Existing Module 17 tests continue to cover upload bounds, dataset-path
restriction, safe errors, configurable CORS, and non-disclosure of worker
exception details.

## Demo prerequisites

1. Use Python 3.13 as documented in the repository.
2. Install dependencies from `requirements.txt`.
3. Ensure the canonical database is available locally, or use the supplied
   SQLite database for the verified local demo path.
4. Use the supplied `csvfiles` datasets only.
5. Run migrations and ingestion explicitly when setting up a fresh database.
6. Start the API with the documented Uvicorn command.
7. Check `/api/health`, `/api/ready`, and `/openapi.json` before demonstrating
   API flows.

The benchmark WAV provider and mock TTS provider used by tests do not require
an external API key. Production speech providers may require their own local
models or provider configuration. PostgreSQL, Docker, cloud deployment,
monitoring, and external speech-provider execution were not claimed as
verified here.

## Limitations and remaining gaps

- Live PostgreSQL execution was not available.
- A Docker build was not executed in this verification.
- Cloud deployment and production monitoring were not verified.
- External speech-provider execution was not required or claimed.
- Retrieval relevance metrics remain `UNKNOWN` by design.
- Existing SQLAlchemy and Pydantic deprecation warnings remain.

## Changed files

- `tests/test_module19_end_to_end.py`
- `docs/module19.md`

No application behavior, supplied domain data, benchmark methodology, or
evaluation labels were changed.
