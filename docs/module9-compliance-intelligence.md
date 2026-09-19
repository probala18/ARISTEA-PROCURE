# Module 9 — Compliance Intelligence Documentation

## 1. Overview & Objectives

Module 9 implements the **Deterministic Compliance Intelligence Service** for Problem Statement 26108 (*Identifying Applicable Indian Standards for Procurement Specifications*).

The module integrates and correlates regulatory facts across five core ingested datasets:
1. **Certification Records** (`certification_records` — 1,573 records from `certification.csv`, `ReportExcel.csv`, `schem.csv`, `standards.csv`).
2. **Quality Control Orders** (`qco_records` — 710 records from `schem.csv`, `standards.csv`).
3. **Product Licence Volumes** (`product_licences` — 75 product category records from `productlicence.csv`).
4. **Ministry / Department Procurement Mappings** (`ministry_product_mappings` — 28 records from `upcomming.csv`).
5. **Canonical Standards & Schemes** (`standards` — 268 records with `certification_scheme` field).

Module 9 delivers:
- **Deterministic Requirement-Level Evaluation**: Classifies compliance status strictly into `MANDATORY`, `VOLUNTARY`, `CONDITIONAL`, or `UNKNOWN` based exclusively on explicit ingested records.
- **Strict Evidence Guardrails**: Never infers mandatory status from standard existence, product licence presence, or dataset appearance.
- **Scope-Aware Regulatory Divergence Detection**: Flags standards where certification records list voluntary compliance while active Quality Control Orders mandate statutory enforcement (e.g. `IS 21`, `IS 26`, `IS 27`).
- **Grounded Scheme Classification**: Identifies `BIS_ISI` (Scheme-I), `CRS` (Compulsory Registration Scheme / Scheme-II), `HALLMARKING`, and Scheme-IV directly from dataset records.
- **Section 66 & Batch API Endpoints**: Exposes `GET /api/standards/{standard_id}/certification`, enhances `GET /api/standards/{standard_id}/compliance`, and adds bounded bulk endpoint `POST /api/standards/compliance/batch`.

---

## 2. Adherence to Mandatory Constraints

| # | Mandatory Constraint | Implementation & Verification Evidence |
|---|----------------------|----------------------------------------|
| **1** | **Deterministic Evidence Layer** | Zero LLM or external knowledge used. Logic is pure rule-based evaluation over database records. |
| **2** | **Ingested Datasets Only** | Grounded strictly in `certification_records`, `qco_records`, `product_licences`, `ministry_product_mappings`, `standards`. |
| **3** | **Exact Requirement-Level Logic** | Explicit mandatory QCO/cert -> `MANDATORY`; conditional cert -> `CONDITIONAL`; voluntary cert with no QCO -> `VOLUNTARY`; missing evidence -> `UNKNOWN`. |
| **4** | **No Inferred Mandatory Status** | Standard existence, product licence presence, or dataset appearance never triggers `MANDATORY`. |
| **5** | **Verbatim QCO Status Preservation** | QCO status is preserved verbatim from dataset (`None` or string). Never synthesized as `ACTIVE`. |
| **6** | **Reuse of Module 4/8 Services** | Reuses `RelationshipEngine.resolve_standard` and `ComplianceConnectorService` without duplication. |
| **7** | **All Evidence Records Preserved** | Voluntary records are never dropped or suppressed when a mandatory QCO coexists. |
| **8** | **Scope-Aware Regulatory Divergence** | Coexistence of voluntary certification and mandatory QCO triggers `REGULATORY_DIVERGENCE` while preserving both records. |
| **9** | **Grounded Scheme Classification** | Mapped strictly from `standard.certification_scheme` and `certification_records.certification_type`. Never guessed from product titles. |
| **10**| **Hallmarking Grounding Discipline** | `HALLMARKING` scheme returned strictly when dataset explicitly supports it (`IS 1417:2016`). |
| **11**| **Full Provenance Preserved** | Every certification, QCO, licence, and divergence record carries `source_dataset` and `source_provenance`. |
| **12**| **Clear Concept Separation** | Status (`MANDATORY`/`VOLUNTARY`/`CONDITIONAL`/`UNKNOWN`) separated from descriptive counts and evidence presence. |
| **13**| **Confidence Score Caveat** | `confidence_score` documented as internal decision-support metric, never presented as legal certainty. |
| **14**| **Zero Synthetic Data Creation** | No synthetic records or edges created in any database tables. |
| **15**| **Bounded Bulk Loading (No N+1)** | `batch_evaluate_compliance` pre-fetches standards, certs, QCOs, and mappings using single `in_()` queries. |
| **16**| **Module 7 Backward Compatibility** | `GET /compliance` preserves all legacy `ComplianceLinksResult` fields with identical keys and types. |
| **17**| **FastAPI Route & Schema Validation** | Tested `TestClient` routes against Pydantic schemas; all appear in `/openapi.json`. |
| **18**| **Read-Only Database Integrity** | Verified table counts remain identical before and after compliance evaluations. |
| **19**| **Supplied Dataset Validation** | Manual validation of cables, motors, IS 21, IS 26, and IS 27 verified strictly against project datasets. |
| **20**| **Comprehensive Case Testing** | 18 unit tests covering mandatory, voluntary, conditional, unknown, uncatalogued, divergence, and batch. |
| **21**| **Verification Execution** | Full pytest regression (114/114 passed) and `scripts/validate_ingestion.py` (all checks passed). |
| **22**| **Reconciled Test Reporting** | 96 previous + 18 new = 114 total cumulative tests. |
| **23**| **Documentation Updated** | Authored `docs/module9-compliance-intelligence.md`. |
| **24**| **Module 10 Stop Discipline** | Halted at Module 9 completion for user review. |

