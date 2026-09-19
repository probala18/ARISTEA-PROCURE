# Module 13 - Evidence-Grounded Specification Generator

## 1. Overview

Module 13 implements the **Specification Generator** for Problem Statement 26108
(*Identifying Applicable Indian Standards for Procurement Specifications*).

The module converts analyzed tender requirements and verified project records into
procurement-ready technical specifications, tender clauses, compliance
checklists, and audit corrections. It is an evidence-first synthesis layer: it
does not create new BIS facts, legal mandates, technical limits, or standard
numbers.

The generator consumes the outputs of the existing modules:

```
Tender Document and Extracted Requirements (Module 11)
                         |
                         v
Evidence-Based Tender Audit (Module 12)
                         |
       +-----------------+------------------+
       |                 |                  |
       v                 v                  v
Recommendation      Relationships       Version / Compliance
Engine (Module 6)   (Module 7)          (Modules 8 and 9)
       \                 |                  /
        +----------------+-----------------+
                         |
                         v
              Module 13 Specification Generator
                         |
                         v
       Generated specification + structured content
       + provenance + editable persisted version
```

## 2. Design Rules

Module 13 follows these rules for every generation path:

1. **Verified data only**: output is grounded in canonical standards, version
   intelligence, compliance records, relationship data, and analyzed tender
   context.
2. **No hallucinated requirements**: the generator never invents IS numbers,
   technical tolerances, test limits, certification requirements, or statutory
   mandates.
3. **Explicit uncertainty**: when the available evidence cannot establish a
   value or requirement, output uses `UNKNOWN` and
   `Insufficient verified evidence`.
4. **Provenance preservation**: generated requirement items retain evidence
   records such as tender clauses, source datasets, QCO order identifiers,
   relationship records, and recommendation evidence.
5. **Origin separation**: every generated requirement is categorized as one of:
   - `TENDER_DERIVED`
   - `RECOMMENDED_STANDARD`
   - `COMPLIANCE_REQUIREMENT`
   - `CONDITIONAL_RECOMMENDATION`
6. **Internal labels remain internal**: `PRIMARY` identifies an internal
   recommendation role only; it is not an official BIS classification.
7. **Confidence is not legal certainty**: `confidence_score` is an internal
   decision-support metric and is not a probability, legal determination, or
   claimed correctness percentage.
8. **Original evidence is immutable during editing**: regeneration and edits
   update only the generated specification record.

## 3. Components and Responsibilities

### 3.1 `SpecificationGenerator`

Location: `backend/app/services/specification_generator/generator.py`

The core engine initializes and reuses:

- `RecommendationEngine`
- `RelationshipEngine`
- `VersionIntelligenceService`
- `ComplianceIntelligenceService`
- `TenderGapAnalyzer`

The dispatcher supports the following `SpecificationType` values:

| Type | Purpose |
|---|---|
| `technical_specification` | Full scope, standards, parameters, testing, safety, and compliance specification |
| `tender_clause` | Formal standards and certification clauses suitable for a tender |
| `compliance_checklist` | Structured verification items for procurement evaluation |
| `audit_correction` | Corrective clauses for gaps found by the tender audit |
| `corrective_clause` | Alias path for tender-clause generation |

### 3.2 Generated Requirement Items

`GeneratedRequirementItem` carries:

- requirement origin and clause text;
- standard identifiers and title when resolved;
- internal role and disclaimers;
- regulatory status and mandatory flag;
- confidence score and its disclaimer;
- trust level (`KNOWN`, `INFERRED`, or `UNKNOWN`);
- evidence and provenance records;
- verification notes.

Tender-derived technical attributes are marked `KNOWN`. Recommendations and
relationship-derived items are marked `INFERRED`. Unestablished information is
represented as `UNKNOWN` rather than guessed.

### 3.3 Persistence and Versioning

Location: `backend/app/services/specification_generator/service.py`

`SpecificationService`:

- validates an optional tender reference;
- invokes the generator;
- stores generated text, structured content, and grounding evidence;
- retrieves one specification or lists specifications for a tender;
- updates title, generated text, or structured content;
- increments `version` and sets `is_edited` on edits;
- leaves tender documents, extracted requirements, standard references, and audit
  records untouched.

Generated records are stored in `generated_specifications` through the
`GeneratedSpecification` model. Module 13 uses the existing database model
with fields for:

