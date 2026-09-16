"""
Standard Reference Resolver for Module 4.
Safely resolves standard identifiers to database entities:
- Exact matches (canonical ID)
- Normalized whitespace/case matches
- Part-level matches
- Series-aware matching (identifies ambiguous base series vs single part)
- Unresolved references (genuinely absent standards)
Never collapses an ambiguous multi-part series into a false exact relationship.
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from backend.app.models.standard import Standard
from backend.app.core.normalizers import parse_standard_id, clean_text
from backend.app.services.knowledge_graph.graph_models import (
    StandardResolutionResult,
    MatchType,
)


class StandardReferenceResolver:
    """Safe standard identifier resolver grounded in the ingested database catalog."""

    def __init__(self, session: Session):
        self.session = session
        # In-memory index of standards for fast multi-part & prefix resolution
        self._load_standards_index()

    def _load_standards_index(self):
        """Loads index of all canonical standards in the database."""
        stds = self.session.query(Standard).all()
        self.by_id: Dict[int, Standard] = {s.id: s for s in stds}
        self.by_canonical: Dict[str, Standard] = {s.standard_id.strip().upper(): s for s in stds}
        
        # Group by is_number (e.g. 'IS 2386 (Part 1)' or base 'IS 2386')
        self.by_is_number: Dict[str, List[Standard]] = {}
        # Group by base prefix+number (e.g. 'IS 2386', 'IS 1367', 'IS 4031')
        self.by_base_is: Dict[str, List[Standard]] = {}

        for s in stds:
            is_num_clean = s.is_number.strip().upper()
            self.by_is_number.setdefault(is_num_clean, []).append(s)

            parsed = parse_standard_id(s.standard_id)
            if parsed and parsed.get("prefix") and parsed.get("number"):
                base_key = f"{parsed['prefix']} {parsed['number']}".upper()
                self.by_base_is.setdefault(base_key, []).append(s)

    def resolve(self, query_string: str) -> StandardResolutionResult:
        """
        Resolves an input identifier to a StandardResolutionResult.
        Distinguishes:
          - EXACT
          - PART
          - SERIES_AMBIGUOUS
          - UNRESOLVED
        """
        if not query_string or not clean_text(query_string):
            return StandardResolutionResult(
                query_string=query_string or "",
                match_type=MatchType.UNRESOLVED,
                is_ambiguous=False,
                details="Empty standard identifier query",
            )

        q_clean = query_string.strip()
        q_upper = q_clean.upper()

        # 1. Direct hit on canonical ID (e.g., 'IS 694:2010')
        if q_upper in self.by_canonical:
            s = self.by_canonical[q_upper]
            return StandardResolutionResult(
                query_string=query_string,
                match_type=MatchType.EXACT,
                canonical_id=s.standard_id,
                standard_id=str(s.id),
                matched_standards=[self._std_to_dict(s)],
                is_ambiguous=False,
                details=f"Exact match on canonical standard_id '{s.standard_id}'",
            )

        # 2. Parse using normalizer
        parsed = parse_standard_id(q_clean)
        if parsed:
            canon_candidate = parsed["canonical_id"].upper()
            if canon_candidate in self.by_canonical:
                s = self.by_canonical[canon_candidate]
                return StandardResolutionResult(
                    query_string=query_string,
                    match_type=MatchType.EXACT,
                    canonical_id=s.standard_id,
                    standard_id=str(s.id),
                    matched_standards=[self._std_to_dict(s)],
                    is_ambiguous=False,
                    details=f"Exact normalized match to canonical standard_id '{s.standard_id}'",
                )

            # Check if is_number with part matches directly (e.g., 'IS 1554 (Part 1)')
            is_num_candidate = parsed["is_number"].upper()
            if is_num_candidate in self.by_is_number:
                matches = self.by_is_number[is_num_candidate]
                if len(matches) == 1:
                    s = matches[0]
                    match_type = MatchType.PART if parsed.get("part") else MatchType.EXACT
                    return StandardResolutionResult(
                        query_string=query_string,
                        match_type=match_type,
                        canonical_id=s.standard_id,
                        standard_id=str(s.id),
                        matched_standards=[self._std_to_dict(s)],
                        is_ambiguous=False,
                        details=f"Unambiguous match on is_number '{s.is_number}'",
                    )
                elif len(matches) > 1:
                    # Multiple versions or parts with same is_number
                    return StandardResolutionResult(
                        query_string=query_string,
                        match_type=MatchType.SERIES_AMBIGUOUS,
                        matched_standards=[self._std_to_dict(s) for s in matches],
                        is_ambiguous=True,
                        details=f"Ambiguous match: {len(matches)} standards share is_number '{is_num_candidate}'",
                    )

            # Check if query is a base series citation without part (e.g., 'IS 2386', 'IS 4031')
            if not parsed.get("part") and parsed.get("prefix") and parsed.get("number"):
                base_key = f"{parsed['prefix']} {parsed['number']}".upper()
                if base_key in self.by_base_is:
                    matches = self.by_base_is[base_key]
                    if len(matches) == 1:
                        s = matches[0]
                        return StandardResolutionResult(
                            query_string=query_string,
                            match_type=MatchType.PART if s.part else MatchType.EXACT,
                            canonical_id=s.standard_id,
                            standard_id=str(s.id),
                            matched_standards=[self._std_to_dict(s)],
                            is_ambiguous=False,
                            details=f"Single standard matching base series '{base_key}'",
                        )
                    else:
                        # MULTIPLE PARTS EXIST IN DB -> MUST PRESERVE AMBIGUITY
                        return StandardResolutionResult(
                            query_string=query_string,
                            match_type=MatchType.SERIES_AMBIGUOUS,
                            matched_standards=[self._std_to_dict(s) for s in matches],
                            is_ambiguous=True,
                            details=(
                                f"Series-level citation '{base_key}' matches {len(matches)} specific parts in database: "
                                f"{[m.standard_id for m in matches]}. Preserving ambiguity to prevent false single-part binding."
                            ),
                        )

        # 3. Direct check on raw string in base_is
        if q_upper in self.by_base_is:
            matches = self.by_base_is[q_upper]
            if len(matches) == 1:
                s = matches[0]
                return StandardResolutionResult(
                    query_string=query_string,
                    match_type=MatchType.PART if s.part else MatchType.EXACT,
                    canonical_id=s.standard_id,
                    standard_id=str(s.id),
                    matched_standards=[self._std_to_dict(s)],
                    is_ambiguous=False,
                    details=f"Single standard matching base series '{q_upper}'",
                )
            else:
                return StandardResolutionResult(
                    query_string=query_string,
                    match_type=MatchType.SERIES_AMBIGUOUS,
                    matched_standards=[self._std_to_dict(s) for s in matches],
                    is_ambiguous=True,
                    details=f"Series-level citation '{q_upper}' matches {len(matches)} parts: {[m.standard_id for m in matches]}.",
                )

        # 4. Genuinely unresolved in supplied catalog
        return StandardResolutionResult(
            query_string=query_string,
            match_type=MatchType.UNRESOLVED,
            is_ambiguous=False,
            details=f"Standard '{query_string}' does not exist in supplied database catalog. Preserved as unresolved reference.",
        )

    def _std_to_dict(self, s: Standard) -> Dict[str, Any]:
        return {
            "id": s.id,
            "standard_id": s.standard_id,
            "is_number": s.is_number,
            "part": s.part,
            "section": s.section,
            "year": s.publication_year,
            "title": s.title,
            "status": s.status,
            "category": s.category,
        }
