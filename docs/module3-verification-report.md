# Module 3 Verification Report: Standard Count & Relationship FK Resolution

**Audit Date**: September 16, 2026  
**System**: PS 26108 BIS Ingestion Pipeline  
**Database**: SQLite (`sih_bis.db`) / PostgreSQL Schema  
**Status**: Verified & Validated (100% test pass rate)

---

## Part 1: Canonical Standard Count Investigation

### User Query
> *"Explain clearly how 268 standards were produced from: `standards.csv` (234) + `sample_standards.json` (78). Are there overlaps? How many unique? Are any duplicates merged? Are any records omitted?"*

### Exact Arithmetic Breakdown

```
  standards.csv:          234 raw rows
- Duplicate rows merged:    4 duplicate rows
-----------------------------------------------
= Unique from CSV:        230 unique standards

  sample_standards.json:   78 raw records
- Overlapping with CSV:    40 records (enriched existing standards with scope, committee, amendments)
-----------------------------------------------
= New unique from JSON:    38 new standards

===============================================
TOTAL CANONICAL STANDARDS: 230 + 38 = 268
```

### 1. Duplicate Rows in `standards.csv` (4 rows merged)
In `standards.csv`, exactly 4 rows contain duplicate `standard_id` entries:
- **Row #87, #88, #89**: Duplicate entries for `IS 13252 (Part 1):2010` (Information Technology Equipment - Safety). Row #29 first established the canonical record; subsequent duplicate rows were merged into the canonical entity, preserving their raw data in the provenance metadata.
- **Row #205**: Duplicate entry for `IS 1239 (Part 1):2004` (Steel Tubes, Tubulars and Other Wrought Steel Fittings). Row #110 first established the canonical record; row #205 was safely merged into provenance.
- **Result**: Zero records omitted; duplicates are consolidated into single canonical records with 100% provenance audit history.

### 2. Overlap between `standards.csv` and `sample_standards.json` (40 records)
- **40 records** present in `sample_standards.json` already existed in `standards.csv` (e.g., `IS 694`, `IS 1293`, `IS 1554 (Part 1)`, `IS 9968 (Part 1)`, etc.).
- When `sample_standards.json` was processed, the pipeline detected the existing records by canonical standard ID / IS number. Rather than creating duplicate database entities, it **enriched** the existing canonical standard with:
  - Technical committee details (e.g., `ETD 08`, `CED 02`, `PCD 03`)
  - Detailed scope and description
  - Subject area and division
  - Version and amendment history in `standard_versions`
- Cross-dataset discrepancies (e.g., status differences) were explicitly registered in the `conflicts` table and provenance JSON.

### 3. Standards Unique to `sample_standards.json` (38 records)
- **38 records** in `sample_standards.json` did not exist in `standards.csv` (e.g., civil/building material standards like `IS 383:2016`, `IS 456:2000`, `IS 1489 (Part 1):2015`, `IS 269:2015`).
- These were inserted as new canonical `Standard` records in the database.

---

## Part 2: Relationship FK Resolution Investigation

### Metrics Summary

| Metric | Count | Percentage |
| :--- | :--- | :--- |
| **Total Relationships** | **111** | 100.0% |
| **Explicit Source Edges** (`relationships.json`) | 27 | 24.3% |
| **Derived Edges** (`sample_standards.json`, `standards.csv`) | 84 | 75.7% |
| **Resolved Target Foreign Keys** (`target_standard_id != NULL`) | **75** | **67.6%** |
| **Unresolved Targets** (`target_standard_id = NULL`) | **36** | **32.4%** |

### Unresolved Relationship Classification

Every single one of the 36 unresolved relationships has been audited against the raw datasets and classified according to the required taxonomy:

| Category | Classification Description | Count | % of Unresolved |
| :---: | :--- | :---: | :---: |
| **A** | Target standard genuinely does not exist in any supplied dataset | **11** | 30.6% |
| **B** | Target exists but standard-ID normalization failed | **0** | 0.0% |
| **C** | Target exists under a different part/section representation (multi-part series citation) | **25** | 69.4% |
| **D** | Target is present only as a textual relationship and cannot be resolved | **0** | 0.0% |
| **E** | Other data-quality issue | **0** | 0.0% |
| **Total** | | **36** | **100.0%** |

---

### Category C: Multi-Part Series Citations (25 items)

#### Why Target Foreign Key is Unlinked
In Indian Standards conventions, standards that define test methods or general supply conditions are frequently cited by their **base IS number series** (e.g., citing `IS 2386` for all aggregate testing, or `IS 4031` for all cement testing, or `IS 101` for paint testing).

However, the supplied standards catalog contains **specific parts** of these standards:
- The catalog contains `IS 2386 (Part 1):1963` and `IS 2386 (Part 4):1963`. A normative reference simply citing `IS 2386` cannot be arbitrarily mapped to Part 1 or Part 4 without corrupting domain accuracy.
- The catalog contains `IS 1367 (Part 1):2014` and `IS 1367 (Part 3):2017`. Fastener standards cite `IS 1367` generally.
- The catalog contains `IS 7098 (Part 1):1988` and `IS 7098 (Part 2):2011`.
- The catalog contains `IS 101 (Part 1/Sec 1):1986`. Paint standards cite `IS 101`.
- The catalog contains `IS 3025 (Part 1)`. Water standards cite `IS 3025`.
- In 5 cases (`IS 1180`, `IS 2026`, `IS 12640`, `IS 12933`, `IS 16046`), `standards.csv` indicates that the current parted standard supersedes an older unparted standard (e.g., `IS 1180 (Part 1):2014` supersedes `IS 1180:1989`). Linking `target_standard_id` to the current standard would create a false self-referential circular supersedes loop (`IS 1180 (Part 1)` supersedes itself).

