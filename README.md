# ARISTEA-PROCURE — Indian Standards & Public Procurement Intelligence Platform

AI-powered procurement decision support platform designed for SIH Problem Statement 26108.

## Verified Data Baseline

The local repository is grounded in the verified ARISTEA dataset:

```text
269 standards
115 relationships
276 versions
710 QCO records
1,573 certifications
75 product licences
28 ministry mappings
14 evaluation queries
100% provenance coverage
```

All standard records, relationships, and compliance rules preserve source file and line-level provenance.

## Architecture & Technology Stack

- **Backend**: FastAPI (Python 3.13), SQLAlchemy 2.0, Pydantic v2, SQLite (`sih_bis.db`) / PostgreSQL (optional)
- **Embedding Model**: Pretrained Sentence Transformers embedding model (`paraphrase-multilingual-MiniLM-L12-v2`)
- **Retrieval Engine**: Semantic Retrieval using Pretrained Sentence Transformers (`paraphrase-multilingual-MiniLM-L12-v2`) and Dense Vector Similarity Search
- **Frontend**: Next.js 14 (App Router), React 18, TypeScript, CSS Variables Design System
- **Flagship — ARISTEA Autopilot** (`POST /api/autopilot/run`, SSE): describe a procurement need by text or voice in 9 languages and get a complete tender package. Autopilot parses the need, discovers primary and knowledge-graph-allied standards per component, checks QCO/certification mandates and standard currency, assesses supplier licence depth, drafts a tender where every clause cites its dataset record, then red-teams its own draft with the tender auditor, auto-fixes gaps and re-audits. Export via `POST /api/autopilot/export` (.docx with evidence annexure).
- **Mounted Workspaces (10)**:
  1. **Requirement Recommendation**: Semantic requirement matching and primary/allied identification
  2. **Standards Explorer**: Hierarchical directory of 268 standards with scope and version history
  3. **Knowledge Graph**: Interactive SVG dependency network and shortest-path tracer
  4. **QCO & Compliance**: Regulatory mandatory orders, certification schemes (ISI/CRS), and divergences
  5. **Tender Auditor**: Section-by-section tender gap analysis and evidence-grounded review
  6. **Specification Drafter**: Verified parameter tables, testing clauses, and inspection plans
  7. **Multilingual Voice**: Speech-to-text pipeline in 8 Indic languages + English
  8. **Audit Trail & History**: Grounded local session activity recording
  9. **BIS Service Hub**: Directory of 75 product licence categories and 28 ministry procurement mappings
  10. **Clause Explainer**: Plain-language translation grounded in verified scopes and amendments

## Database Configuration

The canonical local development database is SQLite:

```env
DATABASE_URL=sqlite:///./sih_bis.db
```

For production deployments, PostgreSQL is supported via `.env`.

## Local Setup

### 1. Backend Setup (Python 3.13)

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Ensure `.env` contains:
```env
DATABASE_URL=sqlite:///./sih_bis.db
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### 2. Database Migration & Data Ingestion

```powershell
alembic upgrade head
python -m scripts.ingest --data-dir csvfiles
python scripts/validate_ingestion.py
```

### 3. Start Backend API

```powershell
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

- API Health: `http://localhost:8000/api/health`
- Database Readiness: `http://localhost:8000/api/ready`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`

### 4. Start Next.js Frontend

In a separate terminal:

```powershell
cd frontend
npm install  # or bun install
npm run dev  # or bun dev
```

Open `http://localhost:3000` in your browser.

## Testing & Validation

Run the full automated test suite:

```powershell
# Backend pytest suite
py -3.13 -m pytest -v

# Ingestion provenance and dataset validation
py -3.13 scripts/validate_ingestion.py

# Frontend unit tests and production build
cd frontend
node --test tests/api.test.mjs
npm run build
```

## Future Innovation Roadmap (CONCEPT / NOT IMPLEMENTED)

The following 7 concepts represent research roadmap directions and are strictly separate from implemented capabilities:
1. Tender-to-Standard Traceability Graph
2. Standard Change Impact Analyzer
3. Procurement Contradiction Detector
4. Evidence Coverage Intelligence
5. Human-in-the-Loop Procurement Review
6. Regulatory Change Simulation
7. Requirement Ambiguity Resolution Loop
