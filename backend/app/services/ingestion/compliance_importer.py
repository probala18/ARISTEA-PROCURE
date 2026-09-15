"""
Compliance and Certification Importer for PS 26108.
Imports:
- schem.csv (QCO Records)
- certification.csv (Certification Records)
- bis_standards.csv (CRS Certification Records & Aliases)
- ReportExcel.csv (Mandatory/Voluntary Certification Records)

Enforces:
- Non-silent ambiguity detection (e.g., standard voluntary in ReportExcel but present in QCO list)
- Provenance preservation for every record
- Hierarchical notification cascading for QCO groups in schem.csv
- Idempotency
"""
import os
import csv
import re
import logging
from typing import Optional, Dict, Any, List

from backend.app.models.compliance import QCORecord, CertificationRecord
from backend.app.models.ontology import ProcurementAlias
from backend.app.models.standard import Standard
from backend.app.services.ingestion.context import IngestionContext, AmbiguityRecord
from backend.app.core.normalizers import (
    parse_standard_id,
    clean_text,
    safe_bool,
    normalize_certification_type,
)

logger = logging.getLogger("ingestion.compliance")

def import_schem_csv(file_path: str, ctx: IngestionContext) -> int:
    """Import schem.csv containing Quality Control Orders (QCOs)."""
    if not os.path.exists(file_path):
        logger.warning(f"schem.csv not found at: {file_path}")
        return 0

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        return 0

    # Group cascading state
    current_qco_title = None
    current_notif_links = None
    count = 0

    # Start from row 1 (skip headers)
    for idx, row in enumerate(rows[1:], start=1):
        if not row or len(row) < 3:
            continue

        raw_is = row[1] if len(row) > 1 else ""
        raw_product = row[2] if len(row) > 2 else ""
        raw_notif = row[3] if len(row) > 3 else ""
        raw_links = row[4] if len(row) > 4 else ""

        # Check if new QCO section header in notification column
        cleaned_notif = clean_text(raw_notif)
        if cleaned_notif:
            current_qco_title = cleaned_notif
            current_notif_links = clean_text(raw_links)

        # Skip rows with no standard number
        if not raw_is or not clean_text(raw_is):
            continue

        parsed = parse_standard_id(raw_is)
        std_number = parsed["is_number"] if parsed else clean_text(raw_is)
        prod_name = clean_text(raw_product)

        # Extract notification number if present (e.g. S.O. No. 191(E))
        notif_num = None
        if current_qco_title:
            m = re.search(r'(S\.O\.\s*No\.?\s*[0-9]+(?:\([A-Za-z0-9]+\))?)', current_qco_title, re.IGNORECASE)
            if m:
                notif_num = m.group(1)

        std_id = ctx.find_standard_id(raw_is) or ctx.find_standard_id(std_number)

        # Check existing QCO record
        existing = (
            ctx.session.query(QCORecord)
            .filter_by(standard_number=std_number, product_name=prod_name, source_dataset="schem.csv")
            .first()
        )

        if existing:
            if std_id and not existing.standard_id:
                existing.standard_id = std_id
            if current_qco_title and not existing.qco_title:
                existing.qco_title = current_qco_title
        else:
            qco = QCORecord(
                standard_id=std_id,
                standard_number=std_number,
                product_name=prod_name,
                qco_title=current_qco_title,
                notification_number=notif_num,
                notification_links=current_notif_links,
                is_mandatory=True,
                source_dataset="schem.csv",
                source_provenance={"raw_row": row, "group_qco": current_qco_title},
            )
            ctx.session.add(qco)
            count += 1
            ctx.stats.qco_records_created += 1

        # Also update standard's qco_applicable if standard exists in DB
        if std_id:
            std_obj = ctx.session.query(Standard).get(std_id)
            if std_obj and not std_obj.qco_applicable:
                std_obj.qco_applicable = True
                if current_qco_title and not std_obj.qco_reference:
                    std_obj.qco_reference = current_qco_title

    ctx.stats.files_processed["schem.csv"] = len(rows) - 1
    logger.info(f"Imported {count} QCO records from schem.csv")
    return count


def import_certification_csv(file_path: str, ctx: IngestionContext) -> int:
    """Import certification.csv (Circuit breakers & electrical switchgear certifications)."""
    if not os.path.exists(file_path):
        logger.warning(f"certification.csv not found at: {file_path}")
        return 0

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        return 0

    count = 0
    for row in rows[1:]:
        if not row or len(row) < 3:
            continue

        raw_is = row[1] if len(row) > 1 else ""
        raw_product = row[2] if len(row) > 2 else ""
        raw_rating = row[3] if len(row) > 3 else ""

        if not raw_is or not clean_text(raw_is):
            continue

        parsed = parse_standard_id(raw_is)
        std_number = parsed["is_number"] if parsed else clean_text(raw_is)
        product_name = clean_text(raw_product)
        rating = clean_text(raw_rating)
        std_id = ctx.find_standard_id(raw_is) or ctx.find_standard_id(std_number)

        existing = (
            ctx.session.query(CertificationRecord)
            .filter_by(
                standard_number=std_number,
                product_name=product_name,
                product_rating=rating,
                source_dataset="certification.csv",
            )
            .first()
        )

        if existing:
            if std_id and not existing.standard_id:
                existing.standard_id = std_id
        else:
            rec = CertificationRecord(
                standard_id=std_id,
                standard_number=std_number,
                product_name=product_name,
                product_rating=rating,
                certification_type="BIS_ISI",
                is_mandatory=True,
                requirement_level="MANDATORY",
                source_dataset="certification.csv",
                source_provenance={"raw_row": row},
            )
            ctx.session.add(rec)
            count += 1
            ctx.stats.certification_records_created += 1

    ctx.stats.files_processed["certification.csv"] = len(rows) - 1
    logger.info(f"Imported {count} certification records from certification.csv")
    return count


