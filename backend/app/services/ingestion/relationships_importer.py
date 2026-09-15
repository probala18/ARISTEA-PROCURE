"""
Explicit Relationships Importer for PS 26108.
Imports relationships.json.
Enforces:
- is_explicit_source = True (clearly segregated from derived references)
- Foreign key linkage where targets exist
- Explicit logging of unresolved cross-references
- Idempotency
"""
import os
import json
import logging
from typing import Dict, Any

from backend.app.models.standard import Standard
from backend.app.models.relationship import StandardRelationship
from backend.app.services.ingestion.context import IngestionContext
from backend.app.core.normalizers import (
    parse_standard_id,
    normalize_relationship_type,
    clean_text,
)

logger = logging.getLogger("ingestion.relationships")

def import_relationships_json(file_path: str, ctx: IngestionContext) -> int:
    """Import relationships.json as explicit relationships."""
    if not os.path.exists(file_path):
        logger.warning(f"relationships.json not found at: {file_path}")
        return 0

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    count = 0
    for source_key, categories in data.items():
        source_std_id = ctx.find_standard_id(source_key)
        if not source_std_id:
            # Query by raw standard_id or is_number
            s_parsed = parse_standard_id(source_key)
            std_obj = ctx.session.query(Standard).filter(
                (Standard.standard_id == source_key) |
                (Standard.standard_id == (s_parsed["canonical_id"] if s_parsed else source_key)) |
                (Standard.is_number == (s_parsed["is_number"] if s_parsed else source_key))
            ).first()
            if std_obj:
                source_std_id = std_obj.id
                ctx.standard_id_map[std_obj.standard_id] = std_obj.id
                ctx.is_number_map[std_obj.is_number] = std_obj.id

        if not source_std_id:
            logger.warning(f"Source standard not found for relationship group: {source_key}")
            ctx.stats.unresolved_relationships.append({
                "source": source_key,
                "target": "N/A",
                "reason": f"Source standard '{source_key}' not found in standards repository",
            })
            continue

        source_std = ctx.session.query(Standard).get(source_std_id)
        source_std_num = source_std.is_number if source_std else source_key

        for category, items in categories.items():
            if not isinstance(items, list):
                continue

            for item in items:
                raw_target_id = item.get("id") or item.get("standard_id") or item.get("standard_number")
                if not raw_target_id:
                    continue

                target_parsed = parse_standard_id(raw_target_id)
                target_num = target_parsed["is_number"] if target_parsed else clean_text(raw_target_id)
                target_title = clean_text(item.get("title"))
                raw_rel_type = item.get("relationship") or category
                rel_type = normalize_relationship_type(raw_rel_type)

                target_std_id = ctx.find_standard_id(raw_target_id) or ctx.find_standard_id(target_num)
                if not target_std_id:
                    ctx.stats.unresolved_relationships.append({
                        "source": source_key,
                        "target": raw_target_id,
                        "normalized_target": target_num,
                        "relationship_type": rel_type,
                        "reason": f"Target standard '{raw_target_id}' not found in database",
                    })

                existing_rel = (
                    ctx.session.query(StandardRelationship)
                    .filter_by(
                        source_standard_id=source_std_id,
                        target_standard_number=target_num,
                        relationship_type=rel_type,
                        is_explicit_source=True,
                    )
                    .first()
                )

                if existing_rel:
                    # Update fields idempotently
                    if target_std_id and not existing_rel.target_standard_id:
                        existing_rel.target_standard_id = target_std_id
                    if target_title and not existing_rel.target_standard_title:
                        existing_rel.target_standard_title = target_title
                else:
                    sr = StandardRelationship(
                        source_standard_id=source_std_id,
                        target_standard_id=target_std_id,
                        source_standard_number=source_std_num,
                        target_standard_number=target_num,
                        target_standard_title=target_title,
                        relationship_type=rel_type,
                        relationship_category=category,
                        relationship_description=f"{category}: {raw_rel_type}",
                        confidence=1.0,
                        is_explicit_source=True,  # EXPLICIT
                        source_dataset="relationships.json",
                        source_provenance={"category": category, "raw_item": item},
                    )
                    ctx.session.add(sr)
                    count += 1
                    ctx.stats.explicit_relationships_created += 1

    ctx.stats.files_processed["relationships.json"] = len(data)
    logger.info(f"Imported {count} explicit relationships from relationships.json")
    return count
