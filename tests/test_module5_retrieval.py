"""
Module 5 Test Suite — Semantic & Hybrid Retrieval Engine.
Covers:
1. Embedding Provider:
   - 384-dimensional vector output & L2 unit normalization
   - Pretrained vs deterministic fallback distinction
   - Standard embedding text construction
2. Lexical Retrieval (BM25Okapi):
   - Keyword search across titles, scopes, categories, keywords
   - Standard number token matching
3. Vector Retrieval:
   - Cosine similarity ranking in 384-dim space
   - Semantic similarity on natural language queries
4. Hybrid Retrieval & Reciprocal Rank Fusion (RRF):
   - Fast-path exact match supporting check
   - Fast-path MUST strictly respect active metadata filters
   - Candidate merge via RRF
   - Metadata filtering (status, category, mandatory cert, QCO)
5. Multi-Signal Reranker:
   - Transparent relevance score calculation (0.0 to 1.0)
   - Explainable breakdown of signals
6. Benchmark Query Retrieval:
   - Evaluation on representative queries from query_dataset.json
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import numpy as np
from sqlalchemy.orm import sessionmaker

from backend.app.core.database import get_engine
from backend.app.models.standard import Standard
from backend.app.services.retrieval import (
    BaseEmbeddingProvider,
    DeterministicSemanticEmbeddingProvider,
    SentenceTransformerEmbeddingProvider,
    EmbeddingTextBuilder,
    get_embedding_provider,
    BM25Index,
    VectorRetriever,
    MultiSignalReranker,
    RerankingWeights,
    ScoredRecommendation,
    HybridRetrievalEngine,
    RetrievalFilter,
    HybridRetrievalResponse,
)


@pytest.fixture(scope="module")
def db_session():
    engine = get_engine("sqlite:///./sih_bis.db")
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture(scope="module")
def hybrid_engine(db_session):
    return HybridRetrievalEngine(db_session)


# ============================================================
# 1. EMBEDDING PROVIDER & VECTOR DIMENSION TESTS
# ============================================================

def test_embedding_provider_dimension_and_normalization():
    """Embedding vectors must strictly be 384-dimensional and unit-normalized (L2 norm = 1.0)."""
    provider = DeterministicSemanticEmbeddingProvider()
    assert provider.dimension == 384
    assert provider.is_pretrained is False

    vec = provider.embed_query("domestic electrical wires and PVC cables")
    assert len(vec) == 384
    norm = np.linalg.norm(vec)
    assert abs(norm - 1.0) < 1e-4


def test_pretrained_vs_fallback_distinction():
    """
    Architectural Rule:
    Pretrained provider is the primary semantic retrieval mechanism.
    Deterministic provider is only an offline/testing fallback and
    must never be presented as equivalent to pretrained semantic embeddings.
    """
    fallback = DeterministicSemanticEmbeddingProvider()
    assert fallback.is_pretrained is False
    assert "fallback" in fallback.model_name.lower() or "offline" in fallback.model_name.lower()

    # Base class enforces abstract property is_pretrained
    assert hasattr(BaseEmbeddingProvider, "is_pretrained")


def test_embedding_text_builder(db_session):
    """Embedding text aggregates standard_id, title, scope, category, keywords without fabricated data."""
    cable_std = db_session.query(Standard).filter(Standard.standard_id.like("%694%")).first()
    assert cable_std is not None

    text = EmbeddingTextBuilder.build_standard_embedding_text(cable_std)
    assert "IS 694" in text
    assert cable_std.title in text
    if cable_std.category:
        assert cable_std.category in text


# ============================================================
# 2. LEXICAL RETRIEVAL (BM25) TESTS
# ============================================================

def test_bm25_keyword_retrieval(db_session):
    """BM25 successfully retrieves standards for domain product keywords."""
    stds = db_session.query(Standard).all()
    bm25 = BM25Index()
    bm25.build_index(stds)

    results = bm25.search("slotted countersunk head screws", top_k=5)
    assert len(results) > 0
    top_hit = results[0]
    assert "screw" in top_hit["title"].lower() or "1364" in top_hit["standard_id"] or "1363" in top_hit["standard_id"]


def test_bm25_exact_is_token_matching(db_session):
    """BM25 matches specific standard number tokens."""
    stds = db_session.query(Standard).all()
    bm25 = BM25Index()
    bm25.build_index(stds)

    results = bm25.search("IS 1293", top_k=5)
    assert len(results) > 0
    matched_ids = [r["standard_id"] for r in results]
    assert any("IS 1293" in sid for sid in matched_ids)


# ============================================================
# 3. VECTOR SEMANTIC RETRIEVAL TESTS
# ============================================================

def test_vector_semantic_search(db_session):
    """Vector retriever computes cosine similarities and returns ranked standards."""
    vr = VectorRetriever(db_session)
    results = vr.search("flexible wires for domestic home wiring", top_k=5)
    assert len(results) > 0
    # Top results should include cable standards (e.g. IS 694)
    top_std_ids = [r["standard_id"] for r in results]
    assert any("694" in sid or "732" in sid or "1554" in sid for sid in top_std_ids)
    assert results[0]["vector_similarity"] > 0.0


# ============================================================
# 4. HYBRID RETRIEVAL & FAST PATH RESPECTING FILTERS
# ============================================================

def test_exact_lookup_fast_path(hybrid_engine):
    """Exact standard number queries use fast path when no conflicting filters apply."""
    resp = hybrid_engine.retrieve("IS 694:2010")
    assert resp.is_exact_match_fast_path is True
    assert len(resp.recommendations) == 1
    assert resp.recommendations[0].standard_id == "IS 694:2010"
    assert resp.recommendations[0].relevance_score == 1.0


def test_exact_lookup_must_respect_active_filters(hybrid_engine):
    """
    CRITICAL RULE:
    Exact lookup is a supporting fast path, NOT the primary recommendation mechanism.
    Exact lookup must STILL RESPECT active metadata filters.
    If a filter excludes the exact match (e.g. category mismatch), fast-path must NOT falsely return it.
    """
    # IS 694 is Electrical/Cables, NOT Civil
    filter_civil = RetrievalFilter(category="Civil Engineering")
    resp = hybrid_engine.retrieve("IS 694:2010", filters=filter_civil)

    # Fast path must be bypassable when filters do not match
    if resp.recommendations:
        for r in resp.recommendations:
            assert r.category is not None
            assert "Civil" in r.category


def test_hybrid_retrieval_reciprocal_rank_fusion(hybrid_engine):
    """Natural language query blends vector and BM25 using RRF and reranker."""
    resp = hybrid_engine.retrieve("PVC insulated cables for power transmission", top_k=5)
    assert len(resp.recommendations) > 0
    top = resp.recommendations[0]
    assert top.relevance_score > 0.0
    assert "semantic_similarity" in top.signals
    assert "bm25_score" in top.signals


def test_hybrid_retrieval_status_filtering(hybrid_engine):
    """Retrieval filter excludes non-matching statuses."""
    filters = RetrievalFilter(status="CURRENT")
    resp = hybrid_engine.retrieve("cement", filters=filters, top_k=10)
    for r in resp.recommendations:
        assert r.status == "CURRENT"


# ============================================================
# 5. MULTI-SIGNAL RERANKER TESTS
# ============================================================

def test_multi_signal_reranker_scoring():
    """Reranker calculates transparent, bounded relevance scores (0.0 to 1.0)."""
    reranker = MultiSignalReranker()
    candidates = [
        {
            "id": 1,
            "standard_id": "IS 694:2010",
            "is_number": "IS 694",
            "title": "PVC Insulated Cables",
            "category": "Electrotechnical",
            "status": "CURRENT",
            "vector_similarity": 0.85,
            "bm25_score": 0.90,
        },
        {
            "id": 2,
            "standard_id": "IS 269:2015",
            "is_number": "IS 269",
            "title": "Ordinary Portland Cement",
            "category": "Civil",
            "status": "CURRENT",
            "vector_similarity": 0.20,
            "bm25_score": 0.10,
        }
    ]

    ranked = reranker.rerank("pvc insulated cables", candidates, top_k=2)
    assert len(ranked) == 2
    assert ranked[0].standard_id == "IS 694:2010"
    assert ranked[0].relevance_score > ranked[1].relevance_score
    assert 0.0 <= ranked[0].relevance_score <= 1.0
    assert "Semantic:" in ranked[0].explanation


# ============================================================
# 6. BENCHMARK QUERY EVALUATION TESTS
# ============================================================

def test_benchmark_queries_accuracy(hybrid_engine):
    """Evaluates core benchmark queries from query_dataset.json."""
    # Query 1: Direct standard lookup
    r1 = hybrid_engine.retrieve("What is IS 694:2010?", top_k=3)
    assert any("694" in r.standard_id for r in r1.recommendations)

    # Query 2: Product to standard lookup
    r2 = hybrid_engine.retrieve("Which standard applies to PVC insulated electrical cables?", top_k=3)
    assert any("694" in r.standard_id or "1554" in r.standard_id for r in r2.recommendations)

    # Query 11: Alternative wording
    r11 = hybrid_engine.retrieve("flexible wires for domestic home wiring", top_k=3)
    assert any("694" in r.standard_id or "732" in r.standard_id for r in r11.recommendations)