---

## 3. Requirement-Level Evaluation Logic

```
                    +--------------------------------+
                    |  Standard / Reference Input   |
                    +--------------------------------+
                                    |
                                    v
                    +--------------------------------+
                    | Query certs, qcos, mappings    |
                    +--------------------------------+
                                    |
       +----------------------------+----------------------------+
       |                            |                            |
       v                            v                            v
[Mandatory QCO               [Conditional Cert           [Voluntary Cert
 OR Mandatory Cert]           AND No Mandatory]           AND No Mandatory]
       |                            |                            |
       v                            v                            v
  MANDATORY                    CONDITIONAL                   VOLUNTARY
       |
       +---> [If Voluntary Cert also present]
             ---> Flag: REGULATORY_DIVERGENCE
             ---> Preserve all records in evidence
```

If zero certification records and zero QCO records exist for the standard:
→ Conclusion: **`UNKNOWN`** with explicit disclaimer.

---

## 4. Regulatory Divergence Cases in Project Dataset

| Standard | Product Scope | Voluntary Record Source | Mandatory Mandate Source | Resolved Status |
|---|---|---|---|---|
| **IS 21** | Wrought Aluminium & Aluminium Alloys | `ReportExcel.csv` (VOLUNTARY) | `schem.csv` (Aluminium and Aluminium Alloys QCO, mand=True) | `MANDATORY` + `REGULATORY_DIVERGENCE` |
| **IS 26** | Tin Ingot Specification | `ReportExcel.csv` (VOLUNTARY) | `schem.csv` (Tin Ingot QCO, mand=True) | `MANDATORY` + `REGULATORY_DIVERGENCE` |
| **IS 27** | Primary Lead Specification | `ReportExcel.csv` (VOLUNTARY) | `schem.csv` (Primary Lead QCO, mand=True) | `MANDATORY` + `REGULATORY_DIVERGENCE` |

---

## 5. Scheme Classification Grounding

| Scheme Type | Criteria from Supplied Datasets | Actual Verified Examples |
|---|---|---|
| **`BIS_ISI`** | `Standard.certification_scheme` contains `"Scheme-I"` or `"ISI Mark"` OR `CertificationRecord.certification_type == "BIS_ISI"` | `IS 694:2010` (Scheme-I / ISI Mark), `IS 12615:2018` |
| **`CRS`** | `Standard.certification_scheme` contains `"CRS"` or `"Scheme-II"` OR `CertificationRecord.certification_type == "CRS"` | `IS 13252 (Part 1):2010` (IT Equipment Safety) |
| **`HALLMARKING`** | `Standard.certification_scheme` contains `"Hallmarking"` | `IS 1417:2016` (Gold and Silver Fineness and Marking) |
| **`SCHEME_IV`** | `Standard.certification_scheme` contains `"Scheme-IV"` | Building Codes, Codes of Practice, Testing Codes |

---

## 6. API Endpoint Specifications

