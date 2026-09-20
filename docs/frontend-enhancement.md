# ARISTEA-PROCURE — Frontend Enhancement & Reference-Inspired Architecture

## 1. Executive Summary

This document details the frontend enhancement of **ARISTEA-PROCURE**, transforming the initial Next.js interface into a high-performance, competition-ready procurement intelligence portal. 

All capabilities draw functional inspiration from modern procurement systems (such as the reference portal at `https://sure-vert.vercel.app/`), while strictly grounded in ARISTEA-PROCURE's proprietary FastAPI backend services, SQLite/PostgreSQL verified BIS knowledge base (`sih_bis.db`), and Indian public procurement statutory mandates (GFR 2017 Rule 144(i), BIS Act 2016 Section 16 & 66, and GeM guidelines).

---

## 2. Technical Stack & Environment

- **Framework**: Next.js 16.3.5 (App Router, Turbopack support)
- **UI Engine**: React 19.2.8
- **Animation Orchestration**: 
  - Framer Motion 13.4.0 (declarative page and drawer transitions)
  - GSAP 3.15.0 (high-precision micro-interactions and dropzone springs)
- **Styling**: Vanilla CSS tokens in `frontend/app/globals.css`
- **Design System**: Royal Indigo (`#1e1b4b`, `#4338ca`) & Warm Amber (`#d97706`) palette with high-contrast neutral backgrounds, frosted glass accents, and fixed executive layout.
- **Backend Grounding**: FastAPI (`http://127.0.0.1:8000`), Python 3.13+, SQLite 3 database (`sih_bis.db`) containing 268 verified BIS standards, 111 relationships, 275 versions, 710 QCO notifications, 1,573 certifications, 75 product licences, and 28 ministry mappings.

---

## 3. Key Architectural Enhancements

### 3.1 Fixed Left Navigation Sidebar
- **Problem**: In the initial design, the navigation sidebar scrolled vertically along with the page content, creating friction when navigating long analysis outputs or document audits.
- **Solution**: The sidebar is styled with `position: fixed; left: 0; top: 0; width: 270px; height: 100vh; overflow-y: auto;` alongside a `.dashboard-main` container with `margin-left: 270px; width: calc(100% - 270px);`. The navigation remains stationary across all scroll positions.

### 3.2 Full API Contract Reconciliation
The frontend client in `frontend/lib/api.ts` was audited and reconciled with backend FastAPI route schemas:
- **Speech AI (`/api/speech/transcribe`)**: Reconciled canonical fields (`transcript`, `language`, `confidence`, `repetition_needed`, `provider`).
- **Compliance Intelligence (`/api/compliance/{std_id}`)**: Reconciled schema to match `qco_records`, `governing_scheme`, `requirement_level`, `divergences`, and statutory `disclaimer`.
- **Tender Auditor (`/api/tenders/analyze`)**: Reconciled audit schema to match `coverage_score`, `expected_vs_present`, `gaps`, and `trust_disclaimer`.
- **Minimal Read-Only Endpoints**: Added `GET /api/standards`, `GET /api/licences`, and `GET /api/ministry-mappings` strictly exposing existing ingested SQLite records with zero new domain intelligence.

---

## 4. Ten-Workspace Comprehensive Layout

ARISTEA-PROCURE now provides ten dedicated workspaces accessible via the fixed sidebar and top tab navigation:

| Workspace | Key Capabilities |
| :--- | :--- |
| **1. Semantic Matcher** (`recommend`) | Intent extraction, requirement cards, grounded reasoning drawer, GeM-ready clause generation, and superseded standards alert (e.g. IS 325 replaced by IS 12615). |
| **2. Standards Directory** (`standard`) | Official BIS catalog listing (268 standards), pagination, filters by category/division, status tags, and metadata details. |
| **3. BIS Service Hub** (`services`) | Directory of 75 verified product licences, 28 ministry procurement alignments, ISI Scheme-I / CRS Scheme-II guidance, and disclaimers for unverified external registries. |
| **4. Clause Explainer** (`simplify`) | Side-by-side technical scope vs plain-language procurement guidance with strict evidence boundary notice (*"Detailed clause text not available in current verified dataset"*). |
| **5. Knowledge Graph** (`graph`) | Interactive radial visualizer rendering node relationships, allied testing standards, and clause connections across 111 verified edges. |
| **6. Compliance & QCO** (`compliance`) | Quality Control Orders statutory matrix across 710 orders, Ministry notifications, implementation dates, and Section 66 regulatory disclaimers. |
| **7. Document Auditor** (`tender`) | File upload (PDF/DOCX/TXT), procurement audit, coverage score meter, expected vs present gap table, and actionable recommendations. |
| **8. Spec Workspace** (`spec`) | Live procurement specification editor, GeM tender clause formatter, one-click copy, and `.md` file export. |
| **9. Voice Assistant** (`voice`) | Multi-lingual audio transcription (Hindi, English, regional), real-time query mapping, and speech confidence scores. |
| **10. Session History** (`history`) | Pure session history (zero fake/seeded demo entries), starts cleanly with *"No recent activity in this session."* |

---

## 5. Verification and Quality Assurance

1. **Automated Unit Testing (`frontend/tests/api.test.mjs`)**:
   - Verified `API_BASE` resolution and fallback.
   - Verified Speech AI contract payload normalization.
   - Verified Compliance Intelligence schema contracts.
   - Verified Tender Audit gap and coverage metrics contracts.
   - Verified Async Job polling status model.
   - **Result**: 10 passing tests, 0 failures.

2. **Ingestion & Data Integrity**:
   - `python scripts/validate_ingestion.py` confirms all 268 standards, 111 graph relationships, 275 versions, 710 QCO records, 1,573 certifications, 75 product licences, and 28 ministry mappings remain authoritative and uncorrupted in `sih_bis.db` (100% provenance coverage).

3. **Backend Service Health**:
   - `/api/health` reports status `ok` with operational modules.
