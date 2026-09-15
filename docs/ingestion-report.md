# BIS AI Recommendation Engine — Dataset Ingestion & Validation Report

**Execution Timestamp**: `2026-09-15T17:42:03.684254`  
**Total Duration**: `1.54 seconds`  

## 1. Datasets Processed (12 of 12 Authoritative Files)

| Dataset File | Processed Records | Role / Target Entity |
|:---|:---:|:---|
| `manifest.json` | 10 | Source Document Provenance (`SourceDocument`) |
| `standards.csv` | 234 | Core Indian Standards (`Standard`, `StandardVersion`) |
| `sample_standards.json` | 78 | Detailed Standards, Normative Refs (`Standard`, `StandardRelationship`) |
| `relationships.json` | 9 | Explicit Domain Knowledge Graph Edges (`StandardRelationship`) |
| `schem.csv` | 711 | Quality Control Orders / QCO Compliance (`QCORecord`) |
| `certification.csv` | 32 | ISI Mark Certification Products (`CertificationRecord`) |
| `bis_standards.csv` | 65 | Compulsory Registration Scheme / IT (`CertificationRecord`, `ProcurementAlias`) |
| `ReportExcel.csv` | 1,476 | Mandatory vs Voluntary Status (`CertificationRecord`) |
| `bis_standards.json` | 77 | Licence Count Cross-Verification (`ProductLicence`) |
| `productlicence.csv` | 76 | Product Licence Counts (`ProductLicence`) |
| `upcomming.csv` | 28 | Ministry / Department Product Standards (`MinistryProductMapping`, `ProcurementAlias`) |
| `query_dataset.json` | 14 | Benchmark Evaluation Queries (`EvaluationQuery`) |

## 2. Ingested Database Entities & Statistics

| Entity Name | Database Table | Count | Linkage / Notes |
|:---|:---|:---:|:---|
| **Indian Standards** | `standards` | **268** | 0 created, 312 merged |
| **Explicit Relationships** | `standard_relationships` | **27** | Source: `relationships.json` (`is_explicit_source=True`) |
| **Derived Relationships** | `standard_relationships` | **84** | Source: `normative_references`, `supersedes` (`is_explicit_source=False`) |
| **Standard Versions & Amendments** | `standard_versions` | **0** | Version history and formal amendment tracking |
| **Quality Control Orders (QCO)** | `qco_records` | **710** | 66 linked to standards table |
| **Certification Records** | `certification_records` | **1,573** | 135 linked to standards table |
| **Product Licences** | `product_licences` | **0** | Factual counts (strictly non-equated to mandatory) |
| **Ministry Product Mappings** | `ministry_product_mappings` | **0** | Government departmental context |
| **Technical Committees / Departments** | `departments` | **0** | ETD, CED, MED technical bodies |
| **Source Documents** | `source_documents` | **0** | Document provenance anchors from manifest |
| **Evaluation Queries** | `evaluation_queries` | **0** | Ground-truth test benchmark suite |

## 3. Provenance & Conflict Resolution Audit

- **Total Identified Conflicts**: `80`
- **Policy**: Non-silent conflict tracking. All field discrepancies between different datasets are recorded in `source_provenance['conflicts']` and preserved for auditability.

