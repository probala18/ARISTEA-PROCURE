"""
Command-Line Runner for BIS Dataset Ingestion (Module 3).

Usage:
  python -m scripts.ingest [--db-url DB_URL] [--data-dir DATA_DIR] [--reset] [--report-out PATH]
"""
import sys
import os
import argparse
import logging
import json

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import Base, get_engine
from backend.app.core.config import settings
from backend.app.services.ingestion.pipeline import IngestionPipeline
from sqlalchemy.orm import sessionmaker

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

def main():
    setup_logging()
    parser = argparse.ArgumentParser(description="Ingest BIS Indian Standards datasets into database.")
    parser.add_argument(
        "--db-url",
        type=str,
        default=None,
        help="Database URL (defaults to PostgreSQL if available, otherwise sqlite:///./sih_bis.db)",
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help="Directory containing the 12 dataset files (defaults to Skill-Connect/csvfiles)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop and recreate all tables before ingestion",
    )
    parser.add_argument(
        "--report-out",
        type=str,
        default="docs/ingestion-report.md",
        help="Path where the Markdown summary report will be written",
    )
    parser.add_argument(
        "--json-out",
        type=str,
        default="docs/ingestion-summary.json",
        help="Path where the JSON summary report will be written",
    )
    args = parser.parse_args()

    # Determine database URL: try settings.DATABASE_URL, fallback to sqlite:///./sih_bis.db
    db_url = args.db_url
    if not db_url:
        # Test if default PostgreSQL is reachable
        try:
            test_engine = get_engine(settings.DATABASE_URL)
            with test_engine.connect():
                db_url = settings.DATABASE_URL
                logging.info(f"Connected to configured PostgreSQL database: {settings.POSTGRES_DB}")
        except Exception:
            db_url = "sqlite:///./sih_bis.db"
            logging.info(f"PostgreSQL not reachable. Falling back to SQLite database: {db_url}")

    # Determine data directory
    data_dir = args.data_dir
    if not data_dir:
        candidates = [
            settings.DATA_DIR,
            "Skill-Connect/csvfiles",
            "csvfiles",
            "Skill-Connect",
            ".",
        ]
        for c in candidates:
            if os.path.exists(os.path.join(c, "standards.csv")):
                data_dir = os.path.abspath(c)
                break
        if not data_dir:
            data_dir = os.path.abspath("Skill-Connect/csvfiles")

    logging.info(f"Target Database: {db_url}")
    logging.info(f"Source Data Directory: {data_dir}")

    # Engine and tables
    engine = get_engine(db_url)
    if args.reset:
        logging.info("Reset requested. Dropping all existing tables...")
        Base.metadata.drop_all(engine)

    logging.info("Ensuring database schema exists...")
    Base.metadata.create_all(engine)

    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()

    try:
        pipeline = IngestionPipeline(session=session, data_dir=data_dir)
        report_dict = pipeline.run()

        # Generate reports
        md_report = pipeline.generate_markdown_report(report_dict)

        # Write markdown report
        os.makedirs(os.path.dirname(args.report_out), exist_ok=True)
        with open(args.report_out, "w", encoding="utf-8") as f:
            f.write(md_report)
        logging.info(f"Markdown report written to: {args.report_out}")

        # Write JSON report
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2)
        logging.info(f"JSON summary written to: {args.json_out}")

        print("\n=======================================================")
        print("               INGESTION COMPLETE SUMMARY               ")
        print("=======================================================")
        print(f"Total Standards Ingested:        {report_dict['entity_counts']['total_standards']}")
        print(f"Explicit Knowledge Graph Edges:  {report_dict['entity_counts']['explicit_relationships']}")
        print(f"Derived Reference Edges:         {report_dict['entity_counts']['derived_relationships']}")
        print(f"Quality Control Orders (QCO):    {report_dict['entity_counts']['qco_records']}")
        print(f"Certification Records:           {report_dict['entity_counts']['certification_records']}")
        print(f"Product Licence Categories:      {report_dict['entity_counts']['product_licence_categories']}")
        print(f"Ministry / Dept Mappings:        {report_dict['entity_counts']['ministry_product_mappings']}")
        print(f"Benchmark Test Queries:          {report_dict['entity_counts']['evaluation_queries']}")
        print(f"Cross-Dataset Conflicts Tracked: {report_dict['conflicts_identified_count']}")
        print(f"Compliance Ambiguities Flagged:  {report_dict['ambiguities_identified_count']}")
        print("=======================================================\n")

    finally:
        session.close()

if __name__ == "__main__":
    main()
