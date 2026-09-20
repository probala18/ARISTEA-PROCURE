# Module 15 - Project-Defined Integration / Reliability Layer

## Objective

Module 15 adds the smallest reliability layer justified by the existing
Modules 1-14 architecture. It manages the lifecycle of Module 14's shared
asynchronous executor and separates API liveness from database readiness.

No BIS, Indian Standards, certification, QCO, tender, recommendation, or
specification-generation facts are introduced.

## Scope

### Included

- Idempotent shutdown for the bounded asynchronous `JobRegistry`.
- FastAPI application lifespan integration that releases the shared executor.
- Read-only `GET /api/ready` database readiness endpoint.
- Focused lifecycle, readiness, validation, and OpenAPI tests.

### Excluded

- Module 16 evaluation metrics.
- Frontend redesign.
- New domain logic or external data.
- Durable/distributed job infrastructure.
- Unrelated SQLAlchemy or Pydantic deprecation cleanup.

The detailed scope decision is recorded in
[module15-scope.md](./module15-scope.md).

## Architecture

```text
FastAPI application lifespan
             |
             v
       JobRegistry.shutdown()
             |
             v
 bounded ThreadPoolExecutor

GET /api/ready
       |
       v
  SessionLocal -> SELECT 1
       |
       +--> ready / HTTP 200
       |
       +--> unavailable / HTTP 503
```

The readiness check is read-only and does not invoke domain services or mutate
project data. Existing `/api/health` behavior remains the liveness contract.

## Implementation

### Job lifecycle

`JobRegistry.shutdown()` is idempotent. Once shutdown begins, new submissions
are rejected explicitly and the executor is closed. Existing job records are
not rewritten or converted into false success states.

### Application lifecycle

The FastAPI lifespan handler calls the shared registry shutdown operation when
the application exits. This prevents executor resources from being left
unmanaged.

### Readiness

`GET /api/ready` executes `SELECT 1` using the configured `SessionLocal`.
Successful connectivity returns HTTP `200`; database failures return HTTP
`503` with explicit `not_ready` and `unavailable` fields. The response also
reports asynchronous-job availability.

## API Changes

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/ready` | Database readiness and async-job availability |

The existing `/api/health` endpoint and all Modules 1-14 routes remain
available.

## Data and Provenance Behavior

Module 15 does not read or transform BIS/domain records beyond the database
connectivity probe. It does not create, update, delete, or reinterpret
standards, relationships, versions, QCOs, certifications, licences, tender
evidence, audit results, or generated specifications.

## Error Handling

- Readiness success: HTTP `200`.
- Database connectivity failure: HTTP `503`.
- Job submission after shutdown: explicit `RuntimeError`.
- Shutdown called more than once: safe no-op.

## Verification

Focused Module 15 tests:

- **5 passed, 0 failed**.

Full cumulative regression:

- **188 passed, 0 failed** across Modules 1-15.
- Existing warnings: **463**, limited to previously known SQLAlchemy
  `Query.get()` and Pydantic class-based-config deprecations.

Ingestion validation:

- **All checks passed**.
- Canonical standards: **268**.
- Relationships: **111**.
- Standard versions: **275**.
- QCO records: **710**.
- Certification records: **1,573**.
- Product licences: **75**.
- Core provenance coverage: **100%**.
- Unlinked relationship targets remained preserved verbatim.

API verification:

- `/api/ready` is registered and exposed in OpenAPI.
- Readiness success returns HTTP `200`.
- Database-unavailable readiness returns HTTP `503`.
- Existing asynchronous job, validation, and health routes remained covered by
  the cumulative suite.

## Completion Report

**MODULE:** 15 - Project-Defined Integration / Reliability Layer  
**STATUS:** Complete  
**SCOPE:** Lifecycle-managed asynchronous resources and database readiness.

**IMPLEMENTED:**

- `JobRegistry.shutdown()` with explicit rejection of new work after shutdown.
- FastAPI lifespan integration for executor cleanup.
- Read-only `/api/ready` readiness endpoint.
- Focused reliability and API tests.

**DATA INTEGRITY:** No domain records were created, updated, deleted, or
reinterpreted. Canonical standards, relationships, versions, QCO records,
certification records, product licences, and source provenance remained intact.

**MODULE 16 BOUNDARY:** Retrieval, intent, multilingual, tender-audit,
evaluation, and latency metrics remain deferred to Module 16. No such metrics
were implemented or claimed in Module 15.

## Limitations

- Job state remains process-local and in-memory.
- `/api/ready` checks database connectivity, not migration version, query
  performance, or downstream external services.
- Evaluation metrics remain deferred to Module 16.
