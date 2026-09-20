# ARISTEA-PROCURE

## Local setup

This repository contains the FastAPI application for SIH Problem Statement
26108. Python 3.13 is the tested runtime.

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Set real local database values in `.env`; `.env.example` contains placeholders
only.

## Database and supplied data

Run the steps in order:

```powershell
alembic upgrade head
python -m scripts.ingest --data-dir csvfiles
python scripts/validate_ingestion.py
```

The application does not automatically migrate or ingest data during startup.

## Start the API

```powershell
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

Useful endpoints:

- `GET /api/health` — liveness
- `GET /api/ready` — database readiness
- `/docs` — generated OpenAPI documentation

## Tests

```powershell
pytest -q
```

## Frontend demo

With the API running, serve the dependency-free demo in a second terminal:

```powershell
python -m http.server 5173 --directory frontend
```

Open `http://localhost:5173`. Set backend `CORS_ALLOWED_ORIGINS` to include
`http://localhost:5173` when it is not already allowed. See `docs/module20.md`
for the supported workflows and verification notes.

## Container

Build and run without embedding credentials:

```powershell
docker build -t aristea-procure .
docker run --rm --env-file .env -p 8000:8000 aristea-procure
```

Database migration and ingestion remain explicit operational steps outside
container startup.
