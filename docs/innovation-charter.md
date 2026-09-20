# ARISTEA-PROCURE — Innovation Charter & Capabilities Matrix

## Document Metadata
- **Platform:** ARISTEA-PROCURE (Problem Statement 26108)
- **Status:** Canonical Strategic Roadmap & Verification Boundary
- **Last Updated:** 2026-09-20
- **Policy Enforcement:** Strict separation between Implemented Capabilities and Conceptual Roadmap.

---

## 1. Implemented Capabilities (Authoritative Baseline)

The following differentiators and architectural capabilities are **fully implemented, grounded in local verified data, and verified via automated test suites**:

| # | Implemented Capability | Architectural Mechanism | Verification Artifacts |
|---|------------------------|-------------------------|------------------------|
| 1 | **Semantic Procurement Requirement Understanding** | Pretrained Sentence Transformers embedding model (`paraphrase-multilingual-MiniLM-L12-v2`) supporting multilingual vector similarity. | `backend/app/services/recommendation/` |
| 2 | **Dense Semantic Vector Retrieval** | 384-dimensional dense vector similarity search via Sentence Transformers with deterministic exact standard identifier fast-path. | `tests/test_module5_retrieval.py` |
| 3 | **Knowledge-Graph Relationship Expansion** | Deterministic traversal of 111 verified relationships (allied test methods, safety standards, normative references). | `backend/app/services/knowledge_graph/` |
| 4 | **Verified Supersession & Version Intelligence** | Temporal and lifecycle tracking across 275 standard versions (`CURRENT`, `SUPERSEDED`, `AMENDMENT_AVAILABLE`). | `backend/app/services/version_intelligence/` |
| 5 | **Deterministic Compliance & QCO Reasoning** | Rule-based GFR 2017 & DPIIT Quality Control Order (QCO) evaluation across 710 statutory orders. | `backend/app/services/compliance/` |
| 6 | **Strict Evidence & Source Provenance Tracking** | 100% provenance coverage linking every recommendation, clause, and finding back to source document hashes. | `scripts/validate_ingestion.py` |
| 7 | **Regulatory Ambiguity Detection** | Automated flagging of divergences between voluntary catalog markings and mandatory QCO notifications (97 identified divergences). | `backend/app/services/audit/` |
| 8 | **Tender RFP Document Gap Auditing** | Multi-format extraction (PDF, DOCX, TXT), standards extraction, outdated citation detection, and missing safety/testing gap identification. | `backend/app/services/audit/` |
| 9 | **Evidence-Grounded Specification Generation** | Structured procurement clause and inspection plan drafting with strict disclaimers preventing hallucinations. | `backend/app/services/specification_generator/` |
| 10 | **Multilingual Voice Assistant** | Faster-Whisper speech-to-text pipeline feeding directly into the identical backend recommendation engine. | `backend/app/services/speech/` |
| 11 | **Verified BIS Service & Regulatory Hub** | Read-only directory exposing 75 verified product licences and 28 ministry procurement mappings. | `backend/app/api/standards.py` |
| 12 | **Clause Explainer & Translation** | Side-by-side technical scope vs plain-language procurement guidance with strict evidence boundary notices. | `frontend/components/views/SimplifyView.tsx` |

---

## 2. Innovation Roadmap — CONCEPT / NOT IMPLEMENTED

> [!IMPORTANT]
> The following seven advanced innovations represent prospective research directions and future roadmap concepts.
> They are **NOT IMPLEMENTED** in the current production baseline. No synthetic mock data, fake prototype claims, or partial implementations are represented as completed functionality.

### Innovation 1: Tender-to-Standard Traceability Graph
- **Status:** `CONCEPT / NOT IMPLEMENTED`
- **Concept:** End-to-end directed acyclic graph (DAG) tracing a raw tender clause sentence through requirement extraction $\rightarrow$ recommended standard $\rightarrow$ normative referenced standards $\rightarrow$ active version $\rightarrow$ statutory QCO compliance status.
- **Prerequisites for Implementation:** Clause-level vector indexing of full tender documents; graph edge formulation connecting tender spans directly to standard clause nodes.

### Innovation 2: Standard Change Impact Analyzer
- **Status:** `CONCEPT / NOT IMPLEMENTED`
- **Concept:** Automated event-driven delta analyzer that ingests new BIS gazette amendments and computes the blast radius across active departmental tenders, supplier catalogues, and pre-approved specification templates.
- **Prerequisites for Implementation:** Real-time BIS Gazette RSS/webhook integration; persistent database of active procurement contracts.

### Innovation 3: Procurement Contradiction Detector
- **Status:** `CONCEPT / NOT IMPLEMENTED`
- **Concept:** Formal logic and NLP constraint solver detecting conflicting specifications within a single RFP (e.g., demanding high-efficiency motor IS 12615 IE3 while simultaneously specifying outdated test method IS 325 tolerances).
- **Prerequisites for Implementation:** Semantic constraint parser and formal ontological rule engine for multi-attribute compatibility.

### Innovation 4: Evidence Coverage Intelligence
- **Status:** `CONCEPT / NOT IMPLEMENTED`
- **Concept:** Quantitative mathematical metric assessing the ratio of verified source evidence tokens to generated procurement text, automatically flagging any generated clause with an evidence coverage score below 95%.
- **Prerequisites for Implementation:** Fine-grained token attribution masking and attention rollout mechanisms in the generation pipeline.

### Innovation 5: Human-in-the-Loop Procurement Review
- **Status:** `CONCEPT / NOT IMPLEMENTED`
- **Concept:** Interactive procurement officer review dashboard capturing manual accept/reject/override decisions on recommended standards and feeding them into an active learning preference model (DPO/RLHF).
- **Prerequisites for Implementation:** Multi-tenant user auth, auditable decision audit logs, and persistent feedback database tables.

### Innovation 6: Regulatory Change Simulation
- **Status:** `CONCEPT / NOT IMPLEMENTED`
- **Concept:** Monte Carlo or deterministic regulatory transition simulator modeling the supply-chain impact, vendor disqualification rate, and cost inflation when a voluntary standard becomes mandatory under an impending QCO deadline.
- **Prerequisites for Implementation:** Comprehensive market supplier database, national testing laboratory capacity figures, and import dependency statistics.

### Innovation 7: Requirement Ambiguity Resolution Loop
- **Status:** `CONCEPT / NOT IMPLEMENTED`
- **Concept:** Dynamic conversational clarification agent that detects high-entropy procurement descriptions, asks the minimal clarifying question (e.g., "Is this cable intended for underground trench or aerial installation?"), and reruns recommendation with updated priors.
- **Prerequisites for Implementation:** Bayesian clarification dialogue policy and conversational state tracker.

---

## 3. Grounding & Data Integrity Policy

1. **Source of Truth:** All active capabilities operate exclusively against the verified local SQLite database (`sih_bis.db`) containing 268 standards, 111 relationships, 275 versions, 710 QCO records, 1,573 certifications, 75 product licences, and 28 ministry mappings.
2. **Strict Fallback Handling:** Where data is not present in the verified dataset, the system deterministically outputs:
   - `Detailed clause text not available in current verified dataset`
   - `Not available in current verified dataset`
   - `UNKNOWN`
3. **No Fabricated Intelligence:** Under no circumstances are fictional laboratory locations, synthetic HUIDs, invented licence numbers, or unverified standard clauses injected into the platform.
