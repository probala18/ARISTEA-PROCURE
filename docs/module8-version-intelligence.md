# Module 8 — Version and Amendment Intelligence Documentation

## 1. Overview & Objectives

Module 8 implements the **Version and Amendment Intelligence Service** for Problem Statement 26108 (*Identifying Applicable Indian Standards for Procurement Specifications*).

The module consolidates:
- **Version and Amendment History**: Grounded in the `StandardVersion` table populated during Module 2 ingestion from `standards.csv` and `sample_standards.json`.
- **Supersession Lineage**: Delegating strictly to Module 4's `SupersessionChainService` as the single source of truth.
- **Dataset-Backed Currency Intelligence**: Differentiating dataset-backed currency status from legal or regulatory currency determination.
- **Evidence-Grounded Warnings**: Emitting structured, provenanced warnings (`SUPERSEDED_WARNING`, `AMENDMENT_AVAILABLE`, `VERSION_GAP`, `UNKNOWN_VERSION_STATUS`) without speculative heuristics.
- **Section 66 API Endpoints**: Exposing `/api/standards/{standard_id}/versions`, `/api/standards/{standard_id}/amendments`, and `/api/standards/{standard_id}/currency` on the existing FastAPI application.

---

## 2. Adherence to Mandatory Constraints

| # | Mandatory Constraint | Implementation & Verification Evidence |
|---|----------------------|----------------------------------------|
| **1** | **Module 4 Single Source of Truth for Supersession** | Directly reuses `SupersessionChainService` and `RelationshipEngine`. Successor relationships are never independently inferred or reconstructed. |
| **2** | **Existing `StandardVersion` Table** | Reads from Module 2's `StandardVersion` table (275 records). Zero new tables or redundant columns created. |
| **3** | **`Standard.status` as Primary Signal** | Currency status (`is_current`) is evaluated strictly from `Standard.status == "CURRENT"`, never inferred solely from publication years. |
| **4** | **No Automatic `OUTDATED_VERSION_WARNING`** | `latest_year != publication_year` does NOT trigger `OUTDATED_VERSION_WARNING`. Instead, it emits `VERSION_GAP` indicating a recorded revision interval. |
| **5** | **Evidence-Grounded Concepts** | Strictly separates `CURRENT`, `SUPERSEDED`, `AMENDMENT_AVAILABLE`, `VERSION_GAP`, and `UNKNOWN_VERSION_STATUS`. |
| **6** | **Superseded Successor Discipline** | `SUPERSEDED_WARNING` includes successor information *only* when the Module 4 graph explicitly establishes it (e.g. `IS 325` -> `IS 12615:2018`). |
| **7** | **Amendment Record Identification** | `AMENDMENT_AVAILABLE` identifies and quotes the actual `StandardVersion` amendment records supporting the warning. |
| **8** | **Source Provenance Preservation** | Every version record, amendment, warning, and supersession statement carries `source_dataset` and `source_provenance`. |
| **9** | **Dataset-Backed Currency Disclaimer** | `/currency` responses include an explicit disclaimer stating this is dataset-backed intelligence, not an independent legal determination. |
| **10**| **Distinction: Dataset Intelligence vs Legal Currency** | Clear distinction documented in models, OpenAPI documentation, and response disclaimers. |
| **11**| **Dual Lookup Support** | Resolves canonical standard ID (e.g. `IS 12615:2018`), normalized number (`IS 12615`), and integer database PK (`1`). |
| **12**| **Historical/Uncatalogued Safety** | Never manufactures synthetic `Standard` rows for uncatalogued historical references. Unresolved targets remain string representations. |
| **13**| **Code Reuse** | Reuses Module 4 resolver, traverser, and supersession logic without duplication. |
| **14**| **FastAPI Route Registration** | Routes registered with `standards_router` under `/api` prefix and validated via `TestClient`. |
| **15**| **OpenAPI Schema Verification** | Verified all three endpoints appear under `/openapi.json`. |
| **16**| **Supplied Examples Tested** | Validated against `IS 12615` (CURRENT), `IS 325` (SUPERSEDED with successor `IS 12615:2018`), and `IS 694` (CURRENT). |
| **17**| **Cumulative Test Reconciliation** | Previous test count: **82**. Module 8 new tests: **14**. Total cumulative: **96**. All 96 passed. |
| **18**| **Zero Ingested Data Mutation** | Module 8 is strictly read-only. Database row counts verified identical before and after calls. |
| **19**| **No External Data/Hallucination** | No web data, external BIS data, or model weights used to fill missing records. |
| **20**| **Automated Test & Audit Execution** | Ran `python -m pytest tests/ -v --tb=short` (96/96 passed) and `scripts/validate_ingestion.py` (all checks passed). |
| **21**| **Documentation Updated** | Authored `docs/module8-version-intelligence.md`. |
| **22**| **Health Check Update** | Updated `/api/health` to `"Module 7 — Relationship Engine & Module 8 — Version & Amendment Intelligence"`. |

---

## 3. Architecture & Service Layer Design

