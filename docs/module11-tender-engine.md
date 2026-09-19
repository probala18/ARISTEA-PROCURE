# Module 11: Tender Document Processing & Tender Document Engine

## Overview
Module 11 implements the **Tender Document Engine** for Problem Statement 26108 (*Identifying Applicable Indian Standards for Procurement Specifications*). It ingests, parses, segments, and analyzes public procurement tender documents (in **PDF**, **DOCX**, and **TXT** formats), preserving fine-grained provenance down to the exact page, section, clause, and character offsets.

---

## 1. Document Processing Architecture (Section 86)

```
                 Uploaded Tender File (PDF, DOCX, TXT)
                                   |
                +------------------v------------------+
                |         get_parser(filename)        |
                +------------------+------------------+
                                   |
         +-------------------------+-------------------------+
         |                         |                         |
+--------v--------+       +--------v--------+       +--------v--------+
|    PDFParser    |       |   DOCXParser    |       |    TXTParser    |
| (PyMuPDF/fitz)  |       |  (python-docx)  |       | (Plain Parser)  |
+--------+--------+       +--------+--------+       +--------+--------+
         |                         |                         |
         +-------------------------+-------------------------+
                                   |
                     DocumentParseResult (Pages + Metadata)
                                   |
                     +-------------v-------------+
                     |       ClauseDetector      |
                     +-------------+-------------+
                                   |
             Sections + Numbered Clauses + Attributes + Intent
                                   |
                     +-------------v-------------+
                     |     StandardExtractor     |
                     +-------------+-------------+
                                   |
             Grounding Against Canonical SQLite Standards & Graph
                                   |
                     +-------------v-------------+
                     |    Database Persistence   |
                     +---------------------------+
                     - tender_documents
                     - tender_sections
                     - tender_requirements
                     - tender_standard_references
```

### Supported Document Formats
1. **PDF (`PDFParser`)**:
   - Implemented using **PyMuPDF** (`pymupdf`) as mandated by Section 86.
   - Extracts page rects, text streams, and rotational angles with 1-indexed page preservation.
2. **DOCX (`DOCXParser`)**:
   - Implemented using **python-docx**.
   - Extracts structured headings, body paragraphs, and tabular cells (BOQ items and specification tables).
3. **TXT (`TXTParser`)**:
   - Handles structured plain-text tender specifications with form-feed (`\x0c`) page segmentation and UTF-8 / Latin-1 fallback decoding.

---

## 2. Clause & Section Segmentation (`ClauseDetector`)

- **Section Types**:
  - `TECHNICAL_SPEC`: Technical specifications, material requirements, equipment parameters.
  - `TESTING_AND_COMPLIANCE`: Quality assurance, type testing, routine inspection, factory acceptance.
  - `SCOPE_OF_WORK`: Overall scope of supply and project deliverables.
  - `ELIGIBILITY`: Bidder qualifications and technical criteria.
  - `BOQ`: Bill of quantities, schedules of items.
  - `GENERAL_TERMS`: Commercial and legal conditions.
- **Clause Extraction**:
  - Identifies numbered clauses (`Clause 1.1`, `3.2.1`, `Item 4`, `(a)`).
  - Preserves exact source text and character boundaries.
  - Detects mandatory status via modal verbs (`shall`, `must`, `mandatory`, `required`).
  - Extracts engineering attributes:
    - **Voltage Ratings** (e.g. `1.1 kV`, `415 V`)
    - **Power Ratings** (e.g. `55 kW`, `75 HP`)
    - **Temperature Ratings** (e.g. `70 deg C`)
    - **Dimensions & Sizes** (e.g. `4 sq mm`, `50 mm`)

---

## 3. Explicit Standard Extraction & Database Grounding (`StandardExtractor`)

- **Pattern Matching**:
  - Matches Indian Standards citations (`IS 12615:2018`, `IS 694`, `IS: 269`, `IS/IEC 60034-1`, `IS 325`).
- **Deterministic Registry Resolution**:
  - Grounds detected citations against the authoritative SQLite `standards` table.
  - Resolves primary standard ID, title, and validity.
- **Supersession Lineage via Module 4 Knowledge Graph**:
  - Detects if an explicit standard is superseded in the graph (e.g., `IS 325` superseded by `IS 12615:2018`).
  - Identifies successor standard ID and successor number directly from `standard_relationships` (`SUPERSEDES` edge).
- **Zero Data Loss for Unlinked References**:
  - Standards not present in the local database (e.g., unlisted or niche standards) are preserved verbatim with `detected_standard_id = None` and `is_valid = False`, ensuring complete tender audit transparency.

---

## 4. Section 67 Tender API Specifications

### 1. `POST /api/tenders/upload`
Uploads and parses a tender document.
- **Form Data**:
  - `file`: PDF, DOCX, or TXT file.
  - `tender_number`: Optional custom tender reference number.
  - `title`: Optional title.
  - `organization`: Optional procuring department.
- **Response**:
```json
{
  "tender_id": 1,
  "tender_number": "TND-A1B2C3D4",
  "filename": "motor_tender.pdf",
  "file_type": "PDF",
  "file_size": 24820,
  "status": "COMPLETED",
  "total_pages": 2,
  "total_sections": 2,
  "total_clauses": 5,
  "total_standards_detected": 3,
  "created_at": "2026-09-19T18:30:00"
}
```

### 2. `GET /api/tenders/{id}`
Retrieves tender metadata and section outline.

### 3. `GET /api/tenders/{id}/status`
Returns processing lifecycle status (`QUEUED`, `PROCESSING`, `COMPLETED`, `FAILED`).

### 4. `GET /api/tenders/{id}/requirements`
Retrieves extracted technical clauses with product keywords and engineering attributes.

### 5. `GET /api/tenders/{id}/references`
Retrieves explicit Indian Standard references with clause context and supersession flags.

---

## 5. Test Verification Summary

- **Module 11 Test Suite** ([`tests/test_module11_tender_engine.py`](file:///c:/Users/BALASUNDAR%20M/Documents/SIH%202026/tests/test_module11_tender_engine.py)): **18 passed, 0 failed**.
- **Full Project Regression Test Suite**: **151 passed, 0 failed** across all 11 modules:
  - `test_module1_data_inventory.py`: 8 passed
  - `test_module2_database_schema.py`: 12 passed
  - `test_module3_verification.py`: 4 passed
  - `test_module4_knowledge_graph.py`: 20 passed
  - `test_module5_retrieval.py`: 12 passed
  - `test_module6_recommendation.py`: 14 passed
  - `test_module7_relationship_engine.py`: 11 passed
  - `test_module8_version_intelligence.py`: 16 passed
  - `test_module9_compliance_intelligence.py`: 12 passed
  - `test_module10_speech_ai.py`: 19 passed
  - `test_module11_tender_engine.py`: 18 passed
  - `test_normalizers.py`: 5 passed
- **Dataset Ingestion Validation Audit** ([`scripts/validate_ingestion.py`](file:///c:/Users/BALASUNDAR%20M/Documents/SIH%202026/scripts/validate_ingestion.py)):
  - 100% provenance verified across all tables.
  - Zero core data mutations.
