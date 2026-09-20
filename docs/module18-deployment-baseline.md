# Module 18 Deployment Baseline

## Audit scope

This baseline reviews the repository before Module 18 changes. The objective is
deployment reproducibility and local production-like operation only. Existing
BIS/procurement intelligence, evaluation methodology, and Module 17 security
behavior are treated as fixed.

## Already implemented

- FastAPI application entry point: `backend.app.main:app`.
- Health endpoint: `GET /api/health`.
- Database readiness endpoint: `GET /api/ready`, using a read-only `SELECT 1`.
- FastAPI lifespan cleanup for the bounded in-process job executor.
- SQLAlchemy database configuration with PostgreSQL support and SQLite test
  fallback.
- Alembic configuration and one initial migration.
- Environment-backed settings for database, CORS, upload limits, audio limits,
  evaluation limits, and logging.
- Module 17 upload/path validation, safe error responses, security headers,
  and configurable CORS.
- Supplied dataset ingestion and provenance validation scripts.
- OpenAPI generation through FastAPI.

## Missing or partial

- No repository dependency manifest was found (`requirements.txt`,
  `pyproject.toml`, Pipfile, or Poetry lockfile).
- No Dockerfile, compose file, or container health check exists.
- `alembic.ini` contains a masked/static URL rather than a documented
  environment-driven deployment URL.
- The root README is only a placeholder and does not describe installation,
  migration, ingestion, validation, or startup.
- Persistent, temporary, and process-local storage behavior is not documented
  in one deployment guide.
- No focused deployment smoke test exists.

## Safe Module 18 improvements

1. Add a minimal pinned `requirements.txt` based on the currently used runtime
   dependencies.
2. Add `.env.example` containing placeholders only.
3. Make Alembic use `DATABASE_URL` from the environment while retaining the
   existing migration metadata.
4. Add a minimal production-oriented Dockerfile and `.dockerignore`.
5. Add a deployment smoke test for app import, health, readiness, OpenAPI,
   and the configured startup surface.
6. Replace the placeholder README with concise reproducible local and
   container instructions.
7. Create `docs/module18.md` with verified runtime, storage, logging, and
   limitation details.

## Explicitly out of scope

Authentication, authorization, Kubernetes, cloud-specific infrastructure,
distributed queues, Redis, Kafka, Celery, autoscaling, WAF, external
monitoring/SIEM, frontend redesign, new AI models, domain data changes, and
benchmark changes.

## Deployment order

Configure environment, create the database, run `alembic upgrade head`, run
the supplied ingestion process, run `scripts/validate_ingestion.py`, then
start the application with the production ASGI command. Application startup
must not ingest or mutate domain data automatically.
