"""
Batch Embedding Generation Script for Module 5.
Builds canonical embedding text for all standards in the database,
generates 384-dimensional vectors, and persists them to standard.embedding.

Usage:
  python -m scripts.generate_embeddings [--db-url DB_URL] [--force]
"""
import sys
import os
import argparse
import logging
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import sessionmaker
from backend.app.core.database import get_engine
from backend.app.models.standard import Standard
from backend.app.services.retrieval.embedding_provider import get_embedding_provider, EmbeddingTextBuilder


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )


def generate_and_store_embeddings(db_url: str = "sqlite:///./sih_bis.db", force: bool = False):
    engine = get_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        provider = get_embedding_provider()
        logging.info(f"Using Embedding Provider: {provider.model_name} (Pretrained: {provider.is_pretrained}, Dim: {provider.dimension})")

        standards = session.query(Standard).all()
        total_stds = len(standards)
        logging.info(f"Loaded {total_stds} standards from database.")

        to_embed = []
        for s in standards:
            if force or s.embedding is None:
                to_embed.append(s)

        if not to_embed:
            logging.info("All standards already possess 384-dim embeddings. Use --force to re-embed.")
            return total_stds

        logging.info(f"Generating embeddings for {len(to_embed)} standards...")
        t0 = time.time()

        for idx, s in enumerate(to_embed, start=1):
            vec = provider.embed_standard(s)
            s.embedding = vec
            if idx % 50 == 0 or idx == len(to_embed):
                session.commit()
                logging.info(f"Embedded {idx}/{len(to_embed)} standards...")

        session.commit()
        duration = time.time() - t0
        logging.info(f"Successfully generated and stored embeddings for {len(to_embed)} standards in {duration:.2f}s ({duration/len(to_embed)*1000:.1f}ms/standard).")
        return len(to_embed)

    finally:
        session.close()


def main():
    setup_logging()
    parser = argparse.ArgumentParser(description="Generate 384-dimensional embeddings for Indian Standards.")
    parser.add_argument("--db-url", type=str, default="sqlite:///./sih_bis.db")
    parser.add_argument("--force", action="store_true", help="Force re-generation for all records")
    args = parser.parse_args()

    generate_and_store_embeddings(db_url=args.db_url, force=args.force)


if __name__ == "__main__":
    main()