| Entity | Field | Existing Source & Value | Incoming Source & Value | Resolution |
|:---|:---|:---|:---|:---|
| `Standard:IS 8112:2013` | `status` | `standards.csv=CURRENT` | `sample_standards.json=SUPERSEDED` | Retained CURRENT; recorded sample_standards.json status as alternative |
| `Standard:IS 12269:2013` | `status` | `standards.csv=CURRENT` | `sample_standards.json=SUPERSEDED` | Retained CURRENT; recorded sample_standards.json status as alternative |
| `Standard:IS 13947 (Part 1):1993` | `status` | `standards.csv=CURRENT` | `sample_standards.json=SUPERSEDED` | Retained CURRENT; recorded sample_standards.json status as alternative |
| `ProductLicence:Amplifiers With Input Power 2000w And Above` | `licence_count` | `productlicence.csv (earlier row)=70` | `productlicence.csv (subsequent row)=70` | Updated to latest row count 70 and recorded duplicate in provenance |
| `ProductLicence:Automatic Data Processing Machine` | `licence_count` | `productlicence.csv (earlier row)=2638` | `productlicence.csv (subsequent row)=2638` | Updated to latest row count 2638 and recorded duplicate in provenance |
| `ProductLicence:Electronic Clocks With Mains Power` | `licence_count` | `productlicence.csv (earlier row)=2` | `productlicence.csv (subsequent row)=2` | Updated to latest row count 2 and recorded duplicate in provenance |
| `ProductLicence:Electronic Games (Video)` | `licence_count` | `productlicence.csv (earlier row)=28` | `productlicence.csv (subsequent row)=28` | Updated to latest row count 28 and recorded duplicate in provenance |
| `ProductLicence:Electronic Musical Systems With Input Power 200w And Above` | `licence_count` | `productlicence.csv (earlier row)=244` | `productlicence.csv (subsequent row)=244` | Updated to latest row count 244 and recorded duplicate in provenance |
| `ProductLicence:Laptop/Notebook/Tablet` | `licence_count` | `productlicence.csv (earlier row)=391` | `productlicence.csv (subsequent row)=391` | Updated to latest row count 391 and recorded duplicate in provenance |
| `ProductLicence:Microwave Ovens` | `licence_count` | `productlicence.csv (earlier row)=77` | `productlicence.csv (subsequent row)=77` | Updated to latest row count 77 and recorded duplicate in provenance |

## 4. Compliance Ambiguity Identification

- **Total Ambiguities Flagged**: `97`
- **Key Regulatory Ambiguity**: Standards marked as `'Voluntary'` in `ReportExcel.csv` that also appear under an active Quality Control Order in `schem.csv`.
- **System Recommendation**: When tenders specify these standards, the AI engine flags them with high-priority audit alerts indicating the regulatory divergence.

| Standard Number | Standard Title | Regulatory Divergence Description |
|:---|:---|:---|
| `IS 21` | WROUGHT ALUMINIUM AND ALUMINIUM ALLOYS FOR MA... | Standard IS 21 is classified as 'Voluntary' in ReportExcel.csv, yet appears under an active Quality Control Order in schem.csv. |
| `IS 26` | TIN INGOT - SPECIFICATION (FIFTH REVISION)... | Standard IS 26 is classified as 'Voluntary' in ReportExcel.csv, yet appears under an active Quality Control Order in schem.csv. |
| `IS 27` | PRIMARY LEAD - SPECIFICATION (FIFTH REVISION)... | Standard IS 27 is classified as 'Voluntary' in ReportExcel.csv, yet appears under an active Quality Control Order in schem.csv. |
| `IS 191` | COPPER... | Standard IS 191 is classified as 'Voluntary' in ReportExcel.csv, yet appears under an active Quality Control Order in schem.csv. |
| `IS 209` | REFINED ZINC - SPECIFICATION (FIFTH REVISION)... | Standard IS 209 is classified as 'Voluntary' in ReportExcel.csv, yet appears under an active Quality Control Order in schem.csv. |
| `IS 302 (Part 1)` | HOUSEHOLD AND SIMILAR ELECTRICAL APPLIANCES S... | Standard IS 302 (Part 1) is classified as 'Voluntary' in ReportExcel.csv, yet appears under an active Quality Control Order in schem.csv. |
| `IS 517` | METHANOL (METHYL ALCOHOL)... | Standard IS 517 is classified as 'Voluntary' in ReportExcel.csv, yet appears under an active Quality Control Order in schem.csv. |
| `IS 617` | ALUMINIUM AND ALUMINIUM ALLOYS INGOTS FOR REM... | Standard IS 617 is classified as 'Voluntary' in ReportExcel.csv, yet appears under an active Quality Control Order in schem.csv. |
| `IS 695` | ACETIC ACID... | Standard IS 695 is classified as 'Voluntary' in ReportExcel.csv, yet appears under an active Quality Control Order in schem.csv. |
| `IS 733` | WROUGHT ALUMINIUM AND ALUMINIUM ALLOY BARS, R... | Standard IS 733 is classified as 'Voluntary' in ReportExcel.csv, yet appears under an active Quality Control Order in schem.csv. |

## 5. Unresolved Cross-References

- **Total Unresolved Cross-References**: `9`
- **Status**: Safely preserved as string targets in `StandardRelationship` with `target_standard_id = NULL` to prevent data loss when external standards are cited.

---
*Report generated automatically by PS 26108 Ingestion Pipeline.*