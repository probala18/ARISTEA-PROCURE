# Module 4 — Knowledge Graph & Relationship Engine Documentation

## 1. Overview & Architecture

The **Knowledge Graph & Relationship Engine** is the structured relationship intelligence layer of the PS 26108 BIS compliance and procurement intelligence system. It translates tabular database records and relationship edges into a typed, directed, and explainable multi-entity knowledge graph.

### Architectural Positioning

```
User Tender / Query
        ↓
NLP / Requirement Extraction (Module 5)
        ↓
Semantic & Hybrid Retrieval (Module 6)
        ↓
Recommendation Engine (Module 7)
        ↓
Knowledge Graph & Relationship Engine (Module 4)  <--- THIS MODULE
        ↓
Compliance & Verification Intelligence (Module 8)
        ↓
Audit, Explanations & Generation (Modules 9–11)
```

The Knowledge Graph provides **structured, ground-truth evidence** to downstream recommendation, audit, and generation engines without performing speculative or ungrounded inferences.

---

## 2. Graph Entities & Node Types

The graph models 9 distinct node types grounded in the ingested datasets:

| Node Type | Source Table | Description |
| :--- | :--- | :--- |
| `STANDARD` | `standards` | Canonical Indian Standards (268 nodes) |
| `STANDARD_VERSION` | `standard_versions` | Version history and amendments (275 nodes) |
| `CERTIFICATION_RECORD` | `certification_records` | Certification facts from ISI/CRS lists (1,573 nodes) |
| `QCO_RECORD` | `qco_records` | Quality Control Orders and Gazette notifications (710 nodes) |
| `PRODUCT_CATEGORY` | `product_licences` | Operative licence counts per category (75 nodes) |
| `MINISTRY_PRODUCT_MAPPING` | `ministry_product_mappings` | Buyer/ministry standard mappings (28 nodes) |
| `PROCUREMENT_CONCEPT` | `procurement_ontology` | Domain procurement keywords & aliases |
| `SOURCE_DOCUMENT` | `source_documents` | Audit provenance anchors (10 nodes) |
| `UNRESOLVED_STANDARD_REFERENCE` | `standard_relationships` | Preserved citations where target is uncataloged or a multi-part series |

---

## 3. Relationship Types & Provenance Separation

The graph supports 16 typed directed relationships with mandatory segregation of **EXPLICIT** vs. **DERIVED** status:

### Technical & Domain Relationships:
- `NORMATIVE_REFERENCE`: Direct citations extracted from `sample_standards.json` (Derived)
- `TESTING`: Test method standards cited in `relationships.json` (Explicit)
- `SAFETY`: Safety requirements cited in `relationships.json` (Explicit)
- `PERFORMANCE`: Efficiency & performance standards in `relationships.json` (Explicit)
- `RELATED_PRODUCT`: Allied product dependencies in `relationships.json` (Explicit)
- `TERMINOLOGY`: Vocabulary & definitions in `relationships.json` (Explicit)
- `INSTALLATION`: Installation & code of practice standards in `relationships.json` (Explicit)
- `SEISMIC_SAFETY`: Earthquake detailing requirements in `relationships.json` (Explicit)
- `FOOD_CONTACT_SAFETY`: Food-grade plastics/materials in `relationships.json` (Explicit)
- `SUPERSEDES`: Forward supersession from `standards.csv` / `relationships.json` (Explicit / Derived)
- `SUPERSEDED_BY`: Programmatically generated reverse edge for supersession chains (Derived)

### Compliance & Hierarchy Relationships:
- `CERTIFICATION_SCHEME`: Standard to BIS ISI / CRS Scheme
- `QCO_REFERENCE`: Standard to Quality Control Order mandate
- `PRODUCT_MAPPING`: Product category to governing standard
- `VERSION_OF`: Amendment to canonical base standard
- `SOURCE_OF`: Raw file row to canonical entity

Every edge maintains full provenance:
- `source_dataset` (`relationships.json`, `sample_standards.json`, `standards.csv`)
- `is_explicit_source` (boolean)
- `source_provenance` (verbatim row JSON)

---

## 4. Multi-Part & Series-Aware Resolution Rules

