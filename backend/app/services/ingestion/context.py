"""
Ingestion context and audit tracking for PS 26108.
Maintains state, caches, statistics, conflict tracking, and ambiguity logs.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set
import logging
from datetime import datetime

logger = logging.getLogger("ingestion")

@dataclass
class ConflictRecord:
    entity_type: str
    entity_id: str
    field_name: str
    existing_source: str
    existing_value: Any
    incoming_source: str
    incoming_value: Any
    resolution: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class AmbiguityRecord:
    standard_number: str
    title: Optional[str]
    schem_qco: bool
    report_excel_status: Optional[str]
    description: str


@dataclass
class IngestionStats:
    files_processed: Dict[str, int] = field(default_factory=dict)
    standards_created: int = 0
    standards_updated: int = 0
    departments_created: int = 0
    explicit_relationships_created: int = 0
    derived_relationships_created: int = 0
    versions_created: int = 0
    qco_records_created: int = 0
    certification_records_created: int = 0
    product_licences_created: int = 0
    ministry_mappings_created: int = 0
    queries_created: int = 0
    source_documents_created: int = 0
    unresolved_relationships: List[Dict[str, Any]] = field(default_factory=list)
    conflicts: List[ConflictRecord] = field(default_factory=list)
    ambiguities: List[AmbiguityRecord] = field(default_factory=list)


class IngestionContext:
    """Shared state during an ingestion execution run."""
    def __init__(self, session):
        self.session = session
        self.stats = IngestionStats()
        
        # In-memory lookup caches: canonical_id -> standard db id, and is_number -> standard db id
        self.standard_id_map: Dict[str, int] = {}
        self.is_number_map: Dict[str, int] = {}
        self.department_code_map: Dict[str, int] = {}
        self.source_doc_map: Dict[str, int] = {}

        self._preload_existing_entities()

    def _preload_existing_entities(self):
        """Preload existing DB entries into lookup caches for idempotent runs."""
        try:
            from backend.app.models.standard import Standard
            from backend.app.models.department import Department
            from backend.app.models.provenance import SourceDocument

            for s in self.session.query(Standard.id, Standard.standard_id, Standard.is_number).all():
                self.standard_id_map[s.standard_id] = s.id
                if s.is_number not in self.is_number_map:
                    self.is_number_map[s.is_number] = s.id

            for d in self.session.query(Department.id, Department.code).all():
                self.department_code_map[d.code] = d.id

            for doc in self.session.query(SourceDocument.id, SourceDocument.document_id, SourceDocument.standard_number).all():
                self.source_doc_map[doc.document_id] = doc.id
                if doc.standard_number:
                    self.source_doc_map[doc.standard_number] = doc.id
        except Exception as e:
            logger.debug(f"Preload skipped (tables may not exist yet): {e}")

    def register_conflict(
        self,
        entity_type: str,
        entity_id: str,
        field_name: str,
        existing_source: str,
        existing_value: Any,
        incoming_source: str,
        incoming_value: Any,
        resolution: str,
    ):
        """Record an explicit conflict between two sources."""
        c = ConflictRecord(
            entity_type=entity_type,
            entity_id=entity_id,
            field_name=field_name,
            existing_source=existing_source,
            existing_value=existing_value,
            incoming_source=incoming_source,
            incoming_value=incoming_value,
            resolution=resolution,
        )
        self.stats.conflicts.append(c)
        logger.warning(
            f"[CONFLICT] {entity_type} '{entity_id}' field '{field_name}': "
            f"'{existing_source}'={existing_value} vs '{incoming_source}'={incoming_value} -> {resolution}"
        )

    def find_standard_id(self, candidate_str: str) -> Optional[int]:
        """Find matching Standard database ID by canonical ID or is_number."""
        if not candidate_str:
            return None
        cand = candidate_str.strip()
        # Direct hit
        if cand in self.standard_id_map:
            return self.standard_id_map[cand]
        if cand in self.is_number_map:
            return self.is_number_map[cand]
        
        # Try normalized
        from backend.app.core.normalizers import parse_standard_id
        parsed = parse_standard_id(cand)
        if parsed:
            if parsed['canonical_id'] in self.standard_id_map:
                return self.standard_id_map[parsed['canonical_id']]
            if parsed['is_number'] in self.is_number_map:
                return self.is_number_map[parsed['is_number']]
        return None