def import_bis_standards_csv(file_path: str, ctx: IngestionContext) -> int:
    """Import bis_standards.csv (Compulsory Registration Scheme / IT & Electronics standards)."""
    if not os.path.exists(file_path):
        logger.warning(f"bis_standards.csv not found at: {file_path}")
        return 0

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        return 0

    count = 0
    # Skip row 0 (system headers) and row 1 (table headers)
    data_rows = rows[2:] if len(rows) > 2 else []
    for row in data_rows:
        if not row or len(row) < 3:
            continue

        raw_is = row[1] if len(row) > 1 else ""
        raw_title = row[2] if len(row) > 2 else ""
        raw_category = row[3] if len(row) > 3 else ""

        if not raw_is or not clean_text(raw_is):
            continue

        parsed = parse_standard_id(raw_is)
        std_number = parsed["is_number"] if parsed else clean_text(raw_is)
        title = clean_text(raw_title)
        category = clean_text(raw_category)
        std_id = ctx.find_standard_id(raw_is) or ctx.find_standard_id(std_number)

        existing = (
            ctx.session.query(CertificationRecord)
            .filter_by(
                standard_number=std_number,
                product_name=title,
                source_dataset="bis_standards.csv",
            )
            .first()
        )

        if existing:
            if std_id and not existing.standard_id:
                existing.standard_id = std_id
        else:
            rec = CertificationRecord(
                standard_id=std_id,
                standard_number=std_number,
                product_name=title,
                product_rating=category,
                certification_type="CRS",
                is_mandatory=True,
                requirement_level="MANDATORY",
                source_dataset="bis_standards.csv",
                source_provenance={"raw_row": row, "scheme": "CRS"},
            )
            ctx.session.add(rec)
            count += 1
            ctx.stats.certification_records_created += 1

        # Also register alias if category is present
        if category:
            alias_ex = (
                ctx.session.query(ProcurementAlias)
                .filter_by(alias=category, canonical_standard_number=std_number)
                .first()
            )
            if not alias_ex:
                pa = ProcurementAlias(
                    alias=category,
                    canonical_standard_number=std_number,
                    standard_id=std_id,
                    product_context=title,
                    confidence=0.95,
                    notes="Imported from bis_standards.csv CRS product categories",
                )
                ctx.session.add(pa)

    ctx.stats.files_processed["bis_standards.csv"] = len(data_rows)
    logger.info(f"Imported {count} CRS certification records from bis_standards.csv")
    return count


def import_report_excel_csv(file_path: str, ctx: IngestionContext) -> int:
    """Import ReportExcel.csv (Mandatory vs Voluntary standards dataset)."""
    if not os.path.exists(file_path):
        logger.warning(f"ReportExcel.csv not found at: {file_path}")
        return 0

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        return 0

    # Build set of standards in QCO list (schem.csv) for cross-checking ambiguities
    qco_std_numbers = set(
        q[0] for q in ctx.session.query(QCORecord.standard_number).distinct().all()
    )

    count = 0
    for row in rows[1:]:
        if not row or len(row) < 4:
            continue

        raw_std_num = row[1]
        title = clean_text(row[2])
        raw_status = clean_text(row[3]) or "Voluntary"

        if not raw_std_num or not clean_text(raw_std_num):
            continue

        parsed = parse_standard_id(raw_std_num)
        std_number = parsed["is_number"] if parsed else clean_text(raw_std_num)
        is_mand = "mandatory" in raw_status.lower()
        req_level = "MANDATORY" if is_mand else "VOLUNTARY"
        std_id = ctx.find_standard_id(raw_std_num) or ctx.find_standard_id(std_number)

        # Ambiguity detection: marked Voluntary in ReportExcel, but listed in QCO table (schem.csv)
        if not is_mand and (std_number in qco_std_numbers or (parsed and parsed["canonical_id"] in qco_std_numbers)):
            amb = AmbiguityRecord(
                standard_number=std_number,
                title=title,
                schem_qco=True,
                report_excel_status=raw_status,
                description=(
                    f"Standard {std_number} is classified as '{raw_status}' in ReportExcel.csv, "
                    f"yet appears under an active Quality Control Order in schem.csv."
                ),
            )
            ctx.stats.ambiguities.append(amb)
            logger.info(f"[AMBIGUITY] {std_number}: Voluntary in ReportExcel vs active QCO in schem.csv")

        existing = (
            ctx.session.query(CertificationRecord)
            .filter_by(
                standard_number=std_number,
                source_dataset="ReportExcel.csv",
            )
            .first()
        )

        if existing:
            if std_id and not existing.standard_id:
                existing.standard_id = std_id
            if title and not existing.product_name:
                existing.product_name = title
        else:
            rec = CertificationRecord(
                standard_id=std_id,
                standard_number=std_number,
                product_name=title,
                certification_type=None,
                is_mandatory=is_mand,
                requirement_level=req_level,
                source_dataset="ReportExcel.csv",
                source_provenance={"raw_row": row, "mandatory_voluntary": raw_status},
            )
            ctx.session.add(rec)
            count += 1
            ctx.stats.certification_records_created += 1

    ctx.stats.files_processed["ReportExcel.csv"] = len(rows) - 1
    logger.info(f"Imported {count} certification records from ReportExcel.csv")
    return count