The `StandardReferenceResolver` categorizes all standard identifier queries into 4 mutually exclusive match types:

1. **`EXACT`**: Direct canonical identifier match (e.g., `IS 694:2010`).
2. **`PART`**: Unambiguous part-level match (e.g., `IS 1554 (Part 1)`).
3. **`SERIES_AMBIGUOUS`**:
   - When a base series standard is cited without part (e.g., `IS 2386` for concrete aggregate testing, `IS 1367` for fastener conditions, or `IS 4031` for cement testing), and the database contains multiple specific parts (e.g. `IS 2386 (Part 1):1963` and `IS 2386 (Part 4):1963`).
   - **Critical Rule**: The engine preserves this ambiguity and **never** collapses `IS 2386` to an arbitrary single part.
4. **`UNRESOLVED`**:
   - Standards that genuinely do not exist in the supplied catalog (e.g., `IS 1599`, `IS 1608 (Part 1)`, `IS 13920`, `IS 4032`, `IS 12235 (Part 1)`).
   - Preserved verbatim as string targets without fabricating external data.

---

## 5. Traversal & Cycle Prevention

The `GraphTraversalService` implements:
- **Depth Limiting**: Default traversal depth is 3; absolute maximum depth is clamped to 5.
- **Cycle Prevention**: Branch-level visited set (`path_visited`) prevents circular infinite loops when bidirectional relationships or circular supersession entries are encountered.
- **Typed Traversal**: Filter by `relationship_types` (e.g., retrieve only `TESTING` or `SAFETY` standards).
- **Shortest Path Finding**: Computes shortest explainable connection between any two standard nodes.

---

## 6. Supersession Chain Engine

The `SupersessionChainService` navigates standard lifecycles:
- **Backward Chain (`SUPERSEDES`)**: Current standard → Older revision → Historical standard.
- **Historical Unresolved Records**: For standards like `IS 1180 (Part 1):2014` that supersede `IS 1180:1989`, the 1989 version is safely represented as an uncataloged historical string target (`resolved: false`) rather than creating an invalid self-referential circular loop.
- **Forward Chain (`SUPERSEDED_BY`)**: Discovers modern replacement standards for withdrawn or superseded specifications.

---

## 7. Compliance Connector & Regulatory Divergence

The `ComplianceConnectorService` provides grounded connections to regulatory data:
- **Certification Records**: Links standard to active ISI and CRS records.
- **QCO Mandates**: Links standard to mandatory Quality Control Orders, notification numbers, and enforcing ministries.
- **Regulatory Divergence Audit**: Detects cases where a standard is listed as `VOLUNTARY` in certification lists (`ReportExcel.csv`) but is legally mandated under an active QCO order (`schem.csv`). Flags these divergences for tender compliance checks.

---

## 8. Path Explanations

The `PathExplainer` renders transparent, audit-ready explanations of graph traversals:

```json
{
  "start_node": "std:4",
  "end_node": "unresolved:IS 2386",
  "total_depth": 1,
  "narrative": "Path from std:4 to unresolved:IS 2386 (Depth 1): -> [NORMATIVE_REFERENCE]-> unresolved:IS 2386",
  "steps": [
    {
      "step_depth": 1,
      "source": "std:4",
      "relationship": "NORMATIVE_REFERENCE",
      "target": "unresolved:IS 2386",
      "edge_nature": "DERIVED (synthesized from normative_references/supersedes)",
      "source_dataset": "sample_standards.json",
      "resolution": "SERIES_AMBIGUOUS",
      "resolution_note": " [AMBIGUOUS SERIES: base standard cites multiple parts]",
      "provenance": {"normative_reference": "IS 2386"}
    }
  ]
}
```

---

## 9. Verification & Test Metrics

- **Dedicated Module 4 Tests**: 18 tests in [`tests/test_module4_knowledge_graph.py`](file:///c:/Users/BALASUNDAR%20M/Documents/SIH%202026/tests/test_module4_knowledge_graph.py)
- **Cumulative Test Suite**: **49/49 tests passing (100%)** across Modules 1–4.
- **Ingestion Audit**: `scripts/validate_ingestion.py` passed with 0 errors.