```
+---------------------------------------------------------------------------------+
|                        FastAPI Standards Router (/api)                         |
|   GET /standards/{id}/versions  |  GET /standards/{id}/amendments  |  /currency |
+---------------------------------------------------------------------------------+
                                      |
                                      v
+---------------------------------------------------------------------------------+
|                 Module 8: VersionIntelligenceService                           |
|  - resolve_standard(id_or_number)                                               |
|  - get_version_report(standard_id)                                              |
|  - get_amendments(standard_id)                                                  |
|  - check_currency(standard_id)                                                  |
|  - batch_version_check(identifiers)                                             |
+---------------------------------------------------------------------------------+
           |                                  |
           v                                  v
+-----------------------+          +----------------------------------------------+
| Module 2 DB Tables    |          | Module 4 Knowledge Graph Services            |
| - standards           |          | - RelationshipEngine                         |
| - standard_versions   |          | - SupersessionChainService (single truth)    |
| - relationships       |          | - StandardReferenceResolver                  |
+-----------------------+          +----------------------------------------------+
```

---

## 4. Evidence Rules & Warning Types

| Warning Type | Trigger Condition | Severity | Evidence Grounding |
|--------------|-------------------|----------|--------------------|
| `SUPERSEDED_WARNING` | `Standard.status == "SUPERSEDED"` | `CRITICAL` | Module 4 `SupersessionChainService` successors list, `Standard.source_file`. |
| `AMENDMENT_AVAILABLE` | `StandardVersion` rows where `amendment_number IS NOT NULL` or `amendment_year IS NOT NULL` | `INFO` | List of amendment records with IDs, years, descriptions, and source datasets. |
| `VERSION_GAP` | `StandardVersion.latest_year != Standard.publication_year` | `INFO` | Publication year vs latest version year comparison, version ID, source dataset. |
| `UNKNOWN_VERSION_STATUS` | Standard exists in database but has zero `StandardVersion` rows | `INFO` | Standard identifier and notice of absent ingested version records. |

---

## 5. API Endpoint Specifications (Section 66)

### 1. `GET /api/standards/{standard_id}/versions`
- **Response**: `VersionIntelligenceReport`
- **Fields**:
  - `standard_id`, `canonical_id`, `is_number`, `title`, `status`, `publication_year`, `latest_year`
  - `version_records`: Complete list of version entries with full provenance
  - `amendments`: Filtered list of amendment records
  - `supersession`: Predecessor and successor lineage from Module 4
  - `warnings`: Evidence-based warnings
  - `disclaimer`: Explicit notice regarding dataset-backed scope

### 2. `GET /api/standards/{standard_id}/amendments`
- **Response**: `List[AmendmentRecord]`
- **Fields**:
  - `id`, `standard_id`, `is_number`, `amendment_number`, `amendment_year`, `change_description`, `current_state`, `source_dataset`, `source_provenance`

### 3. `GET /api/standards/{standard_id}/currency`
- **Response**: `CurrencyCheckResult`
- **Fields**:
  - `standard_id`, `canonical_id`, `is_number`, `title`, `status`, `publication_year`, `latest_year`, `is_current`, `warnings`, `total_amendments`, `disclaimer`

---

## 6. Verification & Test Results

### 1. Test Suite Execution (`pytest`)
- **Previous Baseline Test Count**: 82 tests
  - Module 1 (Data Inventory): 8 tests
  - Module 2 (Database Schema): 8 tests
  - Module 3 (Ingestion Verification): 3 tests
  - Module 4 (Knowledge Graph): 18 tests
  - Module 5 (Retrieval & Search): 12 tests
  - Module 6 (Recommendation Engine): 8 tests
  - Module 7 (Relationship Engine): 13 tests
  - Normalizers: 12 tests
- **Module 8 New Tests**: 14 tests (`tests/test_module8_version_intelligence.py`)
  1. `test_01_version_report_known_standard_is_12615`: PASS
  2. `test_02_amendment_separation_and_provenance`: PASS
  3. `test_03_superseded_detection_with_successor_is_325`: PASS
  4. `test_04_current_standard_verification_is_694`: PASS
  5. `test_05_missing_version_handling_unknown_version_status`: PASS
  6. `test_06_year_interval_reporting_version_gap`: PASS
  7. `test_07_provenance_preservation`: PASS
  8. `test_08_dual_lookup_id_vs_code`: PASS
  9. `test_09_nonexistent_standard_404`: PASS
  10. `test_10_disclaimer_presence_and_legal_currency_distinction`: PASS
  11. `test_11_batch_version_check`: PASS
  12. `test_12_openapi_schema_registration`: PASS
  13. `test_13_health_endpoint_module8`: PASS
  14. `test_14_read_only_integrity_zero_mutations`: PASS
- **Total Cumulative Tests**: **96 tests collected, 96 passed (100% pass rate)**.

### 2. Ingestion Validation Audit (`scripts/validate_ingestion.py`)
- **Standards Table**: 268 records [OK]
- **Standard Relationships**: 111 records [OK]
- **Standard Versions**: 275 records [OK]
- **Provenance Coverage**: 100% [OK]
- **Explicit vs Derived Separation**: 27 explicit, 84 derived [OK]
- **Unlinked Target Preservation**: 36 unresolved targets preserved as strings [OK]
- **Regulatory Divergence Audit**: 97 ambiguous standards detected [OK]
- **Overall Audit Result**: ALL INGESTION & VALIDATION CHECKS PASSED [OK]

---

## 7. Limitations & Operational Scope

1. **Dataset-Backed Boundary**: The service reflects the version and amendment records ingested in `sih_bis.db` (275 versions across 268 standards). It does not autonomously poll external BIS portals.
2. **Legal Currency Caveat**: A standard marked `is_current = True` indicates that the dataset records it as `CURRENT`. For legal and tender enforcement, users must cross-reference official BIS Gazette notifications.
3. **Historical Uncatalogued Successors**: When older standards reference uncatalogued pre-1980s specifications not present in `standards.csv`, they remain unlinked strings without fabricated database rows.