- `analysis_id`
- `spec_type`
- `title`
- `content`
- `structured_content`
- `grounding_evidence`
- `is_edited`
- `version`

## 4. Evidence and Supersession Behavior

### 4.1 Tender Context

For a tender-backed generation, Module 13 reads the tender requirements and
passes the tender through `TenderGapAnalyzer`. The audit result supplies:

- present standards;
- expected and missing standards;
- outdated or superseded references;
- testing and safety gaps;
- certification gaps;
- QCO evidence and coverage context.

The original tender wording remains available as evidence. It is not replaced in
the tender tables when a generated specification corrects a reference.

### 4.2 Superseded Standards

When Version Intelligence and the knowledge graph establish a successor, the
generated specification recommends the successor and explicitly identifies the
legacy reference it replaces. For example, a verified `IS 325` supersession
can produce a correction to `IS 12615:2018`.

An unresolved or unlisted standard remains an evidence-bearing tender reference.
It is not silently converted into a fabricated canonical standard.

### 4.3 Compliance and QCO Requirements

Compliance clauses are created only when the compliance service establishes
applicable evidence. A generated clause retains the relevant QCO order number
when available. If the records do not establish a mandate, the output does not
state that certification is mandatory.

## 5. Output Types

### 5.1 Technical Specification

The generated document contains:

1. scope of procurement;
2. applicable Indian Standards;
3. technical parameters and trust levels;
4. testing and acceptance criteria;
5. safety and environmental requirements;
6. mandatory statutory and BIS certification clauses;
7. a grounding disclaimer.

Technical parameters are copied from extracted tender attributes where present.
If no verified parameter is available, the specification uses an explicit
`UNKNOWN` entry and explains that verified evidence is insufficient.

### 5.2 Tender and Corrective Clauses

The clause generator can include:

- supersession replacement language;
- missing-standard stipulations;
- QCO/BIS certification language where the audit provides evidence;
- an `UNKNOWN` fallback when no verified standard can be formulated.

The structured result records incorporated standards and the evidence behind
each clause.

### 5.3 Compliance Checklist

The checklist provides:

- Indian Standard and title;
- role and origin;
- regulatory status;
- mandatory certification flag;
- QCO number where available;
- verification method;
- action required;
- evidence records.

Testing relationships with a missing title are represented safely using the
known standard identifier as a fallback title; a null title is never allowed
to invalidate the structured checklist.

### 5.4 Audit Correction

Audit correction output presents each finding with:

- gap type;
- identified issue;
- original clause;
- corrected clause;
- trust level;
- evidence.

## 6. API Surface

The Module 13 router is registered under the existing `/api` prefix.

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/specifications/generate` | Generate from tender, analysis session, or query |
| `GET` | `/api/specifications/{id}` | Retrieve a generated specification |
| `PUT` | `/api/specifications/{id}` | Edit a generated specification and increment its version |
| `DELETE` | `/api/specifications/{id}` | Delete a generated specification |
| `POST` | `/api/analysis/{analysis_id}/generate` | Section 69 analysis-session generation |
| `POST` | `/api/tenders/{id}/generate` | Generate directly from a tender |
| `GET` | `/api/tenders/{id}/specifications` | List generated specifications for a tender |

The health response identifies Module 13 as:

`Module 13 - Specification Generator`

## 7. Verification

The following validation was run after the Module 13 implementation:

| Validation | Result |
|---|---:|
| Module 13 tests | **13 passed, 0 failed** |
| Full cumulative regression | **177 passed, 0 failed** |
| Canonical standards count | **268** |
| Core provenance coverage | **100%** |
| Dataset ingestion validation | **All checks passed** |

The ingestion audit also verified that explicit and derived knowledge-graph
relationships remain separated and that unlinked references are preserved
without data loss.

## 8. Files

- `backend/app/services/specification_generator/generator.py`
- `backend/app/services/specification_generator/service.py`
- `backend/app/services/specification_generator/schemas.py`
- `backend/app/services/specification_generator/__init__.py`
- `backend/app/api/specifications.py`
- `backend/app/api/tenders.py`
- `backend/app/models/analysis.py`
- `backend/app/models/tender.py`
- `backend/app/main.py`
- `tests/test_module13_specification_generator.py`

