"""
Redline Document Analysis Service.
Scans tender document text, identifies every Indian Standard citation,
resolves it against the verified BIS database, and returns annotated
segments with inline compliance markers:

- GREEN (COMPLIANT): Current, valid standard reference.
- RED (OUTDATED): Superseded/expired standard with auto-fix to successor.
- ORANGE (UNRECOGNIZED): Standard number not found in verified BIS dataset.
- YELLOW (AMENDED): Current standard but has published amendments.

Reuses the proven StandardExtractor regex and resolution logic
from Module 11 (Tender Engine).
"""
import re
import logging
import hashlib
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session

from backend.app.models.standard import Standard
from backend.app.services.tender_engine.standard_extractor import StandardExtractor
from backend.app.services.version_intelligence import VersionIntelligenceService, WarningType
from backend.app.services.redline.schemas import (
    AnnotationType,
    AutoFixAction,
    RedlineSegment,
    RedlineAnalysisRequest,
    RedlineAnalysisResponse,
    RedlineSummary,
)

logger = logging.getLogger(__name__)


class RedlineService:
    """Produces a visually annotated redline markup of tender documents."""

    def __init__(self, db_session: Session):
        self.db = db_session
        self.extractor = StandardExtractor(db_session)
        self.version_service = VersionIntelligenceService(db_session)

    def analyze(self, request: RedlineAnalysisRequest) -> RedlineAnalysisResponse:
        """
        Main entry point: analyzes document text and returns annotated segments.
        Each standard citation becomes its own segment with compliance metadata;
        surrounding plain text is preserved as PLAIN segments.
        """
        text = request.document_text
        # Find all standard mentions with character positions
        mentions = self._find_all_mentions(text)

        segments: List[RedlineSegment] = []
        auto_fixes: List[AutoFixAction] = []
        seg_id = 0
        prev_end = 0

        for raw_match, norm_id, start, end in mentions:
            # Emit plain text segment before this citation
            if start > prev_end:
                plain_text = text[prev_end:start]
                if plain_text.strip():
                    segments.append(RedlineSegment(
                        segment_id=seg_id,
                        text=plain_text,
                        annotation_type=AnnotationType.PLAIN,
                    ))
                    seg_id += 1

            # Resolve the standard reference
            resolution = self.extractor.resolve_standard(norm_id)
            anno_segment = self._build_annotated_segment(
                seg_id=seg_id,
                raw_text=text[start:end],
                norm_id=norm_id,
                resolution=resolution,
            )
            segments.append(anno_segment)

            # Build auto-fix if outdated
            if anno_segment.annotation_type == AnnotationType.OUTDATED and anno_segment.successor_id:
                fix = self._build_auto_fix(
                    raw_text=text[start:end],
                    old_std_id=norm_id,
                    successor_id=anno_segment.successor_id,
                    successor_title=anno_segment.successor_title,
                    successor_year=anno_segment.successor_year,
                    old_year=anno_segment.publication_year,
                )
                anno_segment.auto_fix = fix
                auto_fixes.append(fix)

            seg_id += 1
            prev_end = end

        # Emit trailing plain text
        if prev_end < len(text):
            trailing = text[prev_end:]
            if trailing.strip():
                segments.append(RedlineSegment(
                    segment_id=seg_id,
                    text=trailing,
                    annotation_type=AnnotationType.PLAIN,
                ))

        # Build summary
        summary = self._compute_summary(segments, auto_fixes)

        # Build corrected text if requested
        corrected_text = None
        if request.auto_fix_all and auto_fixes:
            corrected_text = self._apply_all_fixes(text, auto_fixes)

        return RedlineAnalysisResponse(
            segments=segments,
            summary=summary,
            corrected_text=corrected_text,
            auto_fixes=auto_fixes,
        )

    def apply_single_fix(self, document_text: str, fix_id: str, auto_fixes: List[AutoFixAction]) -> str:
        """Applies a single auto-fix by fix_id and returns corrected text."""
        for fix in auto_fixes:
            if fix.fix_id == fix_id:
                return document_text.replace(fix.old_text, fix.new_text, 1)
        return document_text

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _find_all_mentions(self, text: str) -> List[Tuple[str, str, int, int]]:
        """
        Finds all IS citations with their character offsets.
        Returns list of (raw_match, normalized_id, start_pos, end_pos)
        sorted by start position.
        """
        mentions = []
        seen_spans = set()

        for pat in self.extractor.IS_PATTERNS:
            for m in pat.finditer(text):
                span_key = (m.start(), m.end())
                if span_key in seen_spans:
                    continue
                seen_spans.add(span_key)
                raw = m.group(0).strip()
                norm = self.extractor._clean_number(raw)
                mentions.append((raw, norm, m.start(), m.end()))

        # Sort by position to maintain document order
        mentions.sort(key=lambda x: x[2])
        return mentions

    def _build_annotated_segment(
        self,
        seg_id: int,
        raw_text: str,
        norm_id: str,
        resolution: Dict[str, Any],
    ) -> RedlineSegment:
        """
        Creates an annotated segment for a single standard citation.
        Checks version currency via VersionIntelligenceService.
        """
        std_id_db = resolution.get("detected_standard_id")
        title = resolution.get("title")
        is_valid = resolution.get("is_valid", False)
        is_superseded = resolution.get("is_superseded", False)
        successor_std_id = resolution.get("superseded_by_identifier")

        # Not found in database
        if not is_valid or not std_id_db:
            return RedlineSegment(
                segment_id=seg_id,
                text=raw_text,
                annotation_type=AnnotationType.UNRECOGNIZED,
                standard_id=norm_id,
                tooltip=f"⚠ Standard '{norm_id}' was not found in the verified BIS dataset. Please verify manually.",
                evidence={"resolution": "NOT_IN_DATASET"},
            )

        # Superseded — RED
        if is_superseded:
            successor_title = None
            successor_year = None
            if successor_std_id:
                succ_std = self.db.query(Standard).filter(
                    (Standard.standard_id == successor_std_id) |
                    (Standard.is_number == successor_std_id)
                ).first()
                if succ_std:
                    successor_title = succ_std.title
                    successor_year = succ_std.publication_year

            pub_year = self._get_pub_year(std_id_db)
            return RedlineSegment(
                segment_id=seg_id,
                text=raw_text,
                annotation_type=AnnotationType.OUTDATED,
                standard_id=norm_id,
                standard_title=title,
                status="SUPERSEDED",
                publication_year=pub_year,
                successor_id=successor_std_id,
                successor_title=successor_title,
                successor_year=successor_year,
                tooltip=(
                    f"🔴 WARNING: {norm_id} is SUPERSEDED. "
                    f"Replaced by {successor_std_id or 'a newer edition'}. "
                    f"Click 'Auto-Fix' to update automatically."
                ),
                evidence={
                    "status": "SUPERSEDED",
                    "source": "Module 4 Version Intelligence",
                },
            )

        # Check for amendments via version intelligence
        try:
            currency = self.version_service.check_currency(std_id_db)
            has_amendments = currency.total_amendments > 0

            if not currency.is_current:
                # Version intelligence says not current even though not explicitly SUPERSEDED
                successor_from_vi = None
                successor_title_vi = None
                successor_year_vi = None
                for w in currency.warnings:
                    if w.warning_type == WarningType.SUPERSEDED_WARNING:
                        succs = w.evidence.get("successors", [])
                        if succs:
                            successor_from_vi = succs[0].get("canonical_id") or str(succs[0].get("standard_id"))
                            successor_title_vi = succs[0].get("title")

                if successor_from_vi:
                    succ_std = self.db.query(Standard).filter(
                        (Standard.standard_id == successor_from_vi) |
                        (Standard.is_number == successor_from_vi)
                    ).first()
                    if succ_std:
                        successor_year_vi = succ_std.publication_year

                return RedlineSegment(
                    segment_id=seg_id,
                    text=raw_text,
                    annotation_type=AnnotationType.OUTDATED,
                    standard_id=norm_id,
                    standard_title=title,
                    status="NOT_CURRENT",
                    publication_year=currency.publication_year,
                    successor_id=successor_from_vi,
                    successor_title=successor_title_vi,
                    successor_year=successor_year_vi,
                    tooltip=(
                        f"🔴 WARNING: {norm_id} is no longer the current edition. "
                        f"Updated to {successor_from_vi or 'a newer version'}."
                    ),
                    evidence={"status": currency.status, "source": "Version Intelligence"},
                )

            if has_amendments:
                return RedlineSegment(
                    segment_id=seg_id,
                    text=raw_text,
                    annotation_type=AnnotationType.AMENDED,
                    standard_id=norm_id,
                    standard_title=title,
                    status="CURRENT",
                    publication_year=currency.publication_year,
                    amendments_count=currency.total_amendments,
                    tooltip=(
                        f"🟡 {norm_id} is current but has {currency.total_amendments} "
                        f"published amendment(s). Ensure all amendments are incorporated."
                    ),
                    evidence={"amendments": currency.total_amendments, "status": "CURRENT"},
                )

        except Exception as e:
            logger.debug("Version check for %s skipped: %s", norm_id, e)

        # Fully current — GREEN
        pub_year = self._get_pub_year(std_id_db)
        return RedlineSegment(
            segment_id=seg_id,
            text=raw_text,
            annotation_type=AnnotationType.COMPLIANT,
            standard_id=norm_id,
            standard_title=title,
            status="CURRENT",
            publication_year=pub_year,
            tooltip=f"✅ {norm_id} is the current, valid Indian Standard. Fully compliant.",
            evidence={"status": "CURRENT", "source": "Verified BIS Dataset"},
        )

    def _get_pub_year(self, std_db_id: int) -> Optional[int]:
        """Extracts publication year from standard record."""
        std = self.db.query(Standard).filter(Standard.id == std_db_id).first()
        if std:
            return getattr(std, "publication_year", None)
        return None

    def _build_auto_fix(
        self,
        raw_text: str,
        old_std_id: str,
        successor_id: str,
        successor_title: Optional[str],
        successor_year: Optional[int],
        old_year: Optional[int],
    ) -> AutoFixAction:
        """Creates an auto-fix action to replace an outdated reference."""
        fix_hash = hashlib.md5(f"{old_std_id}:{successor_id}".encode()).hexdigest()[:8]
        return AutoFixAction(
            fix_id=f"fix_{fix_hash}",
            old_text=raw_text,
            new_text=successor_id,
            old_standard_id=old_std_id,
            new_standard_id=successor_id,
            new_standard_title=successor_title,
            reason=(
                f"Standard {old_std_id} (published {old_year or '?'}) has been superseded by "
                f"{successor_id} ({successor_title or 'current edition'}, "
                f"published {successor_year or 'latest'})."
            ),
            year_old=old_year,
            year_new=successor_year,
            confidence=1.0,
        )

    def _apply_all_fixes(self, text: str, auto_fixes: List[AutoFixAction]) -> str:
        """Applies all auto-fix replacements to the document text."""
        corrected = text
        for fix in auto_fixes:
            corrected = corrected.replace(fix.old_text, fix.new_text, 1)
        return corrected

    def _compute_summary(
        self,
        segments: List[RedlineSegment],
        auto_fixes: List[AutoFixAction],
    ) -> RedlineSummary:
        """Computes aggregate statistics for the redline analysis."""
        compliant = sum(1 for s in segments if s.annotation_type == AnnotationType.COMPLIANT)
        outdated = sum(1 for s in segments if s.annotation_type == AnnotationType.OUTDATED)
        unrecognized = sum(1 for s in segments if s.annotation_type == AnnotationType.UNRECOGNIZED)
        amended = sum(1 for s in segments if s.annotation_type == AnnotationType.AMENDED)
        total_refs = compliant + outdated + unrecognized + amended

        if total_refs == 0:
            score = 1.0
        else:
            score = round((compliant + amended) / total_refs, 2)

        return RedlineSummary(
            total_segments=len(segments),
            compliant_count=compliant,
            outdated_count=outdated,
            unrecognized_count=unrecognized,
            amended_count=amended,
            auto_fixes_available=len(auto_fixes),
            compliance_score=score,
        )
