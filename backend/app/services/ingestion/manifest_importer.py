"""
Importer for manifest.json.
Stores source documents and establishes provenance anchors.
"""
import os
import json
import logging
from backend.app.models.provenance import SourceDocument
from backend.app.services.ingestion.context import IngestionContext
from backend.app.core.normalizers import clean_text

logger = logging.getLogger("ingestion.manifest")

def import_manifest(file_path: str, ctx: IngestionContext) -> int:
    """Import manifest.json into source_documents table."""
    if not os.path.exists(file_path):
        logger.warning(f"manifest file not found: {file_path}")
        return 0

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    count = 0
    for item in data:
        doc_id = clean_text(item.get("document_id"))
        if not doc_id:
            continue

        existing = ctx.session.query(SourceDocument).filter_by(document_id=doc_id).first()
        if existing:
            # Update fields idempotently
            existing.filename = clean_text(item.get("filename")) or existing.filename
            existing.standard_number = clean_text(item.get("standard_number")) or existing.standard_number
            existing.revision = clean_text(item.get("revision")) or existing.revision
            existing.source_type = clean_text(item.get("source_type")) or existing.source_type or "STANDARDS_DOCUMENT"
            existing.source_url = clean_text(item.get("source_url")) or existing.source_url
            existing.local_path = clean_text(item.get("local_path")) or existing.local_path
            existing.status = clean_text(item.get("status")) or existing.status
            existing.downloaded = bool(item.get("downloaded", False))
            existing.title = clean_text(item.get("title")) or existing.title
            existing.notes = clean_text(item.get("notes")) or existing.notes
            ctx.source_doc_map[doc_id] = existing.id
            if existing.standard_number:
                ctx.source_doc_map[existing.standard_number] = existing.id
        else:
            doc = SourceDocument(
                document_id=doc_id,
                filename=clean_text(item.get("filename")) or f"{doc_id}.pdf",
                standard_number=clean_text(item.get("standard_number")),
                revision=clean_text(item.get("revision")),
                source_type=clean_text(item.get("source_type")) or "STANDARDS_DOCUMENT",
                source_url=clean_text(item.get("source_url")),
                local_path=clean_text(item.get("local_path")),
                status=clean_text(item.get("status")),
                downloaded=bool(item.get("downloaded", False)),
                title=clean_text(item.get("title")),
                notes=clean_text(item.get("notes")),
            )
            ctx.session.add(doc)
            ctx.session.flush()
            ctx.source_doc_map[doc_id] = doc.id
            if doc.standard_number:
                ctx.source_doc_map[doc.standard_number] = doc.id
            count += 1
            ctx.stats.source_documents_created += 1

    ctx.stats.files_processed["manifest.json"] = len(data)
    logger.info(f"Imported {count} source documents from manifest.json")
    return count
