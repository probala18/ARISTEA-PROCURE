"""
Document Parsers for Tender Engine (Module 11).
Implements Section 86 specifications:
- PDF: uses PyMuPDF (pymupdf)
- DOCX: uses python-docx
- TXT: plain structured parser
Preserves page, section, clause, source text with zero data truncation.
"""
import io
import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class ParsedPage:
    """Represents a single page extracted from a document."""
    page_number: int
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentParseResult:
    """Complete structured extraction result from a document parser."""
    file_type: str
    total_pages: int
    raw_text: str
    pages: List[ParsedPage]
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseDocumentParser(ABC):
    """Abstract Base Class for Tender Document Parsers."""

    @abstractmethod
    def parse(self, content_bytes: bytes, filename: Optional[str] = None) -> DocumentParseResult:
        """Parses document bytes and returns structured text with page preservation."""
        pass


class PDFParser(BaseDocumentParser):
    """PDF parser using PyMuPDF (pymupdf) as mandated in Section 86."""

    def parse(self, content_bytes: bytes, filename: Optional[str] = None) -> DocumentParseResult:
        if not content_bytes or len(content_bytes) < 10:
            raise ValueError("Empty or invalid PDF file content.")

        try:
            import pymupdf
        except ImportError:
            import fitz as pymupdf

        try:
            doc = pymupdf.open(stream=content_bytes, filetype="pdf")
        except Exception as e:
            raise ValueError(f"Failed to open PDF document: {e}")

        pages: List[ParsedPage] = []
        full_text_chunks: List[str] = []

        for page_idx in range(len(doc)):
            page = doc[page_idx]
            page_text = page.get_text("text").strip()
            pages.append(ParsedPage(
                page_number=page_idx + 1,
                text=page_text,
                metadata={
                    "rect": [round(c, 1) for c in page.rect],
                    "rotation": page.rotation,
                }
            ))
            if page_text:
                full_text_chunks.append(page_text)

        doc_meta = doc.metadata or {}
        raw_text = "\n\n".join(full_text_chunks)

        return DocumentParseResult(
            file_type="PDF",
            total_pages=len(pages),
            raw_text=raw_text,
            pages=pages,
            metadata={
                "title": doc_meta.get("title") or filename,
                "author": doc_meta.get("author"),
                "producer": doc_meta.get("producer"),
                "page_count": len(pages),
            }
        )


class DOCXParser(BaseDocumentParser):
    """DOCX parser using python-docx as mandated in Section 86."""

    def parse(self, content_bytes: bytes, filename: Optional[str] = None) -> DocumentParseResult:
        if not content_bytes or len(content_bytes) < 10:
            raise ValueError("Empty or invalid DOCX file content.")

        import docx

        try:
            doc = docx.Document(io.BytesIO(content_bytes))
        except Exception as e:
            raise ValueError(f"Failed to open DOCX document: {e}")

        paragraphs_text: List[str] = []
        for p in doc.paragraphs:
            txt = p.text.strip()
            if txt:
                paragraphs_text.append(txt)

        # Also extract table contents
        for table in doc.tables:
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_cells:
                    paragraphs_text.append(" | ".join(row_cells))

        full_text = "\n\n".join(paragraphs_text)

        # Chunk paragraphs into logical pages (~3000 chars or 50 lines per page)
        pages: List[ParsedPage] = []
        if not paragraphs_text:
            pages.append(ParsedPage(page_number=1, text=""))
        else:
            current_page_num = 1
            current_chunk: List[str] = []
            current_len = 0

            for para in paragraphs_text:
                current_chunk.append(para)
                current_len += len(para)
                if current_len >= 2500:
                    pages.append(ParsedPage(
                        page_number=current_page_num,
                        text="\n\n".join(current_chunk)
                    ))
                    current_page_num += 1
                    current_chunk = []
                    current_len = 0

            if current_chunk:
                pages.append(ParsedPage(
                    page_number=current_page_num,
                    text="\n\n".join(current_chunk)
                ))

        return DocumentParseResult(
            file_type="DOCX",
            total_pages=len(pages),
            raw_text=full_text,
            pages=pages,
            metadata={
                "title": filename,
                "paragraph_count": len(doc.paragraphs),
                "table_count": len(doc.tables),
            }
        )


class TXTParser(BaseDocumentParser):
    """Plain text parser with page and section preservation."""

    def parse(self, content_bytes: bytes, filename: Optional[str] = None) -> DocumentParseResult:
        if not content_bytes:
            raise ValueError("Empty text file content.")

        # Decode text with fallback
        try:
            text = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text = content_bytes.decode("latin-1")
            except Exception as e:
                raise ValueError(f"Failed to decode text file: {e}")

        clean_text = text.strip()

        # Handle form feed (\x0c) page breaks if present
        raw_pages = clean_text.split("\x0c")
        pages: List[ParsedPage] = []

        if len(raw_pages) > 1:
            for idx, p_text in enumerate(raw_pages):
                pages.append(ParsedPage(page_number=idx + 1, text=p_text.strip()))
        else:
            # Chunk by ~3000 characters or logical sections
            lines = clean_text.splitlines()
            current_page_num = 1
            current_chunk: List[str] = []
            current_len = 0

            for line in lines:
                current_chunk.append(line)
                current_len += len(line)
                if current_len >= 2500:
                    pages.append(ParsedPage(
                        page_number=current_page_num,
                        text="\n".join(current_chunk).strip()
                    ))
                    current_page_num += 1
                    current_chunk = []
                    current_len = 0

            if current_chunk:
                pages.append(ParsedPage(
                    page_number=current_page_num,
                    text="\n".join(current_chunk).strip()
                ))

        if not pages:
            pages.append(ParsedPage(page_number=1, text=""))

        return DocumentParseResult(
            file_type="TXT",
            total_pages=len(pages),
            raw_text=clean_text,
            pages=pages,
            metadata={"title": filename, "character_count": len(clean_text)}
        )


def get_parser(filename_or_type: str) -> BaseDocumentParser:
    """Factory function returning the appropriate parser for file format."""
    normalized = filename_or_type.lower()
    if normalized.endswith(".pdf") or normalized == "pdf":
        return PDFParser()
    elif normalized.endswith(".docx") or normalized == "docx":
        return DOCXParser()
    elif normalized.endswith(".txt") or normalized == "txt":
        return TXTParser()
    else:
        # Default fallback: try TXT parser if unknown
        return TXTParser()
