<p align="center">
  <h1 align="center">🏛️ ARISTEA-PROCURE</h1>
  <p align="center">
    <strong>Indian Standards & Public Procurement Intelligence Platform</strong>
  </p>
  <p align="center">
    AI-powered procurement decision support system built for<br/>
    <strong>SIH 2026 — Problem Statement 26108</strong>
  </p>
  <p align="center">
    <img src="https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white" alt="Python 3.13" />
    <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
    <img src="https://img.shields.io/badge/Next.js-16.3-000000?logo=nextdotjs&logoColor=white" alt="Next.js" />
    <img src="https://img.shields.io/badge/React-19.2-61DAFB?logo=react&logoColor=black" alt="React" />
    <img src="https://img.shields.io/badge/TypeScript-5.x-3178C6?logo=typescript&logoColor=white" alt="TypeScript" />
    <img src="https://img.shields.io/badge/SQLite-%E2%9C%93-003B57?logo=sqlite&logoColor=white" alt="SQLite" />
    <img src="https://img.shields.io/badge/PostgreSQL-Optional-4169E1?logo=postgresql&logoColor=white" alt="PostgreSQL" />
    <img src="https://img.shields.io/badge/License-MIT-green" alt="MIT License" />
  </p>
</p>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Problem Statement](#-problem-statement)
- [Verified Data Baseline](#-verified-data-baseline)
- [Architecture & Technology Stack](#-architecture--technology-stack)
- [Project Structure](#-project-structure)
- [Platform Modules (10 Workspaces)](#-platform-modules-10-mounted-workspaces)
- [ARISTEA Autopilot — Flagship Feature](#-aristea-autopilot--flagship-feature)
- [Backend API Reference](#-backend-api-reference)
- [Database Schema](#-database-schema)
- [Data Ingestion Pipeline](#-data-ingestion-pipeline)
- [Local Setup Guide](#-local-setup-guide)
- [Docker Deployment](#-docker-deployment)
- [Cloud Deployment (Render)](#-cloud-deployment-render)
- [Testing & Validation](#-testing--validation)
- [Environment Variables](#-environment-variables)
- [Frontend Architecture](#-frontend-architecture)
- [AI & ML Components](#-ai--ml-components)
- [Security](#-security)
- [Future Innovation Roadmap](#-future-innovation-roadmap)
- [Contributing](#-contributing)
- [Team](#-team)

---

## 🎯 Overview

**ARISTEA-PROCURE** is an end-to-end, AI-powered platform that assists government procurement officers, engineers, and auditors in making standards-compliant purchasing decisions. It leverages **Bureau of Indian Standards (BIS)** data — including IS/ISO standards, Quality Control Orders (QCOs), certification schemes (ISI/CRS), and ministry procurement guidelines — to provide intelligent, evidence-grounded recommendations throughout the entire procurement lifecycle.

The platform combines **semantic search**, **knowledge graph analysis**, **compliance intelligence**, **multilingual voice support**, and an **autonomous Autopilot agent** to transform raw procurement needs into fully audited, export-ready tender documents.

---

## 📌 Problem Statement

> **SIH 2026 — PS 26108**: Design and develop an AI-based recommendation engine that assists public procurement officers in identifying relevant Indian Standards (BIS standards) for procurement specifications, ensuring compliance with Quality Control Orders and government procurement rules (GFR 2017).

---

## 📊 Verified Data Baseline

The platform is grounded in a rigorously verified ARISTEA dataset with **100% provenance coverage** — every record traces back to its source file and line number:

| Data Category         | Count  |
|-----------------------|--------|
| Indian Standards      | 269    |
| Relationships         | 115    |
| Standard Versions     | 276    |
| QCO Records           | 710    |
| Certifications        | 1,573  |
| Product Licences      | 75     |
| Ministry Mappings     | 28     |
| Evaluation Queries    | 14     |
| **Provenance Coverage** | **100%** |

All standard records, relationships, and compliance rules preserve source file and line-level provenance.

---

## 🏗️ Architecture & Technology Stack

```
┌──────────────────────────────────────────────────────────────────────┐
│                        ARISTEA-PROCURE                               │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────┐    ┌──────────────────────────────┐ │
│  │       FRONTEND              │    │         BACKEND              │ │
│  │                             │    │                              │ │
│  │  Next.js 16 (App Router)    │◄──►│  FastAPI (Python 3.13)       │ │
│  │  React 19 + TypeScript 5   │    │  SQLAlchemy 2.0 + Pydantic   │ │
│  │  Framer Motion + GSAP      │    │  ONNX Runtime Embeddings     │ │
│  │  Lucide Icons              │    │  Sentence Transformers       │ │
│  │  CSS Variables Design Sys. │    │                              │ │
│  │                             │    │  ┌──────────────────────┐   │ │
│  │  14 View Components         │    │  │  SQLite / PostgreSQL │   │ │
│  │  Sidebar + Tab Navigation  │    │  │  (sih_bis.db)        │   │ │
│  │  Toast Notifications       │    │  └──────────────────────┘   │ │
│  └─────────────────────────────┘    └──────────────────────────────┘ │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                    SERVICE LAYER (15 Modules)                   │ │
│  │                                                                  │ │
│  │  Recommendation · Retrieval · Knowledge Graph · Compliance      │ │
│  │  Version Intelligence · Relationship Engine · Speech AI         │ │
│  │  Tender Engine · Tender Audit · Specification Generator         │ │
│  │  Adversarial Auditor · Autopilot · Redline · Vision Table      │ │
│  │  Evaluation · Ingestion · Jobs                                  │ │
│  └──────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

### Technology Summary

| Layer             | Technology                                                        |
|-------------------|-------------------------------------------------------------------|
| **Backend**       | FastAPI, Python 3.13, SQLAlchemy 2.0, Pydantic v2, Alembic       |
| **Frontend**      | Next.js 16 (App Router), React 19, TypeScript 5, CSS Variables   |
| **Animation**     | Framer Motion 13, GSAP 3.15                                      |
| **Icons**         | Lucide React 1.47                                                 |
| **Database**      | SQLite (`sih_bis.db`) — local; PostgreSQL (pgvector) — production |
| **Embeddings**    | ONNX Runtime + Sentence Transformers (`all-MiniLM-L6-v2`)        |
| **Retrieval**     | Dense vector similarity search (paraphrase-multilingual-MiniLM)   |
| **Speech**        | Whisper STT pipeline (8 Indic languages + English)                |
| **Containerization** | Docker (multi-stage, with HEALTHCHECK)                         |
| **Deployment**    | Render (Docker), Vercel (frontend)                                |
| **Testing**       | Pytest (20 test modules), Node --test (frontend)                  |

---

## 📁 Project Structure

```
ARISTEA-PROCURE/
├── backend/                      # Python FastAPI backend
│   └── app/
│       ├── api/                  # API route handlers
│       │   ├── standards.py      # Standards & knowledge graph endpoints
│       │   ├── speech.py         # Multilingual voice processing
│       │   ├── tenders.py        # Tender upload, audit, generation
│       │   ├── specifications.py # Specification drafting
│       │   ├── autopilot.py      # Autonomous procurement agent
│       │   ├── advanced.py       # Advanced analytics endpoints
│       │   ├── evaluations.py    # Retrieval evaluation framework
│       │   └── jobs.py           # Async background job management
│       ├── core/                 # Application configuration
│       │   ├── config.py         # Settings (Pydantic BaseSettings)
│       │   ├── database.py       # SQLAlchemy engine & session
│       │   ├── normalizers.py    # Standard ID normalization utilities
│       │   └── security.py       # Security headers & CORS config
│       ├── models/               # SQLAlchemy ORM models
│       │   ├── standard.py       # Standard, embedding fields
│       │   ├── compliance.py     # QCO, certification, licence models
│       │   ├── relationship.py   # Standard dependency graph edges
│       │   ├── version.py        # Standard version history
│       │   ├── department.py     # Ministry/department mappings
│       │   ├── tender.py         # Tender document models
│       │   ├── analysis.py       # Analysis result models
│       │   ├── ontology.py       # Domain ontology/taxonomy
│       │   ├── evaluation.py     # Retrieval evaluation queries
│       │   ├── provenance.py     # Data provenance tracking
│       │   └── specification.py  # Specification generation models
│       ├── services/             # Business logic & AI services
│       │   ├── recommendation/   # Semantic requirement matching
│       │   ├── retrieval/        # Dense vector similarity search
│       │   ├── knowledge_graph/  # Graph traversal & visualization
│       │   ├── compliance_intelligence/  # QCO/GFR 2017 rule engine
│       │   ├── version_intelligence/     # Standard currency analysis
│       │   ├── relationship_engine/      # Standard dependency resolver
│       │   ├── speech/           # Whisper-based multilingual STT
│       │   ├── tender_engine/    # Tender document generation
│       │   ├── tender_audit/     # Section-by-section gap analysis
│       │   ├── specification_generator/  # Spec clause drafting
│       │   ├── adversarial_auditor/      # Red-team tender review
│       │   ├── autopilot/        # End-to-end autonomous agent
│       │   ├── redline/          # Standard comparison & redlining
│       │   ├── vision_table/     # Table extraction from documents
│       │   ├── evaluation/       # Retrieval quality benchmarks
│       │   ├── ingestion/        # CSV/JSON data import pipeline
│       │   └── jobs.py           # Background job registry
│       ├── resources/            # Static resources & templates
│       └── main.py               # FastAPI application entry point
│
├── frontend/                     # Next.js 16 frontend application
│   ├── app/
│   │   ├── layout.tsx            # Root layout with metadata
│   │   ├── page.tsx              # Main SPA page (14 views)
│   │   └── globals.css           # CSS Variables design system
│   ├── components/
│   │   ├── Header.tsx            # Global search bar + navigation
│   │   ├── Sidebar.tsx           # Collapsible workspace sidebar
│   │   ├── TabNav.tsx            # Tab-based workspace navigation
│   │   ├── ui/                   # Reusable UI primitives (Toast, etc.)
│   │   └── views/                # 14 workspace view components
│   │       ├── DashboardView.tsx          # Landing dashboard
│   │       ├── AutopilotView.tsx          # Autopilot agent interface
│   │       ├── RecommendView.tsx          # Semantic requirement matcher
│   │       ├── StandardView.tsx           # Standards directory explorer
│   │       ├── GraphView.tsx              # Knowledge graph visualization
│   │       ├── ComplianceView.tsx         # QCO & compliance checker
│   │       ├── TenderView.tsx             # Tender auditor & drafter
│   │       ├── SpecView.tsx               # Specification generator
│   │       ├── VoiceView.tsx              # Multilingual voice input
│   │       ├── HistoryView.tsx            # Session audit trail
│   │       ├── ServiceHubView.tsx         # BIS services directory
│   │       ├── SimplifyView.tsx           # Clause explainer/simplifier
│   │       ├── RedlineView.tsx            # Standard comparison & redline
│   │       ├── AnalyticsDiagramView.tsx   # Analytics & diagrams
│   │       └── redline/                   # Redline sub-components
│   │           ├── StandardIntelligenceSuite.tsx
│   │           ├── TenderOverviewSection.tsx
│   │           ├── ComparisonMatrixSection.tsx
│   │           ├── BidderRequirementsSection.tsx
│   │           ├── CostEstimationSection.tsx
│   │           ├── EcoTrackSection.tsx
│   │           ├── PrimarySourceTrackerSection.tsx
│   │           └── StandardsMigrationCard.tsx
│   ├── lib/                      # Shared utilities & API client
│   └── tests/                    # Frontend tests
│
├── alembic/                      # Database migration framework
│   ├── env.py                    # Alembic environment config
│   └── versions/
│       └── 001_initial_schema.py # Complete schema (17+ tables)
│
├── csvfiles/                     # Source datasets with provenance
│   ├── standards.csv             # 269 Indian Standards records
│   ├── bis_standards.csv         # BIS standards metadata
│   ├── bis_standards.json        # Structured standards data
│   ├── certification.csv         # 1,573 certification records
│   ├── productlicence.csv        # 75 product licence categories
│   ├── relationships.json        # 115 standard relationships
│   ├── query_dataset.json        # 14 evaluation queries
│   ├── schem.csv                 # Certification schemes
│   ├── ReportExcel.csv           # QCO regulatory reports
│   ├── upcomming.csv             # Upcoming standards
│   ├── sample_standards.json     # Detailed standard samples
│   └── manifest.json             # Dataset manifest with provenance
│
├── scripts/                      # Utility & maintenance scripts
│   ├── ingest.py                 # Data ingestion pipeline
│   ├── validate_ingestion.py     # Post-ingestion verification
│   ├── generate_embeddings.py    # Embedding vector generation
│   ├── evaluate_recommendation.py# Recommendation quality eval
│   ├── evaluate_retrieval.py     # Retrieval accuracy benchmarks
│   ├── test_async_job.py         # Async job system tests
│   ├── test_scenarios_e2e.py     # End-to-end scenario tests
│   ├── test_speech_roundtrip.py  # Speech pipeline tests
│   └── test_tender_flow.py       # Tender workflow tests
│
├── tests/                        # Comprehensive test suite (20 modules)
│   ├── test_module1_data_inventory.py
│   ├── test_module2_database_schema.py
│   ├── test_module3_verification.py
│   ├── test_module4_knowledge_graph.py
│   ├── test_module5_retrieval.py
│   ├── test_module6_recommendation.py
│   ├── test_module7_relationship_engine.py
│   ├── test_module8_version_intelligence.py
│   ├── test_module9_compliance_intelligence.py
│   ├── test_module10_speech_ai.py
│   ├── test_module11_tender_engine.py
│   ├── test_module12_tender_audit.py
│   ├── test_module13_specification_generator.py
│   ├── test_module14_fastapi_integration.py
│   ├── test_module15_integration_reliability.py
│   ├── test_module16_evaluation.py
│   ├── test_module17_security.py
│   ├── test_module18_deployment.py
│   ├── test_module19_end_to_end.py
│   └── test_normalizers.py
│
├── docs/                         # Architecture & module documentation
│   ├── data-inventory.md
│   ├── reference-feature-matrix.md
│   ├── postgresql_schema.sql
│   ├── ingestion-report.md
│   ├── innovation-charter.md
│   ├── module3-verification-report.md
│   ├── module4-knowledge-graph.md
│   ├── module5-retrieval.md
│   ├── module6-recommendation.md
│   ├── module8-version-intelligence.md
│   ├── module9-compliance-intelligence.md
│   ├── module10-speech-ai.md
│   ├── module11-tender-engine.md
│   ├── module12-tender-audit.md
│   ├── module13.md — module21-demo-readiness.md
│   └── ... (30 documentation files)
│
├── Dockerfile                    # Production container build
├── render.yaml                   # Render cloud deployment config
├── vercel.json                   # Vercel frontend deployment
├── alembic.ini                   # Alembic migration config
├── requirements.txt              # Python dependencies
├── package.json                  # Root package config
├── sih_bis.db                    # Pre-built SQLite database (~19 MB)
├── .env.example                  # Environment variable template
└── .gitignore
```

---

## 🧩 Platform Modules (10 Mounted Workspaces)

### 1. 🔍 Requirement Recommendation Engine
> **API**: `POST /api/analyze` · `POST /api/recommend`

Accepts a natural-language procurement requirement (e.g., *"We need to purchase 500 steel reinforcement bars for highway bridge construction"*) and returns semantically matched Indian Standards ranked by cosine similarity. Identifies **primary standards** and **allied/supporting standards** from the knowledge graph.

**How it works:**
- Encodes the query using Sentence Transformers (`all-MiniLM-L6-v2`)
- Computes dense vector similarity against 269 pre-embedded standards
- Retrieves knowledge-graph-connected allied standards
- Returns ranked results with similarity scores, scopes, and provenance

---

### 2. 📚 Standards Explorer
> **API**: `GET /api/standards` · `GET /api/standards/{id}`

A hierarchical, searchable directory of **269 Indian Standards** with:
- Full metadata (IS number, title, scope, category, division, department)
- Version history and amendment tracking (276 versions)
- Pagination, full-text search, and category/division filtering
- Direct linking to related standards via knowledge graph edges

---

### 3. 🕸️ Knowledge Graph
> **API**: `GET /api/graph/{id}` · `GET /api/graph/paths`

An interactive, force-directed graph visualization of the **115 verified relationships** between Indian Standards. Features:
- Radial node expansion for exploring dependency networks
- Shortest-path tracing between any two standards
- Relationship types: supersedes, references, complements, depends_on
- SVG-based rendering with pan/zoom and node tooltips

---

### 4. ✅ QCO & Compliance Intelligence
> **API**: `GET /api/compliance/{id}` · `GET /api/standards/{id}/compliance`

Deterministic compliance checking against:
- **710 Quality Control Orders (QCOs)** — mandatory DPIIT/MeitY regulatory mandates
- **1,573 certification records** — ISI (Scheme-I) and CRS (Scheme-II) status
- **GFR 2017** rule engine — procurement regulation compliance
- Divergence detection between standard versions and active QCO orders

---

### 5. 📝 Tender Auditor
> **API**: `POST /api/tender/upload` · `POST /api/tender/audit`

Section-by-section gap analysis of uploaded tender/RFP documents:
- Multi-format parsing: **PDF**, **DOCX**, **TXT**
- Outdated standard citation detection
- Missing QCO mandate checks
- Compliance gap identification with evidence-grounded suggestions
- Generates structured audit reports with corrective recommendations

---

### 6. 📐 Specification Drafter
> **API**: `POST /api/specification/generate`

Generates procurement specification clauses grounded in verified data:
- Parameter tables with testing requirements
- Inspection plans and acceptance criteria
- Clause text citing specific IS standard sections
- Export-ready format for incorporation into tender documents

---

### 7. 🎙️ Multilingual Voice Interface
> **API**: `POST /api/voice/process-query` · `POST /api/voice/transcribe`

Speech-to-text procurement assistant supporting **9 languages**:
- **English**, **Hindi**, **Tamil**, **Telugu**, **Kannada**, **Malayalam**, **Bengali**, **Marathi**, **Gujarati**
- Whisper-based transcription pipeline
- Automatic routing of transcribed text to the semantic recommendation engine
- Voice-first design for accessibility in field procurement scenarios

---

### 8. 📜 Audit Trail & Session History
> **Frontend**: `HistoryView.tsx`

Local session activity recording with:
- Timestamped log of all user interactions
- Query history with results
- Zero synthetic/fabricated data — fresh sessions start empty
- Exportable audit trail for procurement accountability

---

### 9. 🏢 BIS Service Hub
> **API**: `GET /api/licences` · `GET /api/ministry-mappings`

Directory of BIS services and government procurement mappings:
- **75 product licence categories** (ISI Scheme-I)
- **28 ministry procurement mappings** (MoP, MoHUA, MoRTH, MeitY, etc.)
- CRS (Scheme-II) guidance for electronics/IT goods
- Direct links to relevant standards for each service category

---

### 10. 💡 Clause Explainer & Simplifier
> **API**: `GET /api/standards/{id}` (scope field)

Plain-language translation of technical standard scopes:
- Side-by-side **Technical** vs **Simplified** view
- Procurement-context explanations for non-technical officers
- Grounded in verified standard scopes and amendments
- Explicit boundary marking when detailed clause text is unavailable

---

## 🚀 ARISTEA Autopilot — Flagship Feature

> **API**: `POST /api/autopilot/run` (SSE) · `POST /api/autopilot/export`

The **Autopilot** is an autonomous, multi-stage procurement agent that transforms a natural-language procurement need into a complete, audited tender package:

```
User Input (text or voice, 9 languages)
    │
    ▼
┌─ Stage 1: Requirement Parsing ──────────────────────────┐
│  Parse procurement need into structured components       │
└──────────────────────────────────────────────────────────┘
    │
    ▼
┌─ Stage 2: Standard Discovery ───────────────────────────┐
│  Semantic search → primary standards per component       │
│  Knowledge graph → allied/dependent standards            │
└──────────────────────────────────────────────────────────┘
    │
    ▼
┌─ Stage 3: Compliance & Currency Check ──────────────────┐
│  QCO mandate verification (710 orders)                   │
│  Standard currency validation (supersession check)       │
│  Certification status (ISI/CRS) verification             │
└──────────────────────────────────────────────────────────┘
    │
    ▼
┌─ Stage 4: Supplier Intelligence ────────────────────────┐
│  Product licence depth assessment (75 categories)        │
│  Ministry procurement guideline alignment                │
└──────────────────────────────────────────────────────────┘
    │
    ▼
┌─ Stage 5: Tender Draft Generation ──────────────────────┐
│  Every clause cites its dataset record                   │
│  Specification parameters, testing, inspection plans     │
└──────────────────────────────────────────────────────────┘
    │
    ▼
┌─ Stage 6: Red-Team Adversarial Audit ───────────────────┐
│  Autopilot audits its own draft                          │
│  Auto-fixes identified gaps                              │
│  Re-audits until passing                                 │
└──────────────────────────────────────────────────────────┘
    │
    ▼
Export → .docx with evidence annexure
```

**Key features:**
- **Server-Sent Events (SSE)** for real-time progress streaming
- **Self-healing**: auto-detects and fixes audit gaps in its own output
- **Evidence annexure**: every claim in the tender links to a verified record
- **Export**: `POST /api/autopilot/export` generates a professional `.docx` document

---

## 📡 Backend API Reference

### Health & Readiness

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Application health check |
| `/api/ready` | GET | Database readiness probe |
| `/docs` | GET | Interactive OpenAPI/Swagger docs |

### Standards & Knowledge Graph

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/standards` | GET | Paginated standards directory (search, filter by category/division) |
| `/api/standards/{id}` | GET | Single standard detail with full metadata |
| `/api/standards/{id}/compliance` | GET | Compliance status for a standard |
| `/api/graph/{id}` | GET | Knowledge graph neighbors for a standard |
| `/api/graph/paths` | GET | Shortest path between two standards |

### Recommendation & Analysis

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/analyze` | POST | Semantic requirement analysis & recommendation |
| `/api/recommend` | POST | Requirement-to-standard matching |

### Tender & Specification

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/tender/upload` | POST | Upload tender document (PDF/DOCX/TXT) |
| `/api/tender/audit` | POST | Section-by-section tender audit |
| `/api/tender/generate` | POST | Generate tender draft |
| `/api/specification/generate` | POST | Generate specification clauses |

### Speech & Voice

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/voice/transcribe` | POST | Transcribe audio to text |
| `/api/voice/process-query` | POST | Transcribe + route to recommendation |

### Autopilot

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/autopilot/run` | POST | Run full autopilot pipeline (SSE stream) |
| `/api/autopilot/export` | POST | Export autopilot results as .docx |

### BIS Services

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/licences` | GET | Product licence categories (75 records) |
| `/api/ministry-mappings` | GET | Ministry procurement mappings (28 records) |

### Async Jobs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/jobs/{job_id}` | GET | Check async job status & results |

### Evaluations

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/evaluations/run` | POST | Run retrieval quality evaluation |

---

## 🗄️ Database Schema

The database contains **17+ tables** managed via Alembic migrations:

| Table | Description | Record Count |
|-------|-------------|-------------|
| `standards` | Indian Standards with embeddings | 269 |
| `standard_versions` | Version history & amendments | 276 |
| `relationships` | Standard-to-standard dependency edges | 115 |
| `qco_entries` | Quality Control Orders (regulatory mandates) | 710 |
| `certifications` | ISI/CRS certification records | 1,573 |
| `product_licences` | BIS product licence categories | 75 |
| `departments` | Ministry/department mappings | 28 |
| `evaluation_queries` | Retrieval evaluation test queries | 14 |
| `source_documents` | Data provenance tracking | — |
| `tenders` | Uploaded tender documents | — |
| `tender_sections` | Parsed tender sections | — |
| `tender_audits` | Audit results & gap reports | — |
| `analyses` | Analysis session records | — |
| `ontology_nodes` | Domain taxonomy | — |
| `specifications` | Generated specification clauses | — |

### Database Configuration

**Local development (SQLite)**:
```env
DATABASE_URL=sqlite:///./sih_bis.db
```

**Production (PostgreSQL with pgvector)**:
```env
DATABASE_URL=postgresql://<user>:<password>@<host>:5432/<database>
```

---

## 🔄 Data Ingestion Pipeline

The ingestion system loads data from the `csvfiles/` directory with full provenance tracking:

```powershell
# 1. Run Alembic migrations to create tables
alembic upgrade head

# 2. Ingest all CSV/JSON datasets
python -m scripts.ingest --data-dir csvfiles

# 3. Validate ingestion integrity
python scripts/validate_ingestion.py
```

**Data sources ingested:**

| File | Content | Format |
|------|---------|--------|
| `standards.csv` | 269 Indian Standards records | CSV |
| `bis_standards.csv` / `.json` | BIS metadata & scope | CSV/JSON |
| `certification.csv` | 1,573 certification records | CSV |
| `productlicence.csv` | 75 product licence categories | CSV |
| `relationships.json` | 115 standard dependency edges | JSON |
| `query_dataset.json` | 14 evaluation test queries | JSON |
| `schem.csv` | Certification scheme details | CSV |
| `ReportExcel.csv` | QCO regulatory report data | CSV |
| `manifest.json` | Dataset manifest with provenance | JSON |

---

## 🚀 Local Setup Guide

### Prerequisites

- **Python 3.13+**
- **Node.js 18+** (or Bun)
- **Git**

### 1. Clone the Repository

```powershell
git clone https://github.com/your-org/aristea-procure.git
cd aristea-procure
```

### 2. Backend Setup

```powershell
# Create and activate virtual environment
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install Python dependencies
pip install -r requirements.txt

# Copy environment template
Copy-Item .env.example .env
```

Edit `.env` to set:
```env
DATABASE_URL=sqlite:///./sih_bis.db
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### 3. Database Migration & Data Ingestion

```powershell
# Run migrations
alembic upgrade head

# Ingest datasets
python -m scripts.ingest --data-dir csvfiles

# Validate data integrity
python scripts/validate_ingestion.py
```

> **Note**: The repository ships with a pre-built `sih_bis.db` (~19 MB), so you can skip this step if the database already exists.

### 4. Start the Backend API

```powershell
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

Verify it's running:
- **Health Check**: http://localhost:8000/api/health
- **Database Readiness**: http://localhost:8000/api/ready
- **OpenAPI Docs**: http://localhost:8000/docs

### 5. Start the Frontend

In a separate terminal:

```powershell
cd frontend
npm install     # or: bun install
npm run dev     # or: bun dev
```

Open http://localhost:3000 in your browser.

---

## 🐳 Docker Deployment

Build and run with Docker:

```bash
# Build the image
docker build -t aristea-procure .

# Run the container
docker run -p 8000:8000 \
  -e DATABASE_URL=sqlite:///./sih_bis.db \
  -e CORS_ALLOWED_ORIGINS="*" \
  aristea-procure
```

**Dockerfile features:**
- Based on `python:3.13-slim`
- Pre-caches ONNX embedding model at build time for fast startup
- Includes HEALTHCHECK with 30s interval
- Auto-runs data ingestion if database doesn't exist

---

## ☁️ Cloud Deployment (Render)

The project includes a `render.yaml` for one-click deployment on [Render](https://render.com):

```yaml
services:
  - type: web
    name: aristea-procure-backend
    runtime: docker
    plan: free
    region: oregon
    dockerfilePath: ./Dockerfile
    healthCheckPath: /api/health
```

**Frontend** can be deployed separately on [Vercel](https://vercel.com) using the included `vercel.json`.

---

## 🧪 Testing & Validation

The project includes a comprehensive **20-module test suite** covering every layer:

```powershell
# Run full backend test suite
py -3.13 -m pytest -v

# Run specific module tests
py -3.13 -m pytest tests/test_module4_knowledge_graph.py -v

# Validate data ingestion integrity
py -3.13 scripts/validate_ingestion.py

# Run frontend tests
cd frontend
node --test tests/api.test.mjs

# Production build verification
npm run build
```

### Test Module Coverage

| Module | Test File | Coverage Area |
|--------|-----------|---------------|
| 1 | `test_module1_data_inventory.py` | Dataset inventory & provenance |
| 2 | `test_module2_database_schema.py` | Schema integrity & constraints |
| 3 | `test_module3_verification.py` | Data verification & validation |
| 4 | `test_module4_knowledge_graph.py` | Graph traversal & path finding |
| 5 | `test_module5_retrieval.py` | Semantic retrieval accuracy |
| 6 | `test_module6_recommendation.py` | Recommendation engine quality |
| 7 | `test_module7_relationship_engine.py` | Relationship discovery & resolution |
| 8 | `test_module8_version_intelligence.py` | Standard version currency |
| 9 | `test_module9_compliance_intelligence.py` | QCO/GFR compliance rules |
| 10 | `test_module10_speech_ai.py` | Multilingual speech pipeline |
| 11 | `test_module11_tender_engine.py` | Tender document generation |
| 12 | `test_module12_tender_audit.py` | Tender gap analysis |
| 13 | `test_module13_specification_generator.py` | Specification clause drafting |
| 14 | `test_module14_fastapi_integration.py` | API endpoint integration |
| 15 | `test_module15_integration_reliability.py` | System reliability |
| 16 | `test_module16_evaluation.py` | Retrieval evaluation framework |
| 17 | `test_module17_security.py` | Security headers & CORS |
| 18 | `test_module18_deployment.py` | Docker & deployment |
| 19 | `test_module19_end_to_end.py` | Full workflow scenarios |
| — | `test_normalizers.py` | Standard ID normalization |

---

## ⚙️ Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./sih_bis.db` | Database connection string |
| `ENVIRONMENT` | `development` | Environment mode (`development` / `production`) |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `CORS_ALLOWED_ORIGINS` | `*` | Comma-separated allowed CORS origins |
| `MAX_UPLOAD_BYTES` | `10485760` (10 MB) | Maximum file upload size |
| `MAX_AUDIO_BYTES` | `10485760` (10 MB) | Maximum audio file size |
| `MAX_EVALUATION_QUERIES` | `100` | Max evaluation queries per run |
| `DATA_DIR` | `csvfiles` | Directory containing source datasets |
| `EMBEDDING_BACKEND` | `onnx` | Embedding inference backend |
| `EMBEDDING_MODEL_NAME` | `all-MiniLM-L6-v2` | Sentence Transformers model |
| `USE_PRETRAINED_EMBEDDINGS` | `true` | Use pretrained vs custom embeddings |
| `POSTGRES_USER` | `postgres` | PostgreSQL user (production) |
| `POSTGRES_PASSWORD` | — | PostgreSQL password (production) |
| `POSTGRES_HOST` | `localhost` | PostgreSQL host (production) |
| `POSTGRES_PORT` | `5432` | PostgreSQL port (production) |
| `POSTGRES_DB` | `sih_bis_db` | PostgreSQL database name (production) |

---

## 🎨 Frontend Architecture

The frontend is a **single-page application** built with Next.js 16 (App Router) that renders 14 workspace views through tab-based navigation:

### Design System
- **CSS Variables** — centralized theming via custom properties in `globals.css`
- **Dark mode** — premium dark-themed interface
- **Responsive** — adapts across desktop and tablet viewports

### Animation Stack
- **Framer Motion 13** — page transitions, presence animations, layout animations
- **GSAP 3.15** — hero text reveals, scroll-triggered animations, timeline sequences

### Component Architecture
- **Header** (`Header.tsx`) — global search bar with deterministic routing (IS pattern → Standards Explorer; service keyword → Service Hub; other → Semantic Matcher)
- **Sidebar** (`Sidebar.tsx`) — collapsible workspace navigation with 10+ module entries
- **TabNav** (`TabNav.tsx`) — horizontal tab system for workspace switching
- **14 View Components** — each module renders its own full-featured workspace
- **Toast System** — non-blocking notification system for API responses

### Health Monitoring
The frontend polls `/api/health` every 15 seconds and displays an online/offline indicator in the header.

---

## 🤖 AI & ML Components

### Embedding Model
- **Model**: `all-MiniLM-L6-v2` (Sentence Transformers)
- **Dimension**: 384-dimensional dense vectors
- **Inference**: ONNX Runtime for CPU-optimized inference
- **Multilingual variant**: `paraphrase-multilingual-MiniLM-L12-v2` for cross-language retrieval

### Semantic Retrieval
- Pre-computes embeddings for all 269 standards (scope + title)
- Query-time cosine similarity ranking
- PostgreSQL `pgvector` for production-scale ANN search

### Speech AI
- Whisper-based STT pipeline
- 8 Indic languages + English support
- Audio format conversion and chunking for large files

### Adversarial Auditor
- Red-team module that reviews generated tender drafts
- Checks for: missing QCO mandates, outdated citations, compliance gaps
- Auto-correction loop with re-audit verification

---

## 🔒 Security

- **Security Headers Middleware**: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`
- **CORS Configuration**: Configurable via environment variable
- **Input Validation**: Pydantic v2 request models with detailed validation error responses
- **File Upload Limits**: Configurable `MAX_UPLOAD_BYTES` and `MAX_AUDIO_BYTES`
- **No secrets in code**: All sensitive configuration via environment variables
- **Request validation error handler**: Returns structured error details without exposing internals

---

## 🔮 Future Innovation Roadmap

> **CONCEPT / NOT IMPLEMENTED** — The following 7 concepts represent research roadmap directions and are strictly separate from implemented capabilities:

| # | Innovation | Description |
|---|-----------|-------------|
| 1 | **Tender-to-Standard Traceability Graph** | Map every tender clause to its originating standard requirement |
| 2 | **Standard Change Impact Analyzer** | Predict downstream procurement impact when a standard is revised |
| 3 | **Procurement Contradiction Detector** | Identify conflicting requirements across referenced standards |
| 4 | **Evidence Coverage Intelligence** | Score how well a tender's evidence annexure covers all claims |
| 5 | **Human-in-the-Loop Procurement Review** | Guided expert review workflow with AI suggestions |
| 6 | **Regulatory Change Simulation** | Model "what-if" scenarios for proposed QCO/regulatory changes |
| 7 | **Requirement Ambiguity Resolution Loop** | Interactive disambiguation of vague procurement requirements |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add your feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

Please ensure all tests pass before submitting:
```powershell
py -3.13 -m pytest -v
cd frontend && npm run build
```

---

## 👥 Team

Built for **Smart India Hackathon (SIH) 2026** — Problem Statement 26108

---

<p align="center">
  <strong>ARISTEA-PROCURE</strong> — Empowering India's Public Procurement with AI-Grounded Standards Intelligence
</p>
