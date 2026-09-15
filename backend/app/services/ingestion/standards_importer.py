"""
Standards Importer for PS 26108.
Imports standards.csv and sample_standards.json.
Enforces:
- Canonical standard ID normalization
- Provenance preservation for every imported record
- Non-silent conflict logging when values differ
- Separation of explicit vs derived relationships (normative_references and supersedes are marked derived)
- Version history and amendment tracking
- Idempotency
"""
import os
import csv
import json
import logging
from typing import Dict, Any, Optional

from backend.app.models.standard import Standard
from backend.app.models.version import StandardVersion
from backend.app.models.relationship import StandardRelationship
from backend.app.services.ingestion.context import IngestionContext
from backend.app.services.ingestion.departments import get_or_create_department
from backend.app.core.normalizers import (
    parse_standard_id,
    normalize_status,
    clean_text,
    safe_int,
    safe_bool,
    normalize_certification_type,
)

logger = logging.getLogger("ingestion.standards")

def import_standards_csv(file_path: str, ctx: IngestionContext) -> int:
    """Import standards.csv into standards and standard_versions tables."""
    if not os.path.exists(file_path):
        logger.warning(f"standards.csv not found at: {file_path}")
        return 0

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    count = 0
    for row in rows:
        raw_id = row.get("standard_id")
        if not raw_id or not clean_text(raw_id):
            continue

        parsed = parse_standard_id(raw_id)
        if not parsed:
            continue

        canonical_id = parsed["canonical_id"]
        is_number = parsed["is_number"]
        part = parsed["part"]
        section = parsed["section"]
        pub_year = parsed["year"] or safe_int(row.get("year"))

        title = clean_text(row.get("title")) or is_number
        description = clean_text(row.get("description"))
        category = clean_text(row.get("category"))
        raw_dept = row.get("department")
        dept_id = get_or_create_department(raw_dept, ctx) if raw_dept else None
        status = normalize_status(row.get("status"))
        supersedes = clean_text(row.get("supersedes"))
        cert_scheme = clean_text(row.get("certification_scheme"))
        qco_app = safe_bool(row.get("qco_applicable"))
        qco_ref = clean_text(row.get("qco_reference"))

        # Provenance metadata
        provenance = {
            "sources": [
                {
                    "file": "standards.csv",
                    "raw_row": {k: v for k, v in row.items() if v},
                }
            ],
            "conflicts": [],
        }

        # Check existing standard
        std = ctx.session.query(Standard).filter_by(standard_id=canonical_id).first()
        if not std:
            # Check by is_number if year was not part of original key
            std = ctx.session.query(Standard).filter_by(is_number=is_number, publication_year=pub_year).first()

        if std:
            # Update fields and log any differences
            if std.status != status:
                ctx.register_conflict(
                    entity_type="Standard",
                    entity_id=canonical_id,
                    field_name="status",
                    existing_source=std.source_file,
                    existing_value=std.status,
                    incoming_source="standards.csv",
                    incoming_value=status,
                    resolution=f"Preserved {std.status}",
                )
            if not std.description and description:
                std.description = description
            if not std.category and category:
                std.category = category
            if not std.department_id and dept_id:
                std.department_id = dept_id
            if not std.supersedes and supersedes:
                std.supersedes = supersedes
            if not std.certification_scheme and cert_scheme:
                std.certification_scheme = cert_scheme
            if std.qco_applicable is None and qco_app is not None:
                std.qco_applicable = qco_app
            if not std.qco_reference and qco_ref:
                std.qco_reference = qco_ref
            ctx.stats.standards_updated += 1
        else:
            std = Standard(
                standard_id=canonical_id,
                is_number=is_number,
                part=part,
                section=section,
                title=title,
                description=description,
                category=category,
                subject_area=category,
                department_id=dept_id,
                publication_year=pub_year,
                latest_year=pub_year,
                status=status,
                supersedes=supersedes,
                certification_scheme=cert_scheme,
                qco_applicable=qco_app,
                qco_reference=qco_ref,
                source_file="standards.csv",
                source_provenance=provenance,
            )
            ctx.session.add(std)
            ctx.session.flush()
            count += 1
            ctx.stats.standards_created += 1

        # Populate cache
        ctx.standard_id_map[canonical_id] = std.id
        ctx.is_number_map[is_number] = std.id

        # Record initial version history
        v_existing = (
            ctx.session.query(StandardVersion)
            .filter_by(standard_id=std.id, is_number=is_number, version_year=pub_year)
            .first()
        )
        if not v_existing:
            sv = StandardVersion(
                standard_id=std.id,
                is_number=is_number,
                version_year=pub_year,
                latest_year=pub_year,
                current_state=status,
                superseded_by=None if status == "CURRENT" else supersedes,
                superseded_state=(status == "SUPERSEDED"),
                source_dataset="standards.csv",
                source_provenance={"raw": row},
            )
            ctx.session.add(sv)
            ctx.stats.versions_created += 1

        # Record derived relationship for supersedes if present
        if supersedes:
            sup_norm = parse_standard_id(supersedes)
            target_num = sup_norm["is_number"] if sup_norm else supersedes
            rel_existing = (
                ctx.session.query(StandardRelationship)
                .filter_by(
                    source_standard_id=std.id,
                    target_standard_number=target_num,
                    relationship_type="SUPERSEDES",
                    is_explicit_source=False,
                )
                .first()
            )
            if not rel_existing:
                sr = StandardRelationship(
                    source_standard_id=std.id,
                    target_standard_id=ctx.is_number_map.get(target_num),
                    source_standard_number=is_number,
                    target_standard_number=target_num,
                    relationship_type="SUPERSEDES",
                    relationship_category="supersedes",
                    relationship_description=f"{canonical_id} supersedes {supersedes}",
                    confidence=1.0,
                    is_explicit_source=False,  # DERIVED
                    source_dataset="standards.csv",
                    source_provenance={"raw_field": "supersedes", "value": supersedes},
                )
                ctx.session.add(sr)
                ctx.stats.derived_relationships_created += 1

    ctx.stats.files_processed["standards.csv"] = len(rows)
    logger.info(f"Processed standards.csv: {count} new, {ctx.stats.standards_updated} updated")
    return count


