# Module 15 Scope Assessment

## Objective

Module 15 is defined as a project-specific integration and reliability layer.
Because the roadmap does not provide a detailed approved feature specification,
this assessment derives the smallest safe scope from the existing Modules 1-14
architecture. It does not add new BIS or procurement-domain behavior.

## Capabilities Inherited from Modules 1-14

- Supplied-data ingestion with source provenance and validation.
- Canonical standards, relationships, versions, compliance, licences, QCOs,
  tender evidence, audits, recommendations, speech, and specification
  generation services.
- Synchronous FastAPI routes for the existing services.
- Module 14 validation/error handling and a bounded in-process asynchronous job
  registry.
- Health reporting and OpenAPI exposure.
- Evidence-preserving `UNKNOWN` behavior and internal-only `PRIMARY` and
  `confidence_score` labels.

## Functionality Explicitly Deferred to Module 16

Module 16 owns evaluation and metrics, including retrieval metrics, intent
metrics, multilingual metrics, tender-audit metrics, and latency reporting.
Module 15 will not implement or claim those measurements.

## Identified Module 15 Gaps

The current Module 14 implementation has two integration/reliability gaps that
are directly observable in the repository:

1. The global `ThreadPoolExecutor` has no application-lifecycle shutdown
   operation, so worker resources are not explicitly released during API
   shutdown.
2. `/api/health` is a static liveness response and does not distinguish API
   liveness from database readiness. Existing services depend on the configured
   database, so a lightweight readiness check is justified without introducing
   domain logic.

No evidence supports adding new recommendation, compliance, tender, frontend,
or evaluation functionality in Module 15.

## Exact Implementation Scope

1. Add an explicit, idempotent `JobRegistry.shutdown()` operation.
2. Register application startup/shutdown lifecycle handling so the shared job
   executor is shut down cleanly.
3. Add a read-only `/api/ready` readiness endpoint that checks database
   connectivity and reports asynchronous-job availability.
4. Keep `/api/health` backward compatible and unchanged as a liveness endpoint.
5. Add focused tests for lifecycle shutdown, readiness success/failure, and
   route/OpenAPI behavior.

## Out of Scope

- Module 16 evaluation metrics or benchmark claims.
- Frontend redesign or new UI features.
- New BIS facts, standards, QCOs, certifications, or technical requirements.
- Changes to recommendation, relationship, version, compliance, tender audit,
  or specification-generation algorithms.
- Durable job queues, distributed workers, authentication, or deployment
  orchestration.
- Refactoring existing SQLAlchemy/Pydantic deprecation warnings.

## APIs and Files Expected to Change

- `backend/app/services/jobs.py`: explicit executor shutdown.
- `backend/app/main.py`: application lifespan and readiness route.
- `tests/test_module15_integration_reliability.py`: focused acceptance tests.
- `docs/module15.md`: implementation and verification record.

## Testing Strategy

- Verify readiness returns `200` when the configured database can answer a
  trivial read-only query.
- Verify readiness returns a non-ready response when database connectivity
  fails, without mutating data.
- Verify the readiness route is exposed in OpenAPI.
- Verify job-registry shutdown is idempotent and does not corrupt existing job
  state.
- Run the full cumulative regression and `scripts/validate_ingestion.py`.

## Acceptance Criteria

- API startup and shutdown explicitly manage the shared asynchronous executor.
- Readiness reports database availability separately from liveness.
- Existing Module 1-14 routes and behavior remain backward compatible.
- No project-domain output is generated or modified by the new layer.
- Focused tests, full regression, and ingestion/provenance validation pass.
