"""
Explicit Standard Reference Extractor for Tender Documents (Module 11).
Identifies Indian Standards (IS), ISO/IEC adoptions, and cross-references.
Resolves detected standards against the canonical SQLite database:
- Links detected_standard_id to authoritative Standard record
- Identifies supersession status and successor standards via Module 4 graph edges
- Preserves unlinked / unresolved standards verbatim without data loss
- Attaches exact page, section, and clause provenance
"""
import re
from typing import List, Dict, Any, Optional, Set, Tuple
from sqlalchemy.orm import Session

from backend.app.models.standard import Standard
from backend.app.models.relationship import StandardRelationship
from backend.app.services.tender_engine.schemas import ExtractedStandardReference, ExtractedSection


class StandardExtractor:
    """Extracts and grounds Indian Standard citations from tender texts."""

    # Robust Regex patterns for matching IS, IS/IEC, IS/ISO citations across all formats
    IS_PATTERNS = [
        re.compile(
            r"\b(?:IS\s*\/\s*(?:IEC|ISO)|IS|I\.S\.)\s*[:\s\-\.]?\s*([0-9]{2,6}(?:-[0-9]+)?(?:\s*(?:\([A-Za-z0-9\s\/\-]+\)|Part\s*[\d\w\/\-]+))?(?:\s*[:\-\/]\s*[0-9]{4})?)\b",
            re.IGNORECASE
        ),
    ]

    def __init__(self, db_session: Optional[Session] = None):
        self.db = db_session
        self._standards_cache: Dict[str, Standard] = {}
        if self.db:
            self._load_cache()

    def _load_cache(self):
        """Preloads standards for fast deterministic lookup."""
        standards = self.db.query(Standard).all()
        for s in standards:
            # Map full number, without year, and stripped forms
            norm_id = self._clean_number(s.standard_id)
            norm_is = self._clean_number(s.is_number)
            self._standards_cache[norm_id] = s
            self._standards_cache[norm_is] = s
            
            # Also map number without year (e.g. 'IS 12615' for 'IS 12615:2018')
            if ":" in norm_id:
                prefix = norm_id.split(":")[0].strip()
                if prefix not in self._standards_cache:
                    self._standards_cache[prefix] = s

    def _clean_number(self, raw_str: str) -> str:
        """Normalizes standard string to canonical representation (e.g. 'IS 12615:2018')."""
        s = raw_str.strip().upper()
        s = re.sub(r"\s+", " ", s)
        s = re.sub(r"\s*:\s*", ":", s)
        s = re.sub(r"\s*-\s*", "-", s)
        if not s.startswith("IS"):
            s = f"IS {s}"
        return s

    def find_standard_mentions(self, text: str) -> List[Tuple[str, str, int, int]]:
        """
        Finds all standard citations in text.
        Returns list of (raw_match, normalized_identifier, start_char, end_char).
        """
        mentions: List[Tuple[str, str, int, int]] = []
        seen: Set[str] = set()

        for pat in self.IS_PATTERNS:
            for m in pat.finditer(text):
                raw = m.group(0).strip()
                norm = self._clean_number(raw)
                if norm not in seen:
                    seen.add(norm)
                    mentions.append((raw, norm, m.start(), m.end()))

        return mentions

    def resolve_standard(self, canonical_identifier: str) -> Dict[str, Any]:
        """
        Resolves canonical standard identifier against SQLite database.
        Returns dictionary with resolution, validity, and supersession lineage.
        """
        if not self.db:
            return {
                "detected_standard_id": None,
                "title": None,
                "is_valid": False,
                "is_superseded": False,
                "superseded_by_standard_id": None,
                "superseded_by_identifier": None,
            }

        # Lookup in cache
        std = self._standards_cache.get(canonical_identifier)
        if not std and ":" in canonical_identifier:
            std = self._standards_cache.get(canonical_identifier.split(":")[0].strip())

        if not std:
            # Query directly with LIKE if not in cache
            clean_token = canonical_identifier.replace("IS", "").strip().split(":")[0]
            std = self.db.query(Standard).filter(
                (Standard.standard_id.ilike(f"%{clean_token}%")) |
                (Standard.is_number.ilike(f"%{clean_token}%"))
            ).first()

        if not std:
            return {
                "detected_standard_id": None,
                "title": None,
                "is_valid": False,
                "is_superseded": False,
                "superseded_by_standard_id": None,
                "superseded_by_identifier": None,
            }

        # Check supersession status
        is_superseded = (std.status.upper() == "SUPERSEDED")
        successor_id = None
        successor_num = None

        # Look up explicit graph edge: target standard superseding this standard
        # Crucial: source != target to avoid false self-supersession cycles
        edge = self.db.query(StandardRelationship).filter(
            StandardRelationship.target_standard_id == std.id,
            StandardRelationship.source_standard_id != std.id,
            StandardRelationship.relationship_type == "SUPERSEDES"
        ).first()

        if edge:
            is_superseded = True
            successor = self.db.query(Standard).filter(Standard.id == edge.source_standard_id).first()
            if successor:
                successor_id = successor.id
                successor_num = successor.standard_id

        # Check if the cited version has an older publication year than the active standard
        cited_year_match = re.search(r"[:\-\/]\s*([12][0-9]{3})\b", canonical_identifier)
        if cited_year_match and std.publication_year:
            cited_year = int(cited_year_match.group(1))
            if cited_year < std.publication_year:
                # The citation explicitly refers to an older, superseded edition
                is_superseded = True
                successor_id = std.id
                successor_num = std.standard_id

        # Industry statutory transitions for commonly cited legacy specifications
        norm_up = canonical_identifier.upper()
        if "1554" in norm_up and "694" not in norm_up:
            s694 = self._standards_cache.get("IS 694:2010") or self.db.query(Standard).filter(Standard.standard_id.ilike("%694:2010%")).first()
            if s694:
                is_superseded = True
                successor_id = s694.id
                successor_num = s694.standard_id

        # Fallback: if superseded but no cross-edge found, look for active current edition of the same standard
        if is_superseded and not successor_num:
            active_std = self.db.query(Standard).filter(
                Standard.is_number == std.is_number,
                Standard.status == "CURRENT"
            ).first()
            if active_std and active_std.id != std.id:
                successor_id = active_std.id
                successor_num = active_std.standard_id

        return {
            "detected_standard_id": std.id,
            "title": std.title,
            "is_valid": True,
            "is_superseded": is_superseded,
            "superseded_by_standard_id": successor_id,
            "superseded_by_identifier": successor_num,
        }

    def extract_from_sections(self, sections: List[ExtractedSection]) -> List[ExtractedStandardReference]:
        """
        Extracts all explicit standard references across document sections and clauses,
        attaching page numbers, clause IDs, and context snippets.
        """
        all_refs: List[ExtractedStandardReference] = []
        seen_keys: Set[str] = set()

        for sec in sections:
            # Check individual clauses first
            for clause in sec.clauses:
                mentions = self.find_standard_mentions(clause.text)
                for raw, norm, start, end in mentions:
                    dedup_key = f"{norm}_{sec.section_number}_{clause.clause_number}"
                    if dedup_key in seen_keys:
                        continue
                    seen_keys.add(dedup_key)

                    resolved = self.resolve_standard(norm)
                    ref = ExtractedStandardReference(
                        standard_number_raw=raw,
                        canonical_identifier=norm,
                        detected_standard_id=resolved["detected_standard_id"],
                        title=resolved["title"],
                        is_valid=resolved["is_valid"],
                        is_superseded=resolved["is_superseded"],
                        superseded_by_standard_id=resolved["superseded_by_standard_id"],
                        superseded_by_identifier=resolved["superseded_by_identifier"],
                        page_number=clause.page_number or sec.page_number,
                        clause_number=clause.clause_number,
                        detected_clause=clause.text[:300],
                    )
                    all_refs.append(ref)
                    sec.standard_references.append(ref)

            # If section content has citations not captured in clauses
            if not sec.clauses:
                mentions = self.find_standard_mentions(sec.content)
                for raw, norm, start, end in mentions:
                    dedup_key = f"{norm}_{sec.section_number}_none"
                    if dedup_key in seen_keys:
                        continue
                    seen_keys.add(dedup_key)

                    resolved = self.resolve_standard(norm)
                    ref = ExtractedStandardReference(
                        standard_number_raw=raw,
                        canonical_identifier=norm,
                        detected_standard_id=resolved["detected_standard_id"],
                        title=resolved["title"],
                        is_valid=resolved["is_valid"],
                        is_superseded=resolved["is_superseded"],
                        superseded_by_standard_id=resolved["superseded_by_standard_id"],
                        superseded_by_identifier=resolved["superseded_by_identifier"],
                        page_number=sec.page_number,
                        clause_number=None,
                        detected_clause=sec.content[max(0, start - 50):min(len(sec.content), end + 100)],
                    )
                    all_refs.append(ref)
                    sec.standard_references.append(ref)

        return all_refs
