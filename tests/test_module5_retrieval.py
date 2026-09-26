"""
Module 5 Test Suite — Semantic Vector Retrieval Engine (PS 26108).
Covers:
1. Embedding Provider:
   - 384-dimensional vector output & L2 unit normalization
   - Pretrained vs deterministic fallback distinction
   - Standard embedding text construction
2. Semantic Vector Retrieval:
   - Cosine similarity ranking in 384-dim dense space
   - Semantic understanding on natural language procurement queries
   - Alternative wording with similar meaning retrieves conceptually relevant standards
3. Deterministic Exact Standard Lookup:
   - Fast-path check for exact standard identifier
   - Fast-path MUST strictly respect active metadata filters
4. Metadata Filtering:
   - Deterministic status and category filtering without lexical weighting
5. Semantic-Only Architecture Discipline:
   - Absence of BM25, RRF, or lexical scoring in recommendation signals
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
    VectorRetriever,
    SemanticRetrievalEngine,
    RetrievalFilter,
    SemanticRetrievalResponse,
    ScoredRecommendation,
)


@pytest.fixture(scope="module")
def db_session():
    engine = get_engine("sqlite:///./sih_bis.db")
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture(scope="module")
def semantic_engine(db_session):
    return SemanticRetrievalEngine(db_session)


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
# 2. SEMANTIC VECTOR RETRIEVAL TESTS
# ============================================================

def test_vector_semantic_search(db_session):
    """Vector retriever computes cosine similarities and returns ranked standards."""
    vr = VectorRetriever(db_session)
    results = vr.search("flexible wires for domestic home wiring", top_k=10)
    assert len(results) > 0
    # Top results should include cable/wire standards (IS 694, IS 732, IS 1554, or IS 8130)
    top_std_ids = [r["standard_id"] for r in results]
    assert any("694" in sid or "732" in sid or "1554" in sid or "8130" in sid for sid in top_std_ids)
    assert results[0]["vector_similarity"] > 0.0


def test_semantic_retrieval_alternative_wording(semantic_engine):
    """
    Core Semantic Property:
    Semantically equivalent natural language wording retrieves the relevant standard
    even when the exact keywords differ from the standard title.
    """
    resp = semantic_engine.retrieve("copper conductors for domestic electricity distribution", top_k=5)
    assert len(resp.recommendations) > 0
    top_ids = [r.standard_id for r in resp.recommendations]
    assert any("694" in sid or "1554" in sid or "8130" in sid for sid in top_ids)
    assert resp.recommendations[0].relevance_score > 0.0


def test_semantic_retrieval_pure_vector_ranking(semantic_engine):
    """
    Verifies that relevance score strictly equals vector cosine similarity.
    No BM25, RRF, or lexical boost is applied.
    """
    resp = semantic_engine.retrieve("PVC insulated cables for power transmission", top_k=5)
    assert len(resp.recommendations) > 0
    for r in resp.recommendations:
        assert 0.0 <= r.relevance_score <= 1.0
        # Signals must reflect pure semantic similarity
        assert "semantic_similarity" in r.signals
        assert "bm25_score" not in r.signals
        assert "rrf_score" not in r.signals
        assert r.signals["semantic_similarity"] == r.relevance_score


def test_semantic_retrieval_does_not_invoke_bm25_or_rrf(semantic_engine):
    """
    Architectural Discipline:
    Natural-language recommendation flow must no longer call BM25 or RRF for relevance ranking.
    """
    resp = semantic_engine.retrieve("energy efficient three phase induction motors", top_k=5)
    assert len(resp.recommendations) > 0
    top = resp.recommendations[0]
    assert "12615" in top.standard_id or "motor" in top.title.lower()
    # Ensure explanation documents dense vector similarity, not hybrid or BM25
    assert "semantic" in top.explanation.lower() or "dense" in top.explanation.lower()
    assert "bm25" not in top.explanation.lower()
    assert "rrf" not in top.explanation.lower()


# ============================================================
# 3. DETERMINISTIC EXACT LOOKUP TESTS
# ============================================================

def test_exact_lookup_deterministic_direct_path(semantic_engine):
    """Exact standard number queries use deterministic direct lookup when no conflicting filters apply."""
    resp = semantic_engine.retrieve("IS 694:2010")
    assert resp.is_exact_match_fast_path is True
    assert len(resp.recommendations) == 1
    assert resp.recommendations[0].standard_id == "IS 694:2010"
    assert resp.recommendations[0].relevance_score == 1.0
    assert "exact" in resp.recommendations[0].explanation.lower()


def test_exact_lookup_must_respect_active_filters(semantic_engine):
    """
    CRITICAL RULE:
    Exact lookup is a supporting fast path, NOT the primary recommendation mechanism.
    Exact lookup must STILL RESPECT active metadata filters.
    If a filter excludes the exact match (e.g. category mismatch), fast-path must NOT falsely return it.
    """
    # IS 694 is Electrical/Cables, NOT Civil
    filter_civil = RetrievalFilter(category="Civil Engineering")
    resp = semantic_engine.retrieve("IS 694:2010", filters=filter_civil)

    # Fast path must be bypassable when filters do not match
    if resp.recommendations:
        for r in resp.recommendations:
            assert r.category is not None
            assert "Civil" in r.category


# ============================================================
# 4. METADATA FILTERING TESTS
# ============================================================

def test_semantic_retrieval_status_filtering(semantic_engine):
    """Retrieval filter excludes non-matching statuses deterministically."""
    filters = RetrievalFilter(status="CURRENT")
    resp = semantic_engine.retrieve("cement", filters=filters, top_k=10)
    for r in resp.recommendations:
        assert r.status == "CURRENT"


# ============================================================
# 5. BENCHMARK QUERY EVALUATION TESTS
# ============================================================

def test_benchmark_queries_semantic_accuracy(semantic_engine):
    """Evaluates core benchmark queries from query_dataset.json using pure semantic retrieval."""
    # Query 1: Direct standard lookup
    r1 = semantic_engine.retrieve("What is IS 694:2010?", top_k=3)
    assert any("694" in r.standard_id for r in r1.recommendations)

    # Query 2: Product to standard lookup
    r2 = semantic_engine.retrieve("Which standard applies to PVC insulated electrical cables?", top_k=3)
    assert any("694" in r.standard_id or "1554" in r.standard_id for r in r2.recommendations)

    # Query 11: Alternative wording
    r11 = semantic_engine.retrieve("flexible wires for domestic home wiring", top_k=10)
    assert any("694" in r.standard_id or "732" in r.standard_id or "8130" in r.standard_id for r in r11.recommendations)
