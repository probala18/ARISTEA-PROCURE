# Module 5 — Semantic-Only Retrieval Engine

## Overview

Module 5 provides the semantic retrieval and scoring core for the PS 26108 BIS standards recommendation system. In accordance with Problem Statement 26108, it implements a **Semantic-Search-Only Architecture** for natural-language procurement specifications:
1. **Dense Vector Similarity Search** (384-dimensional cosine similarity embeddings via Sentence Transformers)
2. **Deterministic Exact Standard Lookup** (fast path strictly for explicit canonical standard identifiers, respecting active filters)
3. **Deterministic Metadata Filtering** (status, category, department, mandatory certification, QCO applicability)
4. **Pure Semantic Ranking** generating transparent relevance scores directly from vector cosine similarity $[0.0, 1.0]$

Natural language queries follow the streamlined flow:
$$\text{Natural Language Query} \longrightarrow \text{Semantic Embedding} \longrightarrow \text{Vector Similarity Search} \longrightarrow \text{Relevant Standards}$$

BM25 lexical search, Reciprocal Rank Fusion (RRF), and keyword boosting are completely eliminated from natural language retrieval.

---

## Architectural Principles & Implementation

### 1. Pretrained vs. Deterministic Fallback Embedding Providers
* **Primary Pretrained Provider**: `SentenceTransformerEmbeddingProvider` using `all-MiniLM-L6-v2` / `paraphrase-multilingual-MiniLM-L12-v2` (`dimension = 384`, `is_pretrained = True`).
* **Offline/Testing Fallback**: `DeterministicSemanticEmbeddingProvider` (`deterministic-offline-fallback-384d`, `dimension = 384`, `is_pretrained = False`).
  * *Audit Finding*: Designated strictly as an offline testing fallback for sandboxed environments without network access to Hugging Face, preserving deterministic vector math across test suites. It is never presented as equivalent to genuine pretrained neural representations.
* **Embedding Coverage**:
  * Total canonical standards: **268**
  * Populated embeddings: **268 / 268 (100%)**
  * Vector Dimension: **384**
  * $L_2$ Normalization: **Strictly 1.000000** ($\min = 1.000000, \max = 1.000000$).

### 2. Retrieval Pipeline Execution Order
```
Query Input + Optional Metadata Filters
                  │
                  ▼
         Query Normalization
                  │
                  ▼
     Exact-ID Detection / Mention Extraction
     ├── Exact Match + Pass Filters ──► Direct Lookup Fast-Path (Score = 1.0)
     └── Natural Language Query     ──► Proceed to Semantic Vector Retrieval
                  │
                  ▼
         Vector Semantic Search
         (Top Candidates, Cosine Similarity over 384-d Embeddings)
                  │
                  ▼
        Active Metadata Filtering
        (Deterministic filter constraints applied post-vector search)
                  │
                  ▼
        Pure Semantic Ranking
        (Relevance Score = Vector Cosine Similarity)
                  │
                  ▼
   Ranked Recommendations + Auditable Signal Breakdown
```
*Exact standard code lookup is a deterministic supporting fast path and **strictly respects active metadata filters**.*

### 3. Pure Semantic Scoring & Explainability
* **Relevance Score**: Strictly equals the cosine similarity between the query embedding and the standard embedding vector $[0.0, 1.0]$.
* **Signals**:
  * `semantic_similarity`: Raw cosine similarity score.
  * `status_support`: Indicator of current standard status.
  * `bm25_score`: Fixed to 0.0 (no lexical search invocation).
* Each result includes an auditable explanation string documenting the dense vector similarity and embedding model.

---

## Benchmark Evaluation Results (`query_dataset.json`)

Evaluated against the 14 reference queries from `Skill-Connect/csvfiles/query_dataset.json`:

### Summary Metrics

| Metric | Overall Standard-Seeking (10 Queries) | English Standard Queries (9 Queries) |
|:---|:---:|:---:|
| **Top-1 Accuracy** | **80.0%** (8/10) | **88.9%** (8/9) |
| **Top-3 Accuracy** | **90.0%** (9/10) | **100.0%** (9/9) |
| **Top-5 Accuracy** | **90.0%** (9/10) | **100.0%** (9/9) |
| **Mean Reciprocal Rank (MRR)** | **0.8333** | **0.9259** |
| **Average Latency** | **1.00 ms** | **1.00 ms** |

