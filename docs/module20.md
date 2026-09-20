# Module 20 - Frontend Integration & Demo Interface

## Technology

The demo uses a dependency-free static ES-module frontend in `frontend/`. This
keeps the repository's existing FastAPI/Python architecture intact and avoids
introducing a build tool for a small integration surface. Node's built-in test
runner covers the API service layer.

## Architecture and API integration

`frontend/api.js` centralizes the configurable API base URL, JSON and multipart
requests, safe error parsing, and async job polling. `frontend/app.js` provides
the Recommend, Standard details, Tender audit, and Voice query workflows. UI
rendering is response-driven: missing values are shown as `UNKNOWN`, evidence
and provenance are preserved, and internal `PRIMARY` and confidence semantics
retain their backend disclaimers.

The backend received one minimal compatibility addition: `POST /api/analyze`,
which delegates directly to the existing `RecommendationEngine` and
`RecommendationRequest`. No domain, retrieval, compliance, graph, tender, or
specification logic was duplicated or changed.

## Configuration and startup

The static frontend defaults to `http://localhost:8000`. For another local API
origin, set `window.ARISTEA_API_BASE_URL` before `app.js` loads, or replace the
default in a local serving wrapper. No secrets belong in frontend configuration.

```powershell
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
python -m http.server 5173 --directory frontend
```

Open `http://localhost:5173`. The backend must allow the frontend origin through
its existing `CORS_ALLOWED_ORIGINS` setting; for this local command use
`CORS_ALLOWED_ORIGINS=http://localhost:5173` in the backend environment.

## Supported demo procedure

1. Recommend: try a supplied direct or semantic query, then an ambiguous cable query.
2. Standard details: load `IS 694:2010` to view metadata, versions, relationships, and compliance.
3. Tender audit: upload a supported supplied or locally created TXT/PDF/DOCX document.
4. Generate: use the tender result's generation action to display grounded output and provenance.
5. Voice: upload a supported WAV/MP3/PCM file and inspect transcription, recommendation, and TTS.

Tender upload currently uses the synchronous tender endpoint. The centralized
client also implements the existing async job polling contract for workflows
that use `/api/jobs/{job_id}`.

## Testing and limitations

Frontend tests are in `frontend/tests/api.test.mjs` and cover configurable base
URL, recommendation success, safe API errors, tender/specification payloads,
and async job completion. Browser verification requires the documented API and
frontend servers plus supplied project data. Production deployment, external
speech providers, and live PostgreSQL are not claimed here.
