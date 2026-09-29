"""
Adversarial Auditor AI Service.

A dedicated "second opinion" AI whose sole purpose is to aggressively
double-check every Indian Standard reference for:

1. EXISTENCE: Does the standard number actually exist in the BIS dataset?
2. FORMAT: Is the standard number syntactically valid (IS XXXX:YYYY format)?
3. CURRENCY: Is it the current edition or has it been superseded?
4. PLAUSIBILITY: For numbers not in the dataset, does a close match exist
   (possible typo) or is it completely fabricated?

This prevents AI hallucination — where an LLM confidently invents
fake standard numbers like "IS 9999" that don't exist.

In government procurement, a fake standard number can cause
major legal trouble. This auditor BLOCKS suspicious references.
"""
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from difflib import SequenceMatcher
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.models.standard import Standard
from backend.app.services.tender_engine.standard_extractor import StandardExtractor
from backend.app.services.adversarial_auditor.schemas import (
    VerificationVerdict,
    VerifiedStandard,
    AuditVerificationRequest,
    AuditVerificationResponse,
)

logger = logging.getLogger(__name__)

# Valid IS number format: IS followed by 1-5 digit number, optional part, optional year
IS_FORMAT_REGEX = re.compile(
    r"^(?:IS|I\.S\.)[\s:.\-]*(\d{1,5})(?:\s*\([^)]*\))?(?:\s*[:\-/]\s*\d{4})?$",
    re.IGNORECASE,
)