### 1. `GET /api/standards/{standard_id}/certification` (Section 66)
- **Response**: `StandardCertificationReport`
- **Fields**:
  - `standard_id`, `canonical_id`, `is_number`, `title`
  - `requirement_level`: `MANDATORY` | `VOLUNTARY` | `CONDITIONAL` | `UNKNOWN`
  - `governing_scheme`: `BIS_ISI` | `CRS` | `HALLMARKING` | `SCHEME_I` | `SCHEME_II` | `SCHEME_IV` | `UNKNOWN`
  - `total_certifications`, `total_qcos`
  - `certifications`: List of `GroundedCertificationRecord` with full provenance
  - `qco_mandates`: List of `GroundedQCORecord` with status preserved verbatim
  - `disclaimer`: Legal disclaimer

### 2. `GET /api/standards/{standard_id}/compliance` (Enriched & Backward Compatible)
- **Response**: `ComplianceIntelligenceReport`
- **Fields**:
  - All Module 7 `ComplianceLinksResult` fields (`is_mandatory_certification`, `qco_applicable`, `certification_records`, `qco_records`, `product_licences`, `ministry_mappings`, `regulatory_divergence_detected`, `regulatory_divergence_notes`)
  - Module 9 fields (`requirement_level`, `governing_scheme`, `divergences`, `confidence_score`, `evidence_count`, `disclaimer`)

### 3. `POST /api/standards/compliance/batch` (Bounded Bulk Loading)
- **Payload**: `{"identifiers": ["IS 694", "IS 12615", "IS 21", "IS 1417"]}`
- **Response**: `BatchComplianceResult` with per-standard evaluation, totals by requirement level, and zero N+1 query overhead.

---

## 7. Verification & Test Metrics

### Pytest Test Suite Results
* **Previous Cumulative Tests (Module 1 - 8)**: 96 tests
* **Module 9 New Tests**: 18 tests ([`tests/test_module9_compliance_intelligence.py`](file:///c:/Users/BALASUNDAR%20M/Documents/SIH%202026/tests/test_module9_compliance_intelligence.py)):
  1. `test_01_mandatory_compliance_cables_is_694`: PASS
  2. `test_02_mandatory_compliance_motors_is_12615`: PASS
  3. `test_03_scope_aware_regulatory_divergence_is_21_is_26_is_27`: PASS
  4. `test_04_explicit_voluntary_evidence_handling`: PASS
  5. `test_05_explicit_conditional_evidence_handling`: PASS
  6. `test_06_unknown_status_for_missing_evidence`: PASS
  7. `test_07_hallmarking_scheme_grounding_is_1417`: PASS
  8. `test_08_crs_scheme_grounding_is_13252`: PASS
  9. `test_09_qco_status_preservation_no_active_fabrication`: PASS
  10. `test_10_backward_compatibility_module7_compliance`: PASS
  11. `test_11_section_66_certification_endpoint`: PASS
  12. `test_12_batch_compliance_endpoint_no_n_plus_1`: PASS
  13. `test_13_dual_lookup_id_vs_code`: PASS
  14. `test_14_nonexistent_standard_404`: PASS
  15. `test_15_provenance_preservation`: PASS
  16. `test_16_openapi_schema_registration`: PASS
  17. `test_17_read_only_integrity_zero_mutations`: PASS
  18. `test_18_health_check_module9`: PASS
* **Total Project Tests**: **114 collected, 114 passed (100% pass rate)** in 24.38s.

### Ingestion Validation Audit (`scripts/validate_ingestion.py`)
- **100% of core database tables verified**: 268 standards, 275 versions, 111 relationships, 710 QCO records, 1,573 certification records, 75 product licences, 28 ministry mappings.
- **100% source provenance intact**: Zero records missing provenance.
- **Audit Verdict**: `ALL INGESTION & VALIDATION CHECKS PASSED [OK]`.

---

## 8. Limitations & Operational Scope

1. **Dataset-Grounded Scope**: Compliance intelligence represents facts as recorded in `certification_records`, `qco_records`, and `standards`. Gazette notifications issued subsequent to dataset compilation are not autonomously fetched.
2. **Advisory Decision Support**: Evaluations do not constitute legal certification advice. Tender officers must cross-reference official Gazette orders for statutory enforcement.
3. **Uncatalogued Standards**: References to standards present in `schem.csv` or `certification.csv` that do not exist in `standards.csv` (e.g. `IS 21`) are evaluated directly from compliance records without fabricating synthetic standard rows.
