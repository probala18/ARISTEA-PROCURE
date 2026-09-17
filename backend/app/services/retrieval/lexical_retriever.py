"""
Lexical Retriever implementing BM25Okapi for Module 5.
Indexes:
- is_number & standard_id
- title
- scope & description
- category & subject area
- keywords
Optimized for technical standard terminology, code numbers, and specifications.
"""
from typing import List, Dict, Any, Tuple
import math
import re
from collections import Counter


class BM25Index:
    """Pure-Python BM25Okapi inverted index over Indian Standards."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = 0
        self.avg_doc_len = 0.0
        self.doc_lens: List[int] = []
        self.doc_ids: List[int] = []
        self.doc_metadata: List[Dict[str, Any]] = []
        self.inverted_index: Dict[str, List[Tuple[int, int]]] = {}  # term -> [(doc_idx, freq)]
        self.idf: Dict[str, float] = {}

    def _tokenize(self, text: str) -> List[str]:
        if not text:
            return []
        # Lowercase and split on punctuation / whitespace while preserving numbers
        clean = text.lower()
        # Keep alphanumeric words and IS standard tokens
        tokens = re.findall(r"\b[a-z0-9]+(?:\.[a-z0-9]+)*\b", clean)
        return [t for t in tokens if len(t) > 1]

    def build_index(self, standards: List[Any]):
        """Builds BM25 index over the provided list of standards."""
        self.corpus_size = len(standards)
        self.doc_ids = []
        self.doc_lens = []
        self.doc_metadata = []
        self.inverted_index = {}
        total_len = 0

        doc_term_freqs: List[Dict[str, int]] = []

        for idx, s in enumerate(standards):
            std_id = getattr(s, "id", idx)
            self.doc_ids.append(std_id)

            # Build document text
            text_parts = [
                getattr(s, "standard_id", "") or "",
                getattr(s, "is_number", "") or "",
                getattr(s, "title", "") or "",
                getattr(s, "scope", "") or "",
                getattr(s, "description", "") or "",
                getattr(s, "category", "") or "",
                getattr(s, "subject_area", "") or "",
            ]
            keywords = getattr(s, "keywords", None) or []
            if isinstance(keywords, list):
                text_parts.extend(keywords)

            full_text = " ".join([p for p in text_parts if p])
            tokens = self._tokenize(full_text)
            doc_len = len(tokens)
            self.doc_lens.append(doc_len)
            total_len += doc_len

            tf = Counter(tokens)
            doc_term_freqs.append(tf)

            self.doc_metadata.append({
                "id": std_id,
                "standard_id": getattr(s, "standard_id", ""),
                "is_number": getattr(s, "is_number", ""),
                "title": getattr(s, "title", ""),
                "category": getattr(s, "category", ""),
                "status": getattr(s, "status", ""),
            })

            for term, count in tf.items():
                self.inverted_index.setdefault(term, []).append((idx, count))

        self.avg_doc_len = (total_len / self.corpus_size) if self.corpus_size > 0 else 0.0

        # Calculate IDF for all indexed terms
        self.idf = {}
        for term, postings in self.inverted_index.items():
            df = len(postings)
            # Standard Lucene/BM25 IDF
            idf_val = math.log(1.0 + (self.corpus_size - df + 0.5) / (df + 0.5))
            self.idf[term] = max(0.0, idf_val)

    def search(self, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        """Searches BM25 index with query and returns scored standards."""
        if not query or self.corpus_size == 0:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        scores = [0.0] * self.corpus_size

        for term in query_tokens:
            if term not in self.inverted_index:
                continue

            idf_val = self.idf[term]
            postings = self.inverted_index[term]

            for doc_idx, freq in postings:
                doc_len = self.doc_lens[doc_idx]
                denom = freq + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
                term_score = idf_val * (freq * (self.k1 + 1.0)) / (denom if denom > 0 else 1.0)
                scores[doc_idx] += term_score

        # Rank documents with non-zero scores
        scored_docs = [
            (doc_idx, score)
            for doc_idx, score in enumerate(scores)
            if score > 0.0
        ]
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        results = []
        max_score = scored_docs[0][1] if scored_docs else 1.0

        for doc_idx, raw_score in scored_docs[:top_k]:
            meta = self.doc_metadata[doc_idx].copy()
            meta["bm25_raw_score"] = raw_score
            # Normalize BM25 score to 0..1 relative to top hit
            meta["bm25_score"] = (raw_score / max_score) if max_score > 0 else 0.0
            meta["rank"] = len(results) + 1
            results.append(meta)

        return results
