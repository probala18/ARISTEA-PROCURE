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
- **Backend Grounding**: FastAPI (`http://127.0.0.1:8000`), Python 3.10+, SQLite 3 database (`sih_bis.db`) containing ~13,678 BIS standards, 37 QCO notifications, and 45,951 relationships.

---

## 3. Key Architectural Enhancements

### 3.1 Fixed Left Navigation Sidebar
- **Problem**: In the initial design, the navigation sidebar scrolled vertically along with the page content, creating friction when navigating long analysis outputs or document audits.
- **Solution**: The sidebar is styled with `position: fixed; left: 0; top: 0; width: 270px; height: 100vh; overflow-y: auto;` alongside a `.dashboard-main` container with `margin-left: 270px; width: calc(100% - 270px);`. The navigation remains stationary across all scroll positions.

### 3.2 Full API Contract Reconciliation
The frontend client in `frontend/lib/api.ts` was audited and reconciled with backend FastAPI route schemas:
- **Speech AI (`/api/speech/transcribe`)**: Reconciled canonical fields (`transcript`, `language`, `confidence`, `repetition_needed`, `provider`) with backward-compatible aliases.
- **Compliance Intelligence (`/api/compliance/{std_id}`)**: Reconciled schema to match `qco_records`, `governing_scheme`, `requirement_level`, `divergences`, and statutory `disclaimer`.
- **Tender Auditor (`/api/tenders/analyze`)**: Reconciled audit schema to match `coverage_score`, `expected_vs_present`, `gaps`, and `trust_disclaimer`.
- **Dynamic Config**: `API_BASE` is driven by `process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000'`, and `next.config.ts` proxies `/api/:path*` dynamically.

---

## 4. Eight-Workspace Executive Layout

ARISTEA-PROCURE now provides eight dedicated workspaces accessible via the fixed sidebar and top tab navigation:

| Workspace | Key Capabilities |
| :--- | :--- |
| **1. Semantic Matcher** (`recommend`) | Intent extraction, requirement cards, grounded reasoning drawer, GeM-ready clause generation, and superseded standards alert (e.g. IS 325 replaced by IS 12615). |
| **2. Standards Directory** (`standards`) | Catalog search, pagination, filter by BIS Division (MED, ETD, CED), version lifecycle, and cross-reference explorer. |
| **3. Knowledge Graph** (`graph`) | Interactive radial visualizer rendering node relationships, BIS standard hierarchies, and clause connections. |
| **4. Compliance & QCO** (`compliance`) | Quality Control Orders statutory matrix, Ministry notifications, implementation dates, and Section 66 regulatory disclaimers. |
| **5. Document Auditor** (`tender`) | File upload (PDF/DOCX/TXT), procurement audit, coverage score meter, expected vs present gap table, and actionable recommendations. |
| **6. Spec Workspace** (`spec`) | Live procurement specification editor, GeM tender clause formatter, one-click copy, and `.md` file export. |
| **7. Voice Assistant** (`speech`) | Multi-lingual audio transcription (Hindi, English, regional), real-time query mapping, and speech confidence scores. |
| **8. Session History** (`history`) | Session query logs, recent tender audits, and timestamps cached in browser local storage. |

---

## 5. Verification and Quality Assurance

1. **Automated Unit Testing (`frontend/tests/api.test.mjs`)**:
   - Verified `API_BASE` resolution and fallback.
   - Verified Speech AI contract payload normalization.
   - Verified Compliance Intelligence schema contracts.
   - Verified Tender Audit gap and coverage metrics contracts.
   - Verified Async Job polling status model.
   - **Result**: 6 passing tests, 0 failures.

2. **Ingestion & Data Integrity**:
   - `python scripts/validate_ingestion.py` confirms all 13,678 standards and 45,951 graph relationships remain authoritative and uncorrupted in `sih_bis.db`.

3. **Backend Service Health**:
   - `/api/health` reports status `healthy` with active catalog counters.