class AdversarialAuditorService:
    """
    Aggressively verifies standard references against the authoritative
    BIS database. Flags hallucinations and suspicious references.
    """

    # Thresholds for fuzzy matching
    EXACT_MATCH_THRESHOLD = 0.95
    PARTIAL_MATCH_THRESHOLD = 0.70
    SUSPICIOUS_THRESHOLD = 0.50

    def __init__(self, db_session: Session):
        self.db = db_session
        self.extractor = StandardExtractor(db_session)
        self._all_standards_cache: Optional[List[Dict[str, Any]]] = None

    def verify(self, request: AuditVerificationRequest) -> AuditVerificationResponse:
        """
        Main entry: verifies a list of standard references.
        Each reference gets an independent adversarial verdict.
        """
        results: List[VerifiedStandard] = []

        for ref_str in request.references:
            result = self._verify_single(
                ref_str,
                strict=request.strict_mode,
                include_closest=request.include_closest_matches,
            )
            results.append(result)

        # Compute aggregate metrics
        verified = sum(1 for r in results if r.verdict == VerificationVerdict.VERIFIED)
        superseded_verified = sum(1 for r in results if r.verdict == VerificationVerdict.SUPERSEDED_VERIFIED)
        suspicious = sum(1 for r in results if r.verdict == VerificationVerdict.SUSPICIOUS)
        hallucinated = sum(1 for r in results if r.verdict == VerificationVerdict.HALLUCINATION)
        partial = sum(1 for r in results if r.verdict == VerificationVerdict.PARTIAL_MATCH)
        format_invalid = sum(1 for r in results if r.verdict == VerificationVerdict.FORMAT_INVALID)
        blocked = sum(1 for r in results if r.blocked)

        total = len(results)
        trust_score = round((verified + superseded_verified) / max(1, total), 2)

        # Generate auditor warning if needed
        warning = None
        if hallucinated > 0:
            warning = (
                f"🚨 AUDITOR ALERT: {hallucinated} reference(s) appear to be FABRICATED. "
                f"These standard numbers do not exist in any verified BIS dataset. "
                f"DO NOT use them in official documents. Verify manually."
            )
        elif suspicious > 0:
            warning = (
                f"⚠️ AUDITOR NOTICE: {suspicious} reference(s) could not be fully confirmed. "
                f"These may contain typos or refer to withdrawn standards. "
                f"Please verify manually before use."
            )

        return AuditVerificationResponse(
            total_checked=total,
            verified_count=verified + superseded_verified,
            suspicious_count=suspicious + partial,
            hallucination_count=hallucinated + format_invalid,
            blocked_count=blocked,
            results=results,
            overall_trust_score=trust_score,
            auditor_warning=warning,
        )

    def _verify_single(
        self,
        ref_str: str,
        strict: bool = True,
        include_closest: bool = True,
    ) -> VerifiedStandard:
        """Adversarially verifies a single standard reference."""
        cleaned = ref_str.strip()
        normalized = self.extractor._clean_number(cleaned)

        # STEP 1: Validate format
        if not self._is_valid_format(cleaned):
            return VerifiedStandard(
                input_reference=ref_str,
                normalized_reference=normalized,
                verdict=VerificationVerdict.FORMAT_INVALID,
                confidence=0.95,
                reason=(
                    f"'{ref_str}' does not match any valid Indian Standard format. "
                    f"Expected format: 'IS XXXX:YYYY' (e.g., IS 12615:2018)."
                ),
                blocked=True,
                evidence={"check": "format_validation", "pattern": "IS XXXX:YYYY"},
            )

        # STEP 2: Try exact resolution via StandardExtractor
        resolution = self.extractor.resolve_standard(normalized)

        if resolution.get("is_valid") and resolution.get("detected_standard_id"):
            std_id = resolution["detected_standard_id"]
            title = resolution.get("title", "")
            is_superseded = resolution.get("is_superseded", False)
            successor = resolution.get("superseded_by_identifier")

            if is_superseded:
                return VerifiedStandard(
                    input_reference=ref_str,
                    normalized_reference=normalized,
                    verdict=VerificationVerdict.SUPERSEDED_VERIFIED,
                    confidence=1.0,
                    matched_standard_id=normalized,
                    matched_title=title,
                    matched_status="SUPERSEDED",
                    successor_id=successor,
                    reason=(
                        f"✅ Standard '{normalized}' EXISTS in the BIS database but is SUPERSEDED. "
                        f"It has been replaced by {successor or 'a newer edition'}."
                    ),
                    blocked=False,
                    evidence={
                        "check": "exact_match",
                        "database_id": std_id,
                        "status": "SUPERSEDED",
                        "successor": successor,
                    },
                )

            return VerifiedStandard(
                input_reference=ref_str,
                normalized_reference=normalized,
                verdict=VerificationVerdict.VERIFIED,
                confidence=1.0,
                matched_standard_id=normalized,
                matched_title=title,
                matched_status="CURRENT",
                reason=f"✅ Standard '{normalized}' is VERIFIED — exists and is current in the BIS database.",
                blocked=False,
                evidence={
                    "check": "exact_match",
                    "database_id": std_id,
                    "status": "CURRENT",
                },
            )

        # STEP 3: Not found — look for close matches (possible typos or hallucinations)
        closest = self._find_closest_matches(normalized, top_k=3) if include_closest else []

        if closest:
            best_score = closest[0]["similarity"]

            if best_score >= self.PARTIAL_MATCH_THRESHOLD:
                return VerifiedStandard(
                    input_reference=ref_str,
                    normalized_reference=normalized,
                    verdict=VerificationVerdict.PARTIAL_MATCH,
                    confidence=round(1.0 - best_score, 2),
                    closest_matches=closest,
                    reason=(
                        f"🟠 Standard '{normalized}' was NOT found, but similar standards exist: "
                        f"{', '.join(m['standard_id'] for m in closest[:2])}. "
                        f"This may be a typo. Please verify and correct."
                    ),
                    blocked=strict,
                    evidence={
                        "check": "fuzzy_match",
                        "best_match": closest[0]["standard_id"],
                        "similarity": best_score,
                    },
                )

            if best_score >= self.SUSPICIOUS_THRESHOLD:
                return VerifiedStandard(
                    input_reference=ref_str,
                    normalized_reference=normalized,
                    verdict=VerificationVerdict.SUSPICIOUS,
                    confidence=round(1.0 - best_score, 2),
                    closest_matches=closest,
                    reason=(
                        f"🟡 Standard '{normalized}' was NOT found in the BIS database. "
                        f"Some distant matches exist but confidence is low. "
                        f"I am NOT 100% sure — please check this manually."
                    ),
                    blocked=strict,
                    evidence={
                        "check": "fuzzy_match_weak",
                        "best_match": closest[0]["standard_id"],
                        "similarity": best_score,
                    },
                )

        # STEP 4: Complete hallucination — no close matches at all
        return VerifiedStandard(
            input_reference=ref_str,
            normalized_reference=normalized,
            verdict=VerificationVerdict.HALLUCINATION,
            confidence=0.95,
            closest_matches=closest,
            reason=(
                f"🔴 HALLUCINATION DETECTED: Standard '{normalized}' does NOT exist "
                f"in any verified BIS dataset. This number appears to be fabricated. "
                f"DO NOT use this reference in any official procurement document."
            ),
            blocked=True,
            evidence={
                "check": "no_match",
                "database_searched": True,
                "total_standards_in_db": self._get_standards_count(),
            },
        )

    def _is_valid_format(self, ref_str: str) -> bool:
        """Checks if a reference string has a plausible IS format."""
        cleaned = ref_str.strip()
        # Allow IS prefix variations
        if not re.match(r"^(?:IS|I\.S\.)", cleaned, re.IGNORECASE):
            # Try adding IS prefix and checking
            cleaned = f"IS {cleaned}"
        return bool(IS_FORMAT_REGEX.match(cleaned))

    def _find_closest_matches(
        self, normalized_ref: str, top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Finds the closest matching standards in the database using
        string similarity on standard_id / is_number.
        """
        if self._all_standards_cache is None:
            self._load_standards_cache()

        # Extract just the numeric portion for comparison
        ref_num = self._extract_number(normalized_ref)
        matches = []

        for std in self._all_standards_cache:
            std_num = self._extract_number(std["standard_id"])
            # Compute similarity on the numeric portion
            sim = SequenceMatcher(None, ref_num, std_num).ratio()
            if sim >= 0.3:  # Lower bound for relevance
                matches.append({
                    "standard_id": std["standard_id"],
                    "title": std["title"],
                    "status": std["status"],
                    "similarity": round(sim, 3),
                })

        # Sort by similarity descending
        matches.sort(key=lambda x: x["similarity"], reverse=True)
        return matches[:top_k]

    def _extract_number(self, std_id: str) -> str:
        """Extracts just the numeric portion from a standard ID."""
        nums = re.findall(r"\d+", std_id)
        return "".join(nums)

    def _load_standards_cache(self):
        """Loads all standards into memory for fuzzy matching."""
        standards = self.db.query(Standard).all()
        self._all_standards_cache = [
            {
                "standard_id": s.standard_id or s.is_number,
                "title": s.title,
                "status": getattr(s, "status", "UNKNOWN"),
            }
            for s in standards
        ]

    def _get_standards_count(self) -> int:
        """Returns the total count of standards in the database."""
        try:
            return self.db.query(func.count(Standard.id)).scalar() or 0
        except Exception:
            return 0
