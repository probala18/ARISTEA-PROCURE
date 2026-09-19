# Module 12: Tender Gap Detection & Evidence-Based Audit

## Overview
Module 12 implements the **Tender Gap Detection & Evidence-Based Audit Engine** for Problem Statement 26108 (*Identifying Applicable Indian Standards for Procurement Specifications*). Building upon the parsed clauses and standard references extracted in Module 11, Module 12 conducts an end-to-end, deterministic, multi-stage audit:

```
Tender Document
       │
       ▼
Extracted Requirements (Module 11)
       │
       ▼
Existing Standard References (Module 11)
       │
       ▼
Semantic Recommendation (Module 6)
       │
       ▼
Version Intelligence (Module 8)
       │
       ▼
Compliance Intelligence (Module 9)
       │
       ▼
Gap Detection (Module 12 Engine)
       │
       ▼
Evidence-Based Audit Report (Module 12 API / DB)
```

---

## 1. Core Principles & Section 83 Trust Model

### Strictly Non-Punitive Absence Handling
A core architectural mandate of Module 12 is:
> **The absence of a standard citation in a tender clause must NEVER be treated as automatic non-compliance.**

A gap is only reported under rigorous, evidence-supported categories:
1. `MISSING_REFERENCE`: A product or specification is detailed in the tender without citing the corresponding Indian Standard identified by deterministic or high-confidence recommendation.
2. `OUTDATED_REFERENCE`: An explicit standard is cited in the tender, but the Version Intelligence service confirms it has been withdrawn or superseded by an active edition.
3. `POTENTIALLY_MISSING_TESTING_STANDARD`: A governing product standard is cited, but the knowledge graph identifies an essential allied testing standard that is not referenced for acceptance testing.
4. `POTENTIALLY_MISSING_SAFETY_STANDARD`: A governing product standard is cited, but normative safety standards connected in the knowledge graph are omitted.
5. `CERTIFICATION_GAP`: A cited standard falls under an active mandatory Quality Control Order (QCO), but the tender specification fails to require mandatory BIS certification / ISI mark.
6. `COMPLIANCE_EVIDENCE_MISSING`: An unlisted or unrecognizable standard number is cited in the tender with no corroborating evidence in the canonical BIS registry.
7. `AMBIGUOUS_SPECIFICATION`: A procurement requirement is technically vague or broad, triggering clarification options rather than definitive gaps.
8. `SUFFICIENT_EVIDENCE`: Current, valid standards with verified compliance evidence.

### Section 83 Trust Hierarchy
Every finding in the audit report carries an explicit trust level:
- **`KNOWN`**: Directly extracted from the explicit text of the tender document.
- **`INFERRED`**: Derived by semantic recommendation, graph traversal, or allied relationship inference.
- **`UNKNOWN`**: Genuinely unestablished due to insufficient dataset evidence.

---

## 2. Expected-vs-Present Architecture

The audit report provides a transparent, dual-perspective comparison:

| Component | Description |
|---|---|
| `present_standards` | All explicit standards cited in the tender, with current validity and supersession status |
| `expected_standards` | All standards inferred as necessary based on technical clauses, equipment scope, and knowledge graph links |
| `missing_standards` | High-confidence expected standards not present in the tender citations |
| `outdated_standards` | Standards present in the tender that have been superseded by newer revisions |
| `testing_gaps` | Knowledge graph testing standards missing from testing clauses |
| `safety_gaps` | Knowledge graph safety standards missing from safety clauses |
| `certification_gaps` | Clauses citing QCO-governed standards without mandating ISI mark / BIS license |
| `coverage_score` | Calibrated ratio between 0.0 and 1.0 (and percentage) reflecting standard compliance coverage |

---

## 3. Data Flow & Integration Points

1. **`TenderGapAnalyzer` (`backend/app/services/tender_audit/gap_analyzer.py`)**:
   - Analyzes explicit references using `VersionIntelligenceService` and `ComplianceIntelligenceService`.
   - Inspects `AlliedStandardsGroup` from `RelationshipEngine` for testing and safety edges.
   - Evaluates ungrounded technical requirements using `RecommendationEngine`.
   - Computes weighted coverage metrics and compiles `TenderAuditReport`.

2. **`TenderAuditService` (`backend/app/services/tender_audit/audit_service.py`)**:
   - Manages lifecycle execution and DB persistence to `tender_audit_results`.
   - Updates `TenderDocument.status` to `'AUDITED'`.
   - Caches completed audit reports for sub-millisecond retrieval.

3. **REST API (`backend/app/api/tenders.py`)**:
   - `GET /api/tenders/{id}/audit`: Retrieves or generates the full audit report.
   - Includes full gap breakdown, expected-vs-present lists, and Section 83 disclaimers.

4. **Health Check (`/api/health`)**:
   - Module 12 is registered with operational status in the system health response.
