"""
Ministry and Department Product Mapping Importer for PS 26108.
Imports upcomming.csv into ministry_product_mappings and procurement_aliases.
"""
import os
import csv
import logging
from backend.app.models.department import MinistryProductMapping
from backend.app.models.ontology import ProcurementAlias
from backend.app.services.ingestion.context import IngestionContext
from backend.app.core.normalizers import parse_standard_id, clean_text

logger = logging.getLogger("ingestion.ministry")

def import_ministry_mappings(file_path: str, ctx: IngestionContext) -> int:
    """Import upcomming.csv into ministry_product_mappings table."""
    if not os.path.exists(file_path):
        logger.warning(f"upcomming.csv not found at: {file_path}")
        return 0

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        return 0

    count = 0
    # Skip header rows (row 0 and row 1)
    data_rows = rows[2:] if len(rows) > 2 else []
    for row in data_rows:
        if not row or len(row) < 4:
            continue

        raw_dept = row[1] if len(row) > 1 else ""
        raw_product = row[2] if len(row) > 2 else ""
        raw_is = row[3] if len(row) > 3 else ""

        dept = clean_text(raw_dept)
        prod = clean_text(raw_product)
        if not dept or not prod or not raw_is:
            continue

        parsed = parse_standard_id(raw_is, assume_is_prefix=True)
        std_number = parsed["is_number"] if parsed else clean_text(raw_is)
        std_id = ctx.find_standard_id(raw_is) or ctx.find_standard_id(std_number)

        existing = (
            ctx.session.query(MinistryProductMapping)
            .filter_by(
                ministry_department=dept,
                product_name=prod,
                standard_number=std_number,
            )
            .first()
        )

        if existing:
            if std_id and not existing.standard_id:
                existing.standard_id = std_id
        else:
            mp = MinistryProductMapping(
                ministry_department=dept,
                product_name=prod,
                standard_number=std_number,
                standard_id=std_id,
                source_dataset="upcomming.csv",
                source_provenance={"raw_row": row, "parsed_standard": parsed},
            )
            ctx.session.add(mp)
            count += 1
            ctx.stats.ministry_mappings_created += 1

        # Register procurement alias for product -> standard
        if prod and std_number:
            alias_ex = (
                ctx.session.query(ProcurementAlias)
                .filter_by(alias=prod, canonical_standard_number=std_number)
                .first()
            )
            if not alias_ex:
                pa = ProcurementAlias(
                    alias=prod,
                    canonical_standard_number=std_number,
                    standard_id=std_id,
                    product_context=f"Ministry context: {dept}",
                    confidence=1.0,
                    notes="Imported from upcomming.csv ministry-product mappings",
                )
                ctx.session.add(pa)

    ctx.stats.files_processed["upcomming.csv"] = len(data_rows)
    logger.info(f"Imported {count} ministry product mappings from upcomming.csv")
    return count
