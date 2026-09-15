"""
Product Licence Importer for PS 26108.
Imports productlicence.csv and cross-verifies against bis_standards.json.
Enforces:
- Factual licence count storage (strictly avoiding equating licence counts to mandatory status)
- Cross-verification between CSV and JSON sources
- Non-silent discrepancy recording
- Idempotency
"""
import os
import csv
import json
import logging
from typing import Dict, Any

from backend.app.models.compliance import ProductLicence
from backend.app.services.ingestion.context import IngestionContext
from backend.app.core.normalizers import clean_text, safe_int

logger = logging.getLogger("ingestion.product_licence")

def import_product_licences(
    csv_path: str,
    json_path: str,
    ctx: IngestionContext,
) -> int:
    """Import product licence statistics with JSON cross-validation."""
    json_counts: Dict[str, int] = {}
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            j_data = json.load(f)
            for item in j_data:
                cat = clean_text(item.get("is_number"))
                cnt_str = clean_text(item.get("product"))
                if cat and cnt_str and cat != "Products Category":
                    json_counts[cat.lower()] = safe_int(cnt_str, 0)
        ctx.stats.files_processed["bis_standards.json"] = len(j_data)

    if not os.path.exists(csv_path):
        logger.warning(f"productlicence.csv not found at: {csv_path}")
        return 0

    with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        return 0

    count = 0
    # Skip header rows (row 0 and row 1)
    data_rows = rows[2:] if len(rows) > 2 else []
    seen_in_memory: Dict[str, ProductLicence] = {}
    for row in data_rows:
        if not row or len(row) < 3:
            continue

        raw_cat = row[1] if len(row) > 1 else ""
        raw_cnt = row[2] if len(row) > 2 else ""

        category = clean_text(raw_cat)
        if not category or category == "Products Category":
            continue

        cnt = safe_int(raw_cnt, 0)

        # Cross-verify with JSON
        json_val = json_counts.get(category.lower())
        discrepancy = None
        if json_val is not None and json_val != cnt:
            discrepancy = {
                "csv_count": cnt,
                "json_count": json_val,
                "note": "Licence count difference between productlicence.csv and bis_standards.json",
            }
            ctx.register_conflict(
                entity_type="ProductLicence",
                entity_id=category,
                field_name="licence_count",
                existing_source="productlicence.csv",
                existing_value=cnt,
                incoming_source="bis_standards.json",
                incoming_value=json_val,
                resolution=f"Preserved CSV count {cnt}",
            )

        existing = seen_in_memory.get(category) or (
            ctx.session.query(ProductLicence)
            .filter_by(product_category=category)
            .first()
        )

        if existing:
            # Conflict within same dataset
            ctx.register_conflict(
                entity_type="ProductLicence",
                entity_id=category,
                field_name="licence_count",
                existing_source="productlicence.csv (earlier row)",
                existing_value=existing.licence_count,
                incoming_source="productlicence.csv (subsequent row)",
                incoming_value=cnt,
                resolution=f"Updated to latest row count {cnt} and recorded duplicate in provenance",
            )
            existing.licence_count = cnt
            existing.raw_count_str = raw_cnt
            prov = existing.source_provenance or {}
            if "duplicate_rows" not in prov:
                prov["duplicate_rows"] = []
            prov["duplicate_rows"].append(row)
            if discrepancy:
                prov["discrepancy"] = discrepancy
            existing.source_provenance = prov
        else:
            pl = ProductLicence(
                product_category=category,
                licence_count=cnt,
                raw_count_str=raw_cnt,
                source_dataset="productlicence.csv",
                source_provenance={
                    "raw_row": row,
                    "discrepancy": discrepancy,
                    "json_verified": (json_val == cnt),
                },
            )
            ctx.session.add(pl)
            seen_in_memory[category] = pl
            count += 1
            ctx.stats.product_licences_created += 1

    ctx.stats.files_processed["productlicence.csv"] = len(data_rows)
    logger.info(f"Imported {count} product licence categories")
    return count
