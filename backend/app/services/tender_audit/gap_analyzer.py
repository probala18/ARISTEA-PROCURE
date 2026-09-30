"""
Tender Gap Analyzer (Module 12).
Implements the core audit pipeline:
Tender Document → Extracted Requirements → Existing Standard References
→ Semantic Recommendation → Version Intelligence → Compliance Intelligence
→ Gap Detection → Evidence-Based Audit.

Strictly follows Section 83 Trust Model:
- KNOWN (explicitly present in tender)
- INFERRED (suggested by retrieval, recommendation, or graph)
- UNKNOWN (unestablished by available evidence)
"""
import logging
from typing import List, Dict, Any, Set, Optional
from sqlalchemy.orm import Session

from backend.app.models.standard import Standard
from backend.app.models.tender import (
    TenderDocument,
    TenderRequirement,
    TenderStandardReference,
)
from backend.app.services.recommendation import (
    RecommendationRequest,
    RecommendationEngine,
)
from backend.app.services.version_intelligence import VersionIntelligenceService, WarningType
from backend.app.services.compliance_intelligence import (
    ComplianceIntelligenceService,
    RequirementLevel,
)
from backend.app.services.relationship_engine import RelationshipEngine
from backend.app.services.tender_audit.schemas import (
    GapSeverity,
    GapCategory,
    TrustLevel,
    TenderGapItem,
    ExpectedVsPresentComparison,
    TenderAuditReport,
)

logger = logging.getLogger(__name__)


