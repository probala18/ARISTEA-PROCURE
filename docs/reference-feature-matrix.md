# ARISTEA-PROCURE — Reference Feature Parity Matrix

## Benchmark Objective
This document benchmarks ARISTEA-PROCURE against the public reference interface (`https://bis-sathi.vercel.app/`), categorizing all functional capabilities while strictly adhering to ARISTEA's proprietary architecture, SQLite database (`sih_bis.db`), and verified domain baseline.

---

## 1. Feature Parity Matrix

| # | Reference Capability (`bis-sathi.vercel.app`) | ARISTEA Equivalent | Implementation Category | Data / API Support | Status & Notes |
|---|-----------------------------------------------|--------------------|-------------------------|--------------------|----------------|
| 1 | **Find Standard (Product $\to$ Standard Matcher)** | **Semantic Requirement Matcher** | **Already Supported** | `POST /api/recommend` | Dense semantic vector similarity search via Sentence Transformers over 268 verified standards. Fully grounded. |
| 2 | **Ask AI / Chat Assistant** | **Voice & Text Procurement Assistant** | **Already Supported** | `POST /api/voice/process-query`, `POST /api/recommend` | Grounded pipeline with Whisper STT and deterministic grounding. No hallucinated LLM responses. |
| 3 | **Simplify Standard (Technical vs Plain)** | **Clause Explainer & Simplifier (`SimplifyView`)** | **Implemented through Existing APIs & Data** | `GET /api/standards/{id}`, `GET /api/standards` | Side-by-side technical scope vs plain-language procurement translation. Explicit boundary: *"Detailed clause text not available in current verified dataset"*. |
| 4 | **Standards Directory & Search** | **Standards Directory (`GET /api/standards`)** | **Implemented through New Minimal Read-Only Endpoint** | `GET /api/standards` (paginated, query, category, division) | Direct read-only exposure of 268 `Standard` records from `sih_bis.db`. Preserves provenance. |
| 5 | **BIS Services — Product Certification (ISI)** | **BIS Service Hub — ISI Scheme-I & Licences** | **Implemented through New Minimal Read-Only Endpoint** | `GET /api/licences` (75 records) | Exposes 75 verified product licence records. No synthetic licence numbers. |
| 6 | **BIS Services — Ministry Guidelines** | **BIS Service Hub — Ministry Mappings** | **Implemented through New Minimal Read-Only Endpoint** | `GET /api/ministry-mappings` (28 records) | Exposes 28 verified departmental procurement alignments (MoP, MoHUA, MoRTH, etc.). |
| 7 | **BIS Services — Compulsory Registration (CRS)** | **BIS Service Hub — Scheme-II Guidance** | **Implemented through Existing Data** | Standard metadata & compliance records | Authoritative policy guidelines for electronics/IT goods under MeitY orders. |
| 8 | **Testing Laboratories Locator / GPS Map** | **Testing Standards in Knowledge Graph** | **Unsupported due to Missing Verified Data** | N/A (Lab GIS coordinates absent in dataset) | Tested standards and test methods (e.g. IS 10810) are mapped in graph; live GPS locator explicitly tagged *"Not available in current verified dataset"*. |
| 9 | **Hallmarking & HUID Serial Number Lookup** | **Precious Metals Standard Info (IS 1417)** | **Unsupported due to Missing Verified Data** | N/A (Live HUID database absent in dataset) | Standard metadata present; 6-digit real-time HUID serial registry explicitly tagged *"Not available in current verified dataset"*. |
| 10 | **Online Public Grievance / Redressal** | **Regulatory Reference Guidance** | **Reference-Specific / Excluded** | Central ManakOnline external portal | Out-of-scope for local procurement decision-support platform; clearly disclaimed. |
| 11 | **Unified Global Search & Command Entry** | **Deterministic Global Router (`Header.tsx`)** | **Implemented on Frontend** | Rule 7 routing regex | Deterministic dispatch: exact IS pattern $\to$ Standard Explorer; service keyword $\to$ Service Hub; other $\to$ Semantic Matcher. |
| 12 | **Session Activity & Audit History** | **Genuine Session History (`HistoryView`)** | **Implemented on Frontend** | Local session storage | Zero synthetic/fabricated data. Fresh sessions initialize strictly with *"No recent activity in this session."* |
| 13 | **Tender RFP Document Auditor** | **Document Auditor (`TenderView`)** | **Already Supported (Superior to Ref)** | `POST /api/tender/upload`, `POST /api/tender/audit` | Multi-format RFP parsing (PDF/DOCX/TXT), outdated citation detection, QCO gap checks. |
| 14 | **Knowledge Graph Visualization** | **Topology Graph (`GraphView`)** | **Already Supported (Superior to Ref)** | `GET /api/graph/{id}` | Interactive D3 radial node expansion across 111 verified relationship edges. |
| 15 | **Statutory QCO Compliance Matrix** | **Compliance & QCO View (`ComplianceView`)** | **Already Supported (Superior to Ref)** | `GET /api/compliance/{id}` | Deterministic GFR 2017 & DPIIT Quality Control Order reasoning over 710 statutory orders. |
| 16 | **Specification Drafting Studio** | **Spec Workspace (`SpecView`)** | **Already Supported (Superior to Ref)** | `POST /api/specification/generate` | Grounded procurement clause and inspection test plan drafting with audit provenance. |

---

## 2. Classification Summary

- **Already Supported:** 6 capabilities (Recommendation, Voice Assistant, Tender Auditor, Knowledge Graph, Compliance Matrix, Spec Studio)
- **Implemented through Existing APIs & Data:** 2 capabilities (Clause Explainer, CRS Guidance)
- **Implemented through New Minimal Read-Only Endpoints:** 3 endpoints (`GET /api/standards`, `GET /api/licences`, `GET /api/ministry-mappings`)
- **Unsupported due to Missing Verified Data:** 2 capabilities (Live GPS Lab Map, Real-Time HUID Serial Registry — strictly reported with safe fallback)
- **Reference-Specific / Excluded:** 1 capability (External Grievance Redressal Portal)

---

## 3. Seven Future Innovations (Documented Only)

As mandated by Rule 4 and Section 22:
1. **Tender-to-Standard Traceability Graph** — `CONCEPT / NOT IMPLEMENTED`
2. **Standard Change Impact Analyzer** — `CONCEPT / NOT IMPLEMENTED`
3. **Procurement Contradiction Detector** — `CONCEPT / NOT IMPLEMENTED`
4. **Evidence Coverage Intelligence** — `CONCEPT / NOT IMPLEMENTED`
5. **Human-in-the-Loop Procurement Review** — `CONCEPT / NOT IMPLEMENTED`
6. **Regulatory Change Simulation** — `CONCEPT / NOT IMPLEMENTED`
7. **Requirement Ambiguity Resolution Loop** — `CONCEPT / NOT IMPLEMENTED`
