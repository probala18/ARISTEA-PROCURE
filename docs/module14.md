# Module 14 - FastAPI Integration

**Status:** Complete  
**Scope:** FastAPI API integration, validation, error handling, health
reporting, and asynchronous jobs. Module 15 was not started.

## 1. Overview

Module 14 hardens the FastAPI integration layer for ARISTEA-PROCURE. It
connects the existing standards, speech, tender, audit, and specification
services to a consistent API surface and adds bounded asynchronous execution
for operations that may take longer than a normal request.

Module 14 does not introduce a second business-logic implementation. Existing
service classes remain the source of truth; the API layer validates requests,
maps service failures to HTTP responses, and serializes results.

## 2. API Coverage

The application registers these router groups under `/api`:

- standards and knowledge graph endpoints;
- speech transcription, synthesis, and voice-query endpoints;
- tender upload, status, requirements, references, audit, and specification
  endpoints;
- specification generation, retrieval, editing, deletion, and analysis-session
  endpoints;
- asynchronous job submission and status endpoints.

The generated OpenAPI document exposes **31 API paths**, including the
standards, graph, speech, tender, specification, health, and asynchronous job
surfaces. Existing synchronous APIs remain available; Module 14 adds the
asynchronous surface without duplicating business logic.

The synchronous Module 13 endpoints remain available:

| Method | Endpoint |
|---|---|
| `POST` | `/api/specifications/generate` |
| `GET` | `/api/specifications/{id}` |
| `PUT` | `/api/specifications/{id}` |
| `DELETE` | `/api/specifications/{id}` |
| `POST` | `/api/analysis/{analysis_id}/generate` |
| `POST` | `/api/tenders/{id}/generate` |
| `GET` | `/api/tenders/{id}/specifications` |

## 3. Validation and Error Handling

The API validates:

- supported tender file formats (`PDF`, `DOCX`, and `TXT`);
- non-empty uploaded files;
- path identifiers and enumerated generation types through FastAPI and Pydantic;
- request bodies against the existing service schemas;
- bounded graph traversal parameters;
- supported language and generation options through their existing schemas.

Request validation errors use a stable response shape:

```json
{
  "error": "validation_error",
  "detail": "Request validation failed.",
  "fields": []
}
```

Resource-not-found responses use HTTP `404`. Invalid input uses HTTP `400`,
capacity exhaustion uses HTTP `503`, and unexpected service failures are
reported as HTTP `500` by the relevant endpoint while preserving the existing
service error text needed for diagnostics.

## 4. Asynchronous Jobs

Location:

- `backend/app/services/jobs.py`
- `backend/app/services/job_schemas.py`
- `backend/app/api/jobs.py`

The job registry uses a bounded `ThreadPoolExecutor` and a thread-safe
in-memory registry. Each worker creates and closes its own SQLAlchemy session
through `SessionLocal`; request-scoped sessions are never passed to worker
threads.

Job lifecycle:

```
QUEUED -> RUNNING -> COMPLETED
                    \
                     -> FAILED
```

### 4.1 Submit Asynchronous Tender Processing

`POST /api/jobs/tenders/upload` accepts the same tender file formats and form
metadata as the synchronous upload route. It returns HTTP `202`:

```json
{
  "id": "job UUID",
  "job_type": "tender_upload",
  "status": "QUEUED",
  "status_url": "/api/jobs/{job_id}",
  "created_at": "timestamp"
}
```

### 4.2 Submit Asynchronous Specification Generation

`POST /api/jobs/specifications/generate` accepts the existing
`SpecificationGenerationRequest` body and returns HTTP `202` with
`job_type = "specification_generation"`.

### 4.3 Poll a Job

`GET /api/jobs/{job_id}` returns the current status. Completed jobs expose the
serialized service result. Failed jobs expose an explicit error message and do
not return a success-shaped result.

The registry has a maximum retained-job capacity. Completed and failed records
are evicted before rejecting new work when capacity is reached. This prevents
unbounded memory growth while keeping active jobs protected.

Jobs are process-local by design. Durable tender and specification records are
written by the existing database services, but job status itself is not
intended to survive an API process restart.

## 5. Health Endpoint

`GET /api/health` continues to return the existing `status`, `version`, and
`module` fields and now also reports:

- Module 13 operational status;
- Module 14 operational status;
- asynchronous job status and polling endpoint.

The health response is intentionally lightweight and does not execute a
business operation or mutate project data.

## 6. Verification

Module 14 changes are verified together with the existing application suite.
The existing Module 13 and cumulative regression suites remain the baseline for
protecting the prior modules. The asynchronous routes additionally validate:

- malformed and unsupported uploads are rejected before queue submission;
- jobs return `202` with a pollable identifier;
- unknown job identifiers return `404`;
- worker sessions are isolated from request sessions;
- completed and failed jobs expose explicit terminal state.

Latest verification results:

- Module 14 focused tests: **6 passed, 0 failed**.
- Full cumulative regression: **183 passed, 0 failed**.
- Ingestion validation: **all checks passed**.
- Canonical standards: **268**.
- Core provenance coverage: **100%**.
- Ingestion audit also confirmed 111 relationships, 275 standard versions,
  710 QCO records, and 1,573 certification records.

The test run reported 463 existing warnings, consisting of SQLAlchemy legacy
`Query.get()` warnings and the Pydantic class-based-config deprecation warning.
No new failure was attributable to those warnings.

## 7. Module Completion Report

**MODULE:** 14 - FastAPI Integration  
**STATUS:** Complete  

**IMPLEMENTED:**

- Existing application routers registered under the `/api` prefix.
- Stable request-validation error responses.
- Explicit HTTP handling for invalid input, missing resources, capacity
  exhaustion, and processing failures.
- Health reporting for Module 13, Module 14, and asynchronous jobs.
- Bounded, thread-safe asynchronous job execution and polling.
- Worker-local database sessions with cleanup.
- Focused API tests and cumulative regression coverage.

**TESTS:**

- Module 14 focused suite: 6 tests.
- Full cumulative suite: 183 tests.
- Ingestion/provenance validation: all checks passed.
- OpenAPI route enumeration: 31 paths.

**RESULT:** 6 focused tests passed, 183 cumulative tests passed, and all
ingestion/provenance checks passed.

**KNOWN LIMITATIONS:**

- Job records are process-local and stored in memory.
- Job status is lost when the API process restarts.
- Existing SQLAlchemy and Pydantic deprecation warnings remain.
- Retrieval, intent, multilingual, audit, and latency metrics are deferred to
  Module 16.