class TenderGapAnalyzer:
    """Evaluates tender documents against authoritative BIS standards, graph relationships, and compliance mandates."""

    def __init__(self, db_session: Session):
        self.db = db_session
        self.version_service = VersionIntelligenceService(db_session)
        self.compliance_service = ComplianceIntelligenceService(db_session)
        self.relationship_engine = RelationshipEngine(db_session)
        self.recommendation_engine = RecommendationEngine(db_session)

    def analyze_tender(self, tender: TenderDocument) -> TenderAuditReport:
        """Executes full evidence-based gap analysis on a parsed tender document."""
        gaps: List[TenderGapItem] = []

        present_standards_data: List[Dict[str, Any]] = []
        expected_standards_data: List[Dict[str, Any]] = []
        missing_standards_data: List[Dict[str, Any]] = []
        outdated_standards_data: List[Dict[str, Any]] = []
        testing_gaps_data: List[Dict[str, Any]] = []
        safety_gaps_data: List[Dict[str, Any]] = []
        certification_gaps_data: List[Dict[str, Any]] = []

        # Collect present standard IDs and normalized strings
        present_refs = self.db.query(TenderStandardReference).filter(
            TenderStandardReference.tender_id == tender.id
        ).all()

        present_std_ids: Set[int] = {r.detected_standard_id for r in present_refs if r.detected_standard_id}
        present_clean_numbers: Set[str] = {
            r.standard_number_raw.upper().replace(" ", "") for r in present_refs if r.standard_number_raw
        }

        # ---------------------------------------------------------------------
        # 1. EVALUATE PRESENT EXPLICIT STANDARD CITATIONS (KNOWN)
        # ---------------------------------------------------------------------
        for ref in present_refs:
            raw_num = ref.standard_number_raw
            std = self.db.query(Standard).filter(Standard.id == ref.detected_standard_id).first() if ref.detected_standard_id else None

            if not std:
                # Unlisted or unrecognized standard reference
                present_standards_data.append({
                    "raw_number": raw_num,
                    "canonical_id": raw_num,
                    "is_resolved": False,
                    "status": "UNRECOGNIZED_IN_DATASET",
                    "trust_level": TrustLevel.KNOWN.value,
                })
                gaps.append(TenderGapItem(
                    gap_category=GapCategory.COMPLIANCE_EVIDENCE_MISSING,
                    severity=GapSeverity.ADVISORY,
                    trust_level=TrustLevel.UNKNOWN,
                    standard_id=raw_num,
                    clause_reference=None,
                    clause_text=ref.detected_clause,
                    issue_description=f"Standard reference '{raw_num}' is cited but not found in the local BIS registry.",
                    recommendation="Verify standard existence against current BIS catalogue.",
                    evidence={"unresolved_reference": raw_num},
                ))
                continue

            std_num = std.standard_id or std.is_number
            std_title = std.title

            # Check Currency & Supersession via Version Intelligence and Extracted Reference
            currency = self.version_service.check_currency(std.id)
            is_outdated = (currency.status == "SUPERSEDED") or (not currency.is_current) or bool(ref.is_superseded)

            successor_id = None
            successor_title = None
            for w in currency.warnings:
                if w.warning_type == WarningType.SUPERSEDED_WARNING:
                    succs = w.evidence.get("successors", [])
                    if succs:
                        successor_id = succs[0].get("canonical_id") or str(succs[0].get("standard_id"))
                        successor_title = succs[0].get("title")

            if not successor_id and ref.superseded_by_standard_id:
                succ_std = self.db.query(Standard).filter(Standard.id == ref.superseded_by_standard_id).first()
                if succ_std:
                    successor_id = succ_std.standard_id
                    successor_title = succ_std.title

            present_standards_data.append({
                "standard_id": std.id,
                "canonical_id": ref.standard_number_raw or std_num,
                "title": std_title,
                "is_resolved": True,
                "status": "SUPERSEDED" if is_outdated else currency.status,
                "publication_year": currency.publication_year,
                "latest_year": currency.latest_year,
                "successor": successor_id,
                "trust_level": TrustLevel.KNOWN.value,
            })

            if is_outdated:
                outdated_info = {
                    "standard_id": ref.standard_number_raw or std_num,
                    "title": std_title,
                    "status": "SUPERSEDED",
                    "successor_id": successor_id,
                    "successor_title": successor_title,
                    "clause_text": ref.detected_clause,
                }
                outdated_standards_data.append(outdated_info)

                gaps.append(TenderGapItem(
                    gap_category=GapCategory.OUTDATED_REFERENCE,
                    severity=GapSeverity.CRITICAL,
                    trust_level=TrustLevel.KNOWN,
                    standard_id=ref.standard_number_raw or std_num,
                    title=std_title,
                    clause_reference=None,
                    clause_text=ref.detected_clause,
                    successor_standard_id=successor_id,
                    successor_title=successor_title,
                    issue_description=(
                        f"Tender explicitly references outdated/superseded standard {ref.standard_number_raw or std_num}. "
                        f"This standard has been superseded by {successor_id or 'a current edition'}."
                    ),
                    recommendation=(
                        f"Replace outdated reference {ref.standard_number_raw or std_num} with current successor {successor_id or 'current standard'} "
                        f"({successor_title or 'current edition'})."
                    ),
                    evidence={
                        "cited_status": "SUPERSEDED" if is_outdated else std.status,
                        "successor_chain": successor_id,
                        "source_provenance": "Module 4 Knowledge Graph explicit supersession",
                    }
                ))
            else:
                # Check for available amendments
                if currency.total_amendments > 0:
                    gaps.append(TenderGapItem(
                        gap_category=GapCategory.SUFFICIENT_EVIDENCE,
                        severity=GapSeverity.INFO,
                        trust_level=TrustLevel.KNOWN,
                        standard_id=std_num,
                        title=std_title,
                        issue_description=f"Standard {std_num} is current with {currency.total_amendments} published amendments.",
                        recommendation="Ensure procurement specifications incorporate all published amendments.",
                        evidence={"amendments_count": currency.total_amendments},
                    ))

            # Check Compliance Intelligence (QCO & Certification Mandates)
            compliance = self.compliance_service.evaluate_compliance(std.id)
            if compliance and compliance.requirement_level == RequirementLevel.MANDATORY:
                # Tender cited a mandatory standard — verify if clause enforces certification
                clause_lower = (ref.detected_clause or "").lower()
                has_cert_mention = any(k in clause_lower for k in ["certif", "qco", "isi", "mandatory", "licence", "license"])
                
                if not has_cert_mention:
                    schemes_list = [compliance.governing_scheme] if compliance.governing_scheme else []
                    cert_gap_info = {
                        "standard_id": std_num,
                        "title": std_title,
                        "requirement_level": "MANDATORY",
                        "qco_enforced": compliance.qco_applicable,
                        "schemes": schemes_list,
                    }
                    certification_gaps_data.append(cert_gap_info)
                    gaps.append(TenderGapItem(
                        gap_category=GapCategory.CERTIFICATION_GAP,
                        severity=GapSeverity.WARNING,
                        trust_level=TrustLevel.KNOWN,
                        standard_id=std_num,
                        title=std_title,
                        clause_text=ref.detected_clause,
                        issue_description=(
                            f"Standard {std_num} is subject to MANDATORY BIS certification under Quality Control Orders, "
                            f"but the tender clause does not explicitly mandate valid BIS certification/licence."
                        ),
                        recommendation=(
                            f"Add an explicit compliance requirement: 'Bidders must possess valid BIS Certification / Licence "
                            f"for {std_num} as per applicable QCO.'"
                        ),
                        evidence={
                            "qco_enforced": compliance.qco_applicable,
                            "schemes": schemes_list,
                        }
                    ))

            # Check Knowledge Graph Allied Standards (Testing & Safety)
            allied_group = self.relationship_engine.get_allied_standards(std.id)
            if allied_group:
                for item in allied_group.testing:
                    allied_id = item.standard_number or item.standard_id
                    if not allied_id:
                        continue
                    clean_allied = allied_id.upper().replace(" ", "")
                    if clean_allied not in present_clean_numbers and (not item.standard_id or item.standard_id not in present_std_ids):
                        t_info = {
                            "primary_standard": std_num,
                            "allied_standard_id": allied_id,
                            "allied_title": item.title,
                            "relationship": item.relationship_type or "TESTING",
                        }
                        testing_gaps_data.append(t_info)
                        gaps.append(TenderGapItem(
                            gap_category=GapCategory.POTENTIALLY_MISSING_TESTING_STANDARD,
                            severity=GapSeverity.ADVISORY,
                            trust_level=TrustLevel.INFERRED,
                            standard_id=allied_id,
                            title=item.title,
                            issue_description=(
                                f"Tender cites {std_num}, but omits allied testing standard {allied_id} "
                                f"({item.title or 'Testing standard'}) connected in the knowledge graph."
                            ),
                            recommendation=(
                                f"Consider stipulating test methods in accordance with {allied_id} "
                                f"for acceptance testing."
                            ),
                            evidence={"governing_standard": std_num, "graph_edge": item.relationship_type or "TESTING"},
                        ))

                for item in allied_group.safety:
                    allied_id = item.standard_number or item.standard_id
                    if not allied_id:
                        continue
                    clean_allied = allied_id.upper().replace(" ", "")
                    if clean_allied not in present_clean_numbers and (not item.standard_id or item.standard_id not in present_std_ids):
                        s_info = {
                            "primary_standard": std_num,
                            "allied_standard_id": allied_id,
                            "allied_title": item.title,
                            "relationship": item.relationship_type or "SAFETY",
                        }
                        safety_gaps_data.append(s_info)
                        gaps.append(TenderGapItem(
                            gap_category=GapCategory.POTENTIALLY_MISSING_SAFETY_STANDARD,
                            severity=GapSeverity.WARNING,
                            trust_level=TrustLevel.INFERRED,
                            standard_id=allied_id,
                            title=item.title,
                            issue_description=(
                                f"Tender cites {std_num}, but omits normative safety standard {allied_id} "
                                f"({item.title or 'Safety standard'})."
                            ),
                            recommendation=(
                                f"Include explicit safety compliance clause referencing {allied_id}."
                            ),
                            evidence={"governing_standard": std_num, "graph_edge": item.relationship_type or "SAFETY"},
                        ))

        # ---------------------------------------------------------------------
        # 2. EVALUATE UNGROUNDED TECHNICAL REQUIREMENTS (INFERRED)
        # ---------------------------------------------------------------------
        reqs = self.db.query(TenderRequirement).filter(
            TenderRequirement.tender_id == tender.id
        ).all()

        seen_recommended_standards: Set[str] = set()

        for req in reqs:
            # Check if this requirement has technical attributes or product keywords
            if not req.product_keywords and not req.technical_attributes:
                continue

            # Run semantic recommendation
            rec_result = self.recommendation_engine.recommend(
                RecommendationRequest(query_text=req.requirement_text, max_primary=2, include_allied=False)
            )

            if rec_result.is_out_of_scope:
                continue

            if rec_result.is_ambiguous:
                gaps.append(TenderGapItem(
                    gap_category=GapCategory.AMBIGUOUS_SPECIFICATION,
                    severity=GapSeverity.ADVISORY,
                    trust_level=TrustLevel.INFERRED,
                    clause_text=req.requirement_text,
                    issue_description=(
                        "Requirement is technically broad or ambiguous. Multiple distinct standards could apply."
                    ),
                    recommendation=(
                        rec_result.clarification_prompt.explanation if rec_result.clarification_prompt
                        else "Clarify operating voltage, material grade, or application scope."
                    ),
                    evidence={"ambiguity_signals": req.product_keywords},
                ))
                continue

            # Check primary candidates against present citations
            for candidate in rec_result.primary_standards:
                cand_num = candidate.standard_id or candidate.is_number
                clean_cand = cand_num.upper().replace(" ", "")

                expected_standards_data.append({
                    "standard_id": cand_num,
                    "title": candidate.title,
                    "confidence_score": candidate.confidence_score,
                    "relevance_score": candidate.relevance_score,
                    "trust_level": TrustLevel.INFERRED.value,
                })

                if clean_cand not in present_clean_numbers and candidate.id not in present_std_ids:
                    if clean_cand in seen_recommended_standards:
                        continue
                    seen_recommended_standards.add(clean_cand)

                    # Verified missing reference gap
                    is_mand = bool(candidate.compliance_note and "MANDATORY" in candidate.compliance_note.upper())
                    sev = GapSeverity.CRITICAL if is_mand else GapSeverity.WARNING

                    missing_standards_data.append({
                        "standard_id": cand_num,
                        "title": candidate.title,
                        "confidence_score": candidate.confidence_score,
                        "is_mandatory": is_mand,
                        "clause_text": req.requirement_text,
                    })

                    gaps.append(TenderGapItem(
                        gap_category=GapCategory.MISSING_REFERENCE,
                        severity=sev,
                        trust_level=TrustLevel.INFERRED,
                        standard_id=cand_num,
                        title=candidate.title,
                        clause_text=req.requirement_text,
                        issue_description=(
                            f"Tender specifies '{', '.join(req.product_keywords)}' but omits reference to applicable "
                            f"Indian Standard {cand_num} ({candidate.title})."
                        ),
                        recommendation=(
                            f"Include technical reference to {cand_num} in the technical specifications."
                        ),
                        evidence={
                            "confidence_score": candidate.confidence_score,
                            "relevance_score": candidate.relevance_score,
                            "is_mandatory": is_mand,
                            "source_dataset": "Module 6 Semantic Recommendation",
                        }
                    ))

        # ---------------------------------------------------------------------
        # 3. COMPUTE COVERAGE SCORE
        # ---------------------------------------------------------------------
        total_present = len(present_standards_data)
        outdated_count = len(outdated_standards_data)
        missing_count = len(missing_standards_data)
        testing_gap_count = len(testing_gaps_data)
        safety_gap_count = len(safety_gaps_data)

        # Baseline calculation:
        # Valid current present standards add to score.
        # Outdated standards heavily penalized (-0.35 each).
        # Missing primary product standards penalized (-0.25 each).
        # Missing allied testing/safety standards lightly penalized (-0.05 each).
        if total_present == 0 and missing_count == 0:
            coverage = 0.50  # Neutral / unestablished
        else:
            valid_present = max(0, total_present - outdated_count)
            denom = max(1, valid_present + missing_count)
            base_ratio = valid_present / float(denom)

            # Deductions
            deductions = (outdated_count * 0.25) + (testing_gap_count * 0.05) + (safety_gap_count * 0.05)
            coverage = max(0.0, min(1.0, base_ratio - deductions))

        coverage_score = round(coverage, 2)
        coverage_pct = round(coverage_score * 100, 1)

        # Summary generation
        crit_count = sum(1 for g in gaps if g.severity == GapSeverity.CRITICAL)
        warn_count = sum(1 for g in gaps if g.severity == GapSeverity.WARNING)
        adv_count = sum(1 for g in gaps if g.severity == GapSeverity.ADVISORY)

        summary_parts = [
            f"Tender audit completed with overall standards coverage score of {coverage_pct}%.",
            f"Found {len(present_standards_data)} explicit standard citations ({outdated_count} outdated).",
        ]
        if missing_count > 0:
            summary_parts.append(f"Identified {missing_count} missing primary standard references.")
        if testing_gap_count > 0 or safety_gap_count > 0:
            summary_parts.append(f"Detected {testing_gap_count} potential testing gaps and {safety_gap_count} safety gaps.")
        if crit_count > 0:
            summary_parts.append(f"CRITICAL ACTION REQUIRED: {crit_count} critical issues must be resolved before tender publication.")

        audit_summary_str = " ".join(summary_parts)

        comparison = ExpectedVsPresentComparison(
            present_standards=present_standards_data,
            expected_standards=expected_standards_data,
            missing_standards=missing_standards_data,
            outdated_standards=outdated_standards_data,
            testing_gaps=testing_gaps_data,
            safety_gaps=safety_gaps_data,
            certification_gaps=certification_gaps_data,
        )

        return TenderAuditReport(
            tender_id=tender.id,
            tender_number=tender.tender_number,
            filename=tender.filename,
            coverage_score=coverage_score,
            coverage_percentage=coverage_pct,
            audit_summary=audit_summary_str,
            total_gaps_found=len(gaps),
            critical_issues_count=crit_count,
            warnings_count=warn_count,
            advisories_count=adv_count,
            gaps=gaps,
            expected_vs_present=comparison,
            created_at=tender.created_at,
        )