def import_sample_standards_json(file_path: str, ctx: IngestionContext) -> int:
    """Import sample_standards.json into standards, standard_versions, and derived relationships."""
    if not os.path.exists(file_path):
        logger.warning(f"sample_standards.json not found at: {file_path}")
        return 0

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    count = 0
    for item in data:
        raw_is = item.get("is_number")
        if not raw_is:
            continue

        part = clean_text(item.get("part"))
        section = clean_text(item.get("section"))
        pub_year = safe_int(item.get("year_of_publication"))
        latest_year = safe_int(item.get("latest_year")) or pub_year

        # Build full identifier string
        composed_id = raw_is
        if part:
            composed_id += f" (Part {part})"
        if section:
            composed_id += f"/Sec {section}"
        if pub_year:
            composed_id += f":{pub_year}"

        parsed = parse_standard_id(composed_id)
        canonical_id = parsed["canonical_id"] if parsed else composed_id
        is_number = parsed["is_number"] if parsed else raw_is

        title = clean_text(item.get("title")) or is_number
        scope = clean_text(item.get("scope"))
        description = clean_text(item.get("description"))
        subject_area = clean_text(item.get("subject_area"))
        division = clean_text(item.get("division"))
        tech_comm = clean_text(item.get("technical_committee"))
        dept_id = get_or_create_department(tech_comm, ctx) if tech_comm else None
        status = normalize_status(item.get("status"))
        is_mand = safe_bool(item.get("is_mandatory_certification"))
        cert_type = normalize_certification_type(item.get("certification_type"))

        # Look up existing standard by canonical_id or is_number
        std_id = ctx.find_standard_id(canonical_id) or ctx.find_standard_id(is_number)
        std = ctx.session.query(Standard).get(std_id) if std_id else None
        if not std:
            std = ctx.session.query(Standard).filter(
                (Standard.standard_id == canonical_id) |
                (Standard.standard_id == is_number) |
                ((Standard.is_number == is_number) & (Standard.publication_year == pub_year)) |
                (Standard.is_number == is_number)
            ).first()

        if std:
            # Check for conflict in status
            if std.status and std.status != status:
                ctx.register_conflict(
                    entity_type="Standard",
                    entity_id=std.standard_id,
                    field_name="status",
                    existing_source=std.source_file,
                    existing_value=std.status,
                    incoming_source="sample_standards.json",
                    incoming_value=status,
                    resolution=f"Retained {std.status}; recorded sample_standards.json status as alternative",
                )
                # Append conflict to source_provenance
                prov = std.source_provenance or {"sources": [], "conflicts": []}
                if "conflicts" not in prov:
                    prov["conflicts"] = []
                prov["conflicts"].append({
                    "field": "status",
                    "existing_value": std.status,
                    "incoming_value": status,
                    "source": "sample_standards.json",
                })
                std.source_provenance = prov

            # Merge / enrich fields
            if not std.scope and scope:
                std.scope = scope
            if not std.description and description:
                std.description = description
            if not std.division and division:
                std.division = division
            if not std.subject_area and subject_area:
                std.subject_area = subject_area
            if not std.department_id and dept_id:
                std.department_id = dept_id
            if not std.latest_year and latest_year:
                std.latest_year = latest_year
            if std.is_mandatory_certification is None and is_mand is not None:
                std.is_mandatory_certification = is_mand
            if not std.certification_scheme and cert_type:
                std.certification_scheme = cert_type

            # Add source entry
            prov = std.source_provenance or {"sources": [], "conflicts": []}
            if "sources" not in prov:
                prov["sources"] = []
            prov["sources"].append({
                "file": "sample_standards.json",
                "raw_item": {k: v for k, v in item.items() if k not in ("normative_references", "amendments")},
            })
            std.source_provenance = prov
            ctx.stats.standards_updated += 1
        else:
            provenance = {
                "sources": [
                    {
                        "file": "sample_standards.json",
                        "raw_item": {k: v for k, v in item.items() if k not in ("normative_references", "amendments")},
                    }
                ],
                "conflicts": [],
            }
            std = Standard(
                standard_id=canonical_id,
                is_number=is_number,
                part=part,
                section=section,
                title=title,
                scope=scope,
                description=description,
                category=subject_area,
                subject_area=subject_area,
                division=division,
                department_id=dept_id,
                technical_committee=tech_comm,
                publication_year=pub_year,
                latest_year=latest_year,
                status=status,
                certification_scheme=cert_type,
                is_mandatory_certification=is_mand,
                source_file="sample_standards.json",
                source_provenance=provenance,
            )
            ctx.session.add(std)
            ctx.session.flush()
            count += 1
            ctx.stats.standards_created += 1

        # Cache standard IDs
        ctx.standard_id_map[canonical_id] = std.id
        ctx.is_number_map[is_number] = std.id

        # Record version history & amendments
        amendments = item.get("amendments") or []
        if amendments:
            for am in amendments:
                am_num = safe_int(am.get("amendment_number"))
                am_yr = safe_int(am.get("year"))
                desc = clean_text(am.get("change_summary"))
                v_ex = (
                    ctx.session.query(StandardVersion)
                    .filter_by(standard_id=std.id, amendment_number=am_num, amendment_year=am_yr)
                    .first()
                )
                if not v_ex:
                    sv = StandardVersion(
                        standard_id=std.id,
                        is_number=is_number,
                        version_year=pub_year,
                        latest_year=latest_year,
                        amendment_number=am_num,
                        amendment_year=am_yr,
                        change_description=desc,
                        current_state=status,
                        source_dataset="sample_standards.json",
                        source_provenance={"amendment": am},
                    )
                    ctx.session.add(sv)
                    ctx.stats.versions_created += 1
        else:
            # Base version if not already created
            v_ex = (
                ctx.session.query(StandardVersion)
                .filter_by(standard_id=std.id, version_year=pub_year)
                .first()
            )
            if not v_ex:
                sv = StandardVersion(
                    standard_id=std.id,
                    is_number=is_number,
                    version_year=pub_year,
                    latest_year=latest_year,
                    current_state=status,
                    source_dataset="sample_standards.json",
                    source_provenance={"base_item": raw_is},
                )
                ctx.session.add(sv)
                ctx.stats.versions_created += 1

        # Process normative_references -> DERIVED relationships
        norm_refs = item.get("normative_references") or []
        for ref in norm_refs:
            if isinstance(ref, dict):
                ref_raw = ref.get("id") or ref.get("standard_number")
                ref_title = clean_text(ref.get("title"))
            elif isinstance(ref, str):
                ref_raw = ref.strip()
                ref_title = None
            else:
                continue

            if not ref_raw:
                continue
            ref_norm = parse_standard_id(ref_raw)
            ref_target = ref_norm["is_number"] if ref_norm else ref_raw.strip()

            rel_ex = (
                ctx.session.query(StandardRelationship)
                .filter_by(
                    source_standard_id=std.id,
                    target_standard_number=ref_target,
                    relationship_type="NORMATIVE_REFERENCE",
                    is_explicit_source=False,
                )
                .first()
            )
            if not rel_ex:
                sr = StandardRelationship(
                    source_standard_id=std.id,
                    target_standard_id=ctx.find_standard_id(ref_target),
                    source_standard_number=is_number,
                    target_standard_number=ref_target,
                    target_standard_title=ref_title,
                    relationship_type="NORMATIVE_REFERENCE",
                    relationship_category="normative_references",
                    relationship_description=f"Normative reference cited in {is_number}",
                    confidence=0.9,
                    is_explicit_source=False,  # DERIVED
                    source_dataset="sample_standards.json",
                    source_provenance={"normative_reference": ref},
                )
                ctx.session.add(sr)
                ctx.stats.derived_relationships_created += 1

    ctx.stats.files_processed["sample_standards.json"] = len(data)
    logger.info(f"Processed sample_standards.json: {count} new standards created")
    return count