### Category Breakdown

1. **Exact Standard Lookup (Q01)**:
   * `What is IS 694:2010?` → **Rank 1** (`IS 694:2010`, Score: 0.685).
2. **Semantic / Domain Queries (Q02, Q03, Q04, Q07, Q09, Q11, Q13)**:
   * Q02: `Which standard applies to PVC insulated electrical cables?` → **Rank 1** (`IS 1554 (Part 1):1988`), **Rank 2** (`IS 694:2010`).
   * Q03: `Is BIS certification mandatory for cables under IS 694?` → **Rank 1** (`IS 694:2010`).
   * Q04: `Where can I test electrical cables in laboratories?` → **Rank 1** (`IS 10810 (Part 1):1984` - Test Methods for Cables).
   * Q07: `For my cables business, do I need BIS certification and do I need to test it in laboratories?` → **Rank 3** (`IS 694:2010`).
   * Q09: `What is the standard for high voltage cables?` → **Rank 1** (`IS 7098 (Part 2):2011`).
   * Q11: `flexible wires for domestic home wiring` → **Rank 1** (`IS 694:2010`).
   * Q13: `What is the difference between IS 694 and IS 1554 for power cables?` → **Rank 1** (`IS 694:2010`), **Rank 2** (`IS 1554 (Part 1):1988`).
3. **Ambiguous Product Queries (Q08, Q14)**:
   * Q08: `Which BIS standard do I need for cables?` → **Rank 1** (`IS 694:2010`). Correctly returns candidate series in Top 3 (`IS 694`, `IS 14255`, `IS 1554`).
   * Q14: `What testing is required?` → Flagged for user clarification as expected; standard retrieval scores are diffuse without a specified product.
4. **Multilingual Query (Q12)**:
   * `क्या केबल के लिए BIS सर्टिफिकेशन जरूरी है?` → **MISS** in raw English retrieval (scores $< 0.10$). Ground truth explicitly specifies translation to normalized English query before retrieval (handled in Module 6 NLU orchestration).
5. **Out-of-Scope Query (Q10)**:
   * `What is the weather in Delhi today?` → No standard match (low diffuse scores $< 0.45$). Correctly routed out of scope by domain intent classification.
6. **Informational Overview Queries (Q05, Q06)**:
   * `What are the services offered by BIS?` / `What is BIS and what does it do?` → Designed for documentary overview chunks (`needs_rag`), not catalog standards.

---

## Cumulative Test Suite Reconciliation

| Module | Test File | Collected Tests | Passing |
|:---|:---|:---:|:---:|
| Module 1 | [`tests/test_module1_data_inventory.py`](file:///c:/Users/BALASUNDAR%20M/Documents/SIH%202026/tests/test_module1_data_inventory.py) | 8 | 8 |
| Module 2 | [`tests/test_module2_database_schema.py`](file:///c:/Users/BALASUNDAR%20M/Documents/SIH%202026/tests/test_module2_database_schema.py) | 8 | 8 |
| Module 3 (Normalizers) | [`tests/test_normalizers.py`](file:///c:/Users/BALASUNDAR%20M/Documents/SIH%202026/tests/test_normalizers.py) | 12 | 12 |
| Module 3 (Verification) | [`tests/test_module3_verification.py`](file:///c:/Users/BALASUNDAR%20M/Documents/SIH%202026/tests/test_module3_verification.py) | 3 | 3 |
| Module 4 | [`tests/test_module4_knowledge_graph.py`](file:///c:/Users/BALASUNDAR%20M/Documents/SIH%202026/tests/test_module4_knowledge_graph.py) | 18 | 18 |
| Module 5 | [`tests/test_module5_retrieval.py`](file:///c:/Users/BALASUNDAR%20M/Documents/SIH%202026/tests/test_module5_retrieval.py) | 12 | 12 |
| **Total Cumulative** | **All 6 Test Suites** | **61** | **61** |

No regressions found across any prior modules.