#### Preservation Decision
The system preserves the exact citation in `target_standard_number` (e.g. `'IS 4031'`, `'IS 2386'`, `'IS 101'`) and sets `target_standard_id = NULL`. This prevents arbitrary part assignment while preserving full queryability across the knowledge graph.

#### Detailed Examples of Category C:
1. `IS 383:2016` --[NORMATIVE_REFERENCE]--> `'IS 2386'` (Database contains `IS 2386 (Part 1):1963` and `IS 2386 (Part 4):1963`)
2. `IS 269:2015` --[NORMATIVE_REFERENCE]--> `'IS 4031'` (Database contains `IS 4031 (Part 1):1996`)
3. `IS 455:2015` --[NORMATIVE_REFERENCE]--> `'IS 4031'` (Database contains `IS 4031 (Part 1):1996`)
4. `IS 1489 (Part 1):2015` --[NORMATIVE_REFERENCE]--> `'IS 3812'` (Database contains `IS 3812 (Part 1):2013`)
5. `IS 277:2018` --[NORMATIVE_REFERENCE]--> `'IS 513'` (Database contains `IS 513 (Part 1):2016`)
6. `IS 4985:2021` --[NORMATIVE_REFERENCE]--> `'IS 7834'` (Database contains `IS 7834 (Part 1):1987`)
7. `IS 10500:2012` --[NORMATIVE_REFERENCE]--> `'IS 3025'` (Database contains `IS 3025 (Part 1)`)
8. `IS 1363 (Part 1):2019` --[NORMATIVE_REFERENCE]--> `'IS 1367'` (Database contains `IS 1367 (Part 1)` and `(Part 3)`)
9. `IS 2395 (Part 1):1994` --[NORMATIVE_REFERENCE]--> `'IS 101'` (Database contains `IS 101 (Part 1/Sec 1):1986`)
10. `IS 1180 (Part 1):2014` --[SUPERSEDES]--> `'IS 1180'` (Superseded `IS 1180:1989`; unparted historical standard)

---

### Category A: Target Genuinely Does Not Exist in Supplied Catalog (11 items)

#### Why Target Foreign Key is Unlinked
These 11 standards are cited in `relationships.json` or in `standards.csv` supersedes fields, but **no record for them exists anywhere in the supplied standards datasets** (`standards.csv` or `sample_standards.json`). Per strict hackathon rules, external BIS datasets must not be downloaded or scraped.

#### Complete Enumeration of Category A:
1. `IS 15999 (Part 2/Sec 1)` — Cited in `relationships.json` by `IS 12615:2018` (Motors) under PERFORMANCE. Not present in standards catalog.
2. `IS/IEC 60034` — Cited in `relationships.json` by `IS 12615:2018` under SAFETY. Not present in standards catalog.
3. `IS 1608 (Part 1)` — Cited in `relationships.json` by `IS 1786:2008` (TMT Steel) under TESTING. Not present in standards catalog.
4. `IS 1599` — Cited in `relationships.json` by `IS 1786:2008` under TESTING (Bend test). Not present in standards catalog.
5. `IS 13920` — Cited in `relationships.json` by `IS 1786:2008` under SEISMIC_SAFETY (Ductile detailing). Not present in standards catalog.
6. `IS 4032` — Cited in `relationships.json` by `IS 269:2015` (Cement) under TESTING (Chemical analysis). Not present in standards catalog.
7. `IS 12235 (Part 1)` — Cited in `relationships.json` by `IS 4985:2021` (PVC Pipes) under TESTING. Not present in standards catalog.
8. `IS 10146` — Cited in `relationships.json` by `IS 4985:2021` under FOOD_CONTACT_SAFETY. Not present in standards catalog.
9. `IS 11346` — Cited in `relationships.json` by `IS 8034:2018` (Submersible pumps) under TESTING. Not present in standards catalog.
10. `IS 13947 (Part 2)` — Cited in `standards.csv` as superseded by `IS/IEC 60947 (Part 2):2019`. Obsolete standard not in current catalog.
11. `IS 780` — Cited in `standards.csv` as superseded by `IS 14846:2000` (Sluice valves). Obsolete standard not in current catalog.

#### Preservation Decision
All 11 targets are preserved verbatim in `StandardRelationship.target_standard_number` with `confidence=1.0` and source provenance pointing to `relationships.json` or `standards.csv`.

---

## Part 3: Test Suite & Integrity Confirmation

- **Total Unit & Integration Tests**: 31 tests
- **Pass Rate**: 100% (31/31 passed)
  - `tests/test_module1_data_inventory.py`: 8 passed
  - `tests/test_module2_database_schema.py`: 8 passed
  - `tests/test_normalizers.py`: 12 passed
  - `tests/test_module3_verification.py`: 3 passed
- **Validation Script**: `scripts/validate_ingestion.py` executed with `ALL INGESTION & VALIDATION CHECKS PASSED [OK]`.
- **Zero data loss**: All 111 relationship edges are preserved in the knowledge graph.
