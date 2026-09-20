"""
Retrieval Evaluation Script for ARISTEA-PROCURE.
Evaluates Semantic Vector Retrieval against the 14 benchmark queries in query_dataset.json.
Measures:
- Top-1 Accuracy
- Top-3 Accuracy
- Top-5 Accuracy
- Mean Reciprocal Rank (MRR)
- Average Latency (ms)

Usage:
  python -m scripts.evaluate_retrieval [--db-url DB_URL] [--json-path PATH]
"""
import sys
import os
import json
import time
import argparse
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy.orm import sessionmaker
from backend.app.core.database import get_engine
from backend.app.services.retrieval.semantic_retriever import SemanticRetrievalEngine
from backend.app.core.normalizers import parse_standard_id


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )


def evaluate_retrieval_benchmark(db_url: str = "sqlite:///./sih_bis.db", json_path: str = "Skill-Connect/csvfiles/query_dataset.json"):
    if not os.path.exists(json_path):
        json_path = "csvfiles/query_dataset.json"

    with open(json_path, "r", encoding="utf-8") as f:
        queries_data = json.load(f)

    engine = get_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        retriever = SemanticRetrievalEngine(session)
        print("\n" + "=" * 70)
        print("  PS 26108 — DIAGNOSTIC RETRIEVAL REGRESSION AUDIT (SEMANTIC-ONLY)")
        print("  NOTE: Expectations below are Legacy Diagnostic Regression Expectations,")
        print("  NOT Official Ground Truth. The benchmark dataset query_dataset.json")
        print("  does not supply structured retrieval relevance rankings.")
        print("=" * 70 + "\n")

        # Legacy Diagnostic Regression Expectations (Development Fixture Only, NOT Official Ground Truth)
        # For non-standard queries (general info, out of scope, unclarified), expected_standards is empty
        query_targets = {
            "Q01": ["IS 694"],
            "Q02": ["IS 694", "IS 1554"],
            "Q03": ["IS 694"],
            "Q04": ["IS 10810", "IS 694", "IS 14255"],
            "Q05": [],  # Service listing (informational overview)
            "Q06": [],  # General BIS overview (documentary RAG)
            "Q07": ["IS 694", "IS 1554"],
            "Q08": ["IS 694", "IS 7098", "IS 1554"],
            "Q09": ["IS 7098", "IS 1554"],
            "Q10": [],  # Out of scope query ("weather in Delhi")
            "Q11": ["IS 694"],
            "Q12": ["IS 694"],  # Hindi localized query (requires NLU query translation in Module 6)
            "Q13": ["IS 694", "IS 1554"],
            "Q14": [],  # Needs clarification ("What testing is required?")
        }

        total_queries = len(queries_data)
        standard_queries = 0
        top1_hits = 0
        top3_hits = 0
        top5_hits = 0
        reciprocal_ranks = []
        latencies_ms = []

        category_results = {}
        results_log = []

        for idx, item in enumerate(queries_data, start=1):
            qid = item.get("id", f"Q{idx:02d}")
            q_text = item.get("query_text") or item.get("query")
            cat = item.get("category", "General")
            intent = item.get("expected_intent") or item.get("intent", "UNKNOWN")
            expected_stds = query_targets.get(qid, [])

            t0 = time.time()
            resp = retriever.retrieve(q_text, top_k=5)
            latency = (time.time() - t0) * 1000
            latencies_ms.append(latency)

            # Determine rank of expected standard if applicable
            rank = None
            if expected_stds:
                standard_queries += 1
                for r_idx, rec in enumerate(resp.recommendations, start=1):
                    if any(
                        exp.lower() in rec.standard_id.lower() or exp.lower() in rec.is_number.lower()
                        for exp in expected_stds
                    ):
                        rank = r_idx
                        break

                if rank == 1:
                    top1_hits += 1
                    top3_hits += 1
                    top5_hits += 1
                    reciprocal_ranks.append(1.0)
                elif rank in (2, 3):
                    top3_hits += 1
                    top5_hits += 1
                    reciprocal_ranks.append(1.0 / rank)
                elif rank in (4, 5):
                    top5_hits += 1
                    reciprocal_ranks.append(1.0 / rank)
                else:
                    reciprocal_ranks.append(0.0)

            hit_symbol = f"HIT (Rank {rank})" if rank else ("N/A (Non-Standard)" if not expected_stds else "MISS")
            top3_summary = [(r.standard_id, round(r.relevance_score, 3)) for r in resp.recommendations[:3]]
            print(f"[{qid:3s}] {hit_symbol:18} | {latency:5.1f}ms | Category: {cat}")
            print(f"      Query: '{q_text}'")
            print(f"      Expected Standards : {expected_stds if expected_stds else 'None (Non-standard / Out of Scope / Clarification)'}")
            print(f"      Top-3 Retrieved    : {top3_summary}")

            if cat not in category_results:
                category_results[cat] = {"total": 0, "hits": 0, "ranks": []}
            category_results[cat]["total"] += 1
            if rank:
                category_results[cat]["hits"] += 1
                category_results[cat]["ranks"].append(rank)

            results_log.append({
                "id": qid,
                "query": q_text,
                "category": cat,
                "intent": intent,
                "expected": expected_stds,
                "rank": rank,
                "latency_ms": round(latency, 2),
                "top3": top3_summary,
            })

        mrr = sum(reciprocal_ranks) / standard_queries if standard_queries > 0 else 0.0
        avg_latency = sum(latencies_ms) / total_queries if total_queries > 0 else 0.0

        print("\n" + "=" * 70)
        print("          OFFICIAL BENCHMARK RETRIEVAL STATUS (MODULE 16)")
        print("=" * 70)
        print("  NOTE: query_dataset.json does not provide formal structured relevance")
        print("  labels for ranked retrieval. Official metrics are preserved as:")
        print("  Official Precision@1 : UNKNOWN")
        print("  Official Precision@3 : UNKNOWN")
        print("  Official Recall@5    : UNKNOWN")
        print("  Official MRR         : UNKNOWN")
        print("=" * 70)
        print("     DIAGNOSTIC DEVELOPMENT REGRESSION SUMMARY (FIXTURES ONLY)")
        print("=" * 70)
        print(f"  Total Queries In Dataset         : {total_queries}")
        print(f"  Standard-Seeking Queries         : {standard_queries}")
        print(f"  Diagnostic Top-1 Match Rate      : {top1_hits}/{standard_queries} ({top1_hits/standard_queries*100:.1f}%)")
        print(f"  Diagnostic Top-3 Match Rate      : {top3_hits}/{standard_queries} ({top3_hits/standard_queries*100:.1f}%)")
        print(f"  Diagnostic Top-5 Match Rate      : {top5_hits}/{standard_queries} ({top5_hits/standard_queries*100:.1f}%)")
        print(f"  Diagnostic Reciprocal Rank (MRR) : {mrr:.4f}")
        print(f"  Average Retrieval Latency        : {avg_latency:.2f} ms")
        print("=" * 70 + "\n")

        return {
            "total_queries": total_queries,
            "standard_queries": standard_queries,
            "official_precision_at_1": "UNKNOWN",
            "official_precision_at_3": "UNKNOWN",
            "official_recall_at_5": "UNKNOWN",
            "official_mrr": "UNKNOWN",
            "diagnostic_top1_match_rate": round(top1_hits / standard_queries, 4) if standard_queries else 0.0,
            "diagnostic_top3_match_rate": round(top3_hits / standard_queries, 4) if standard_queries else 0.0,
            "diagnostic_top5_match_rate": round(top5_hits / standard_queries, 4) if standard_queries else 0.0,
            "diagnostic_mrr": round(mrr, 4),
            "avg_latency_ms": round(avg_latency, 2),
            "category_breakdown": category_results,
            "results": results_log,
        }

    finally:
        session.close()


def main():
    setup_logging()
    parser = argparse.ArgumentParser(description="Evaluate retrieval engine on query_dataset.json.")
    parser.add_argument("--db-url", type=str, default="sqlite:///./sih_bis.db")
    parser.add_argument("--json-path", type=str, default="Skill-Connect/csvfiles/query_dataset.json")
    args = parser.parse_args()

    evaluate_retrieval_benchmark(db_url=args.db_url, json_path=args.json_path)


if __name__ == "__main__":
    main()
