"""
Specification Generator Engine (Module 13).
Grounded strictly in verified project records and analyzed tender context:
- RecommendationEngine (Module 6)
- RelationshipEngine (Module 7)
- VersionIntelligenceService (Module 8)
- ComplianceIntelligenceService (Module 9)
- TenderEngineService (Module 11)
- TenderGapAnalyzer (Module 12)

Strictly adheres to:
1. Zero hallucination of IS numbers, technical tolerances, test limits, or legal mandates.
2. If data cannot establish a requirement, outputs UNKNOWN / 'Insufficient verified evidence'.
3. PRIMARY is an internal recommendation role only (not official BIS).
4. confidence_score is an internal decision-support metric only.
5. Preserves complete evidence and provenance for every generated item.
6. Clearly distinguishes TENDER_DERIVED, RECOMMENDED_STANDARD, COMPLIANCE_REQUIREMENT, CONDITIONAL_RECOMMENDATION.
"""
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from backend.app.models.standard import Standard
from backend.app.models.tender import (
    TenderDocument,
    TenderRequirement,
    TenderStandardReference,
)
from backend.app.services.recommendation import RecommendationEngine, RecommendationRequest
from backend.app.services.relationship_engine import RelationshipEngine
from backend.app.services.version_intelligence import VersionIntelligenceService
from backend.app.services.compliance_intelligence import ComplianceIntelligenceService
from backend.app.services.tender_audit import TenderGapAnalyzer, GapCategory
from backend.app.services.specification_generator.schemas import (
    SpecificationType,
    RequirementOrigin,
    RegulatoryStatus,
    GeneratedRequirementItem,
    TechnicalSpecificationContent,
    TenderClauseContent,
    ComplianceChecklistItem,
    AuditCorrectionContent,
)


class SpecificationGenerator:
    """
    Core engine for generating evidence-grounded procurement specifications,
    corrective clauses, and compliance checklists.
    """

    def __init__(self, db: Session):
        self.db = db
        self.recommendation_engine = RecommendationEngine(db)
        self.relationship_engine = RelationshipEngine(db)
        self.version_service = VersionIntelligenceService(db)
        self.compliance_service = ComplianceIntelligenceService(db)
        self.gap_analyzer = TenderGapAnalyzer(db)

    def generate(
        self,
        generation_type: SpecificationType,
        tender_id: Optional[int] = None,
        analysis_id: Optional[str] = None,
        query_text: Optional[str] = None,
        title: Optional[str] = None,
        include_allied: bool = True,
        include_checklists: bool = True,
    ) -> Tuple[str, Dict[str, Any], List[Dict[str, Any]]]:
        """
        Master generation dispatcher.
        Returns: (generated_text, structured_content_dict, provenance_records_list)
        """
        if generation_type == SpecificationType.TECHNICAL_SPECIFICATION:
            return self.generate_technical_specification(
                tender_id=tender_id,
                analysis_id=analysis_id,
                query_text=query_text,
                title=title,
                include_allied=include_allied,
            )
        elif generation_type in (SpecificationType.TENDER_CLAUSE, SpecificationType.CORRECTIVE_CLAUSE):
            return self.generate_tender_clause(
                tender_id=tender_id,
                query_text=query_text,
                title=title,
            )
        elif generation_type == SpecificationType.COMPLIANCE_CHECKLIST:
            return self.generate_compliance_checklist(
                tender_id=tender_id,
                query_text=query_text,
                title=title,
            )
        elif generation_type == SpecificationType.AUDIT_CORRECTION:
            return self.generate_audit_correction(
                tender_id=tender_id,
                title=title,
            )
        else:
            raise ValueError(f"Unsupported specification generation type: {generation_type}")

    # =========================================================================
    # 1. TECHNICAL SPECIFICATION GENERATION
    # =========================================================================
    def generate_technical_specification(
        self,
        tender_id: Optional[int] = None,
        analysis_id: Optional[str] = None,
        query_text: Optional[str] = None,
        title: Optional[str] = None,
        include_allied: bool = True,
    ) -> Tuple[str, Dict[str, Any], List[Dict[str, Any]]]:
        """
        Generates a comprehensive, standards-aligned technical procurement specification.
        """
        applicable_standards: List[GeneratedRequirementItem] = []
        testing_standards: List[GeneratedRequirementItem] = []
        safety_standards: List[GeneratedRequirementItem] = []
        compliance_clauses: List[GeneratedRequirementItem] = []
        technical_parameters: List[Dict[str, Any]] = []
        provenance_summary: List[Dict[str, Any]] = []

        seen_standards = set()
        spec_title = title or "TECHNICAL PROCUREMENT SPECIFICATION"
        scope_lines = []

        if tender_id:
            tender = self.db.query(TenderDocument).filter(TenderDocument.id == tender_id).first()
            if not tender:
                raise ValueError(f"Tender document ID {tender_id} not found.")

            spec_title = title or f"TECHNICAL SPECIFICATION: {tender.title or tender.filename}"

            # Audit tender for comprehensive gap analysis
            audit_report = self.gap_analyzer.analyze_tender(tender)

            # 1. Gather scope and technical parameters from tender requirements
            reqs = self.db.query(TenderRequirement).filter(TenderRequirement.tender_id == tender_id).all()
            for r in reqs:
                scope_lines.append(f"- {r.requirement_text}")
                if r.technical_attributes:
                    for k, v in r.technical_attributes.items():
                        technical_parameters.append({
                            "parameter": k.replace("_", " ").title(),
                            "value": str(v),
                            "origin": RequirementOrigin.TENDER_DERIVED.value,
                            "trust_level": "KNOWN",
                            "note": f"Extracted from tender clause {r.id}",
                        })

            # 2. Process explicit present standards
            for present in audit_report.expected_vs_present.present_standards:
                std_ident = present.get("canonical_id") or present.get("standard_id") or ""
                std = self._find_standard(present.get("standard_id") or std_ident)
                if not std:
                    continue

                std_num = std.standard_id
                clean_num = std_num.upper().replace(" ", "")
                seen_standards.add(clean_num)

                # Check supersession
                v_info = self.version_service.check_currency(std.id)
                comp_info = self.compliance_service.evaluate_compliance(std.id)
                req_level_str = comp_info.requirement_level.value if comp_info and comp_info.requirement_level else "UNKNOWN"
                is_mand = (req_level_str == "MANDATORY")

                succ_num, succ_id = self._extract_successor_from_currency(v_info)
                if v_info and not v_info.is_current and succ_num:
                    succ_std = self._find_standard(succ_num)
                    applicable_standards.append(GeneratedRequirementItem(
                        item_id=f"std-{std.id}-superseded",
                        origin=RequirementOrigin.RECOMMENDED_STANDARD,
                        clause_heading="Governing Equipment Standard (Supersession Rectification)",
                        clause_text=(
                            f"The equipment shall strictly conform to current Indian Standard {succ_num} "
                            f"('{succ_std.title if succ_std else 'Updated Standard'}'), replacing superseded "
                            f"legacy standard {std_num} referenced in tender clauses."
                        ),
                        standard_id=succ_num,
                        standard_number=succ_num,
                        title=succ_std.title if succ_std else None,
                        role="PRIMARY",
                        regulatory_status=RegulatoryStatus(req_level_str),
                        is_mandatory=is_mand,
                        confidence_score=1.0,
                        trust_level="INFERRED",
                        evidence_sources=[{
                            "source_dataset": "standard_relationships / supersedes",
                            "legacy_standard": std_num,
                            "active_standard": succ_num,
                            "successor_id": succ_id,
                        }],
                        verification_notes="Legacy standard updated via knowledge graph supersession chain.",
                    ))
                    std = succ_std or std
                else:
                    applicable_standards.append(GeneratedRequirementItem(
                        item_id=f"std-{std.id}-present",
                        origin=RequirementOrigin.TENDER_DERIVED,
                        clause_heading="Governing Indian Standard",
                        clause_text=f"The supplied product shall conform to Indian Standard {std.standard_id}: '{std.title}'.",
                        standard_id=std.standard_id,
                        standard_number=std.standard_id,
                        title=std.title,
                        role="PRIMARY",
                        regulatory_status=RegulatoryStatus(req_level_str),
                        is_mandatory=is_mand,
                        confidence_score=1.0,
                        trust_level="KNOWN",
                        evidence_sources=[{
                            "source_dataset": "tender_document / explicit citation",
                            "standard_id": std.standard_id,
                        }],
                    ))

                # If mandatory QCO applies, stipulate compliance clause
                if comp_info and (comp_info.qco_applicable or is_mand):
                    compliance_clauses.append(GeneratedRequirementItem(
                        item_id=f"comp-{std.id}",
                        origin=RequirementOrigin.COMPLIANCE_REQUIREMENT,
                        clause_heading=f"Mandatory BIS Certification Requirement ({std.standard_id})",
                        clause_text=(
                            f"Bidders must possess a valid BIS Licence / Certificate of Conformity for {std.standard_id} "
                            f"(bearing standard ISI Mark) issued by the Bureau of Indian Standards as per applicable "
                            f"statutory Quality Control Order ({self._get_qco_order_number(comp_info) or 'Gazette QCO'})."
                        ),
                        standard_id=std.standard_id,
                        standard_number=std.standard_id,
                        title=std.title,
                        regulatory_status=RegulatoryStatus.MANDATORY,
                        is_mandatory=True,
                        confidence_score=1.0,
                        trust_level="INFERRED",
                        evidence_sources=[{
                            "source_dataset": "qco_records / certification_records",
                            "qco_order_number": self._get_qco_order_number(comp_info),
                            "governing_scheme": comp_info.governing_scheme if comp_info else None,
                        }],
                        verification_notes="Enforced by verified Quality Control Order records.",
                    ))

                # Allied testing & safety standards
                if include_allied and std:
                    allied_group = self.relationship_engine.get_allied_standards(std.id)
                    if allied_group:
                        for test_item in allied_group.testing:
                            test_num = test_item.standard_number or test_item.standard_id
                            clean_test = test_num.upper().replace(" ", "")
                            if clean_test not in seen_standards:
                                seen_standards.add(clean_test)
                                testing_standards.append(GeneratedRequirementItem(
                                    item_id=f"test-{clean_test}",
                                    origin=RequirementOrigin.CONDITIONAL_RECOMMENDATION,
                                    clause_heading="Testing & Acceptance Criteria",
                                    clause_text=(
                                        f"Acceptance and type testing shall be carried out in accordance with {test_num} "
                                        f"('{test_item.title or 'Testing Methods'}') at an accredited/BIS-approved laboratory."
                                    ),
                                    standard_id=test_num,
                                    standard_number=test_num,
                                    title=test_item.title,
                                    role="TESTING",
                                    regulatory_status=RegulatoryStatus.VOLUNTARY,
                                    is_mandatory=False,
                                    confidence_score=0.9,
                                    trust_level="INFERRED",
                                    evidence_sources=[{
                                        "source_dataset": "relationships.json / standards.csv",
                                        "relationship_type": test_item.relationship_type,
                                        "governing_standard": std.standard_id,
                                    }],
                                ))

                        for safe_item in allied_group.safety:
                            safe_num = safe_item.standard_number or safe_item.standard_id
                            clean_safe = safe_num.upper().replace(" ", "")
                            if clean_safe not in seen_standards:
                                seen_standards.add(clean_safe)
                                safety_standards.append(GeneratedRequirementItem(
                                    item_id=f"safe-{clean_safe}",
                                    origin=RequirementOrigin.CONDITIONAL_RECOMMENDATION,
                                    clause_heading="Safety & Environmental Compliance",
                                    clause_text=(
                                        f"The equipment design and construction shall comply with normative safety standard {safe_num} "
                                        f"('{safe_item.title or 'Safety Code'}')."
                                    ),
                                    standard_id=safe_num,
                                    standard_number=safe_num,
                                    title=safe_item.title,
                                    role="SAFETY",
                                    regulatory_status=RegulatoryStatus.VOLUNTARY,
                                    is_mandatory=False,
                                    confidence_score=0.9,
                                    trust_level="INFERRED",
                                    evidence_sources=[{
                                        "source_dataset": "relationships.json / standards.csv",
                                        "relationship_type": safe_item.relationship_type,
                                        "governing_standard": std.standard_id,
                                    }],
                                ))

            # 3. Process missing standards identified in tender audit
            for missing in audit_report.expected_vs_present.missing_standards:
                m_num = missing.get("standard_id", "")
                clean_m = m_num.upper().replace(" ", "")
                if clean_m not in seen_standards:
                    seen_standards.add(clean_m)
                    m_std = self._find_standard(m_num)
                    comp_m = self.compliance_service.evaluate_compliance(m_std.id) if m_std else None
                    m_req_level = comp_m.requirement_level.value if comp_m and comp_m.requirement_level else "UNKNOWN"

                    applicable_standards.append(GeneratedRequirementItem(
                        item_id=f"missing-{clean_m}",
                        origin=RequirementOrigin.RECOMMENDED_STANDARD,
                        clause_heading="Recommended Standard for Unreferenced Requirement",
                        clause_text=(
                            f"Procurement item conforming to '{missing.get('clause_text', '')}' shall adhere to Indian Standard "
                            f"{m_num} ('{missing.get('title', '')}')."
                        ),
                        standard_id=m_num,
                        standard_number=m_num,
                        title=missing.get("title"),
                        role="PRIMARY",
                        regulatory_status=RegulatoryStatus(m_req_level),
                        is_mandatory=bool(missing.get("is_mandatory", False)),
                        confidence_score=float(missing.get("confidence_score", 0.85)),
                        trust_level="INFERRED",
                        evidence_sources=[{
                            "source_dataset": "recommendation_engine / tender_clause",
                            "detected_requirement": missing.get("clause_text"),
                        }],
                        verification_notes="Identified as missing primary standard in tender gap analysis.",
                    ))

        elif query_text or analysis_id:
            # Standalone requirement query generation
            query = query_text or "Procurement Requirement"
            scope_lines.append(f"- Procurement scope: {query}")
            rec_result = self.recommendation_engine.recommend(
                RecommendationRequest(query_text=query, max_primary=2, include_allied=True)
            )

            for cand in rec_result.primary_standards:
                std = self.db.query(Standard).filter(Standard.id == cand.id).first()
                clean_num = (cand.standard_id or cand.is_number).upper().replace(" ", "")
                seen_standards.add(clean_num)

                comp_info = self.compliance_service.evaluate_compliance(cand.id)
                cand_req_level = comp_info.requirement_level.value if comp_info and comp_info.requirement_level else "UNKNOWN"
                cand_is_mand = (cand_req_level == "MANDATORY")

                applicable_standards.append(GeneratedRequirementItem(
                    item_id=f"cand-{cand.id}",
                    origin=RequirementOrigin.RECOMMENDED_STANDARD,
                    clause_heading="Governing Indian Standard",
                    clause_text=f"The supplied goods shall conform to Indian Standard {cand.standard_id}: '{cand.title}'.",
                    standard_id=cand.standard_id,
                    standard_number=cand.is_number,
                    title=cand.title,
                    role="PRIMARY",
                    regulatory_status=RegulatoryStatus(cand_req_level),
                    is_mandatory=cand_is_mand,
                    confidence_score=cand.confidence_score,
                    trust_level="INFERRED",
                    evidence_sources=[{
                        "source_dataset": "standards.csv / hybrid_retrieval",
                        "relevance_score": cand.relevance_score,
                    }],
                ))

                if comp_info and (comp_info.qco_applicable or cand_is_mand):
                    compliance_clauses.append(GeneratedRequirementItem(
                        item_id=f"comp-{cand.id}",
                        origin=RequirementOrigin.COMPLIANCE_REQUIREMENT,
                        clause_heading=f"Mandatory BIS Certification Requirement ({cand.standard_id})",
                        clause_text=(
                            f"Bidders must possess a valid BIS Licence for {cand.standard_id} bearing ISI Mark "
                            f"as per applicable Quality Control Order ({self._get_qco_order_number(comp_info) or 'Gazette QCO'})."
                        ),
                        standard_id=cand.standard_id,
                        standard_number=cand.is_number,
                        title=cand.title,
                        regulatory_status=RegulatoryStatus.MANDATORY,
                        is_mandatory=True,
                        confidence_score=1.0,
                        trust_level="INFERRED",
                        evidence_sources=[{
                            "source_dataset": "qco_records",
                            "qco_order_number": self._get_qco_order_number(comp_info),
                        }],
                    ))

                # Allied standards from recommendation response
                if include_allied and std:
                    allied_group = self.relationship_engine.get_allied_standards(std.id)
                    if allied_group:
                        for test_item in allied_group.testing:
                            test_num = test_item.standard_number or test_item.standard_id
                            clean_test = test_num.upper().replace(" ", "")
                            if clean_test not in seen_standards:
                                seen_standards.add(clean_test)
                                testing_standards.append(GeneratedRequirementItem(
                                    item_id=f"test-{clean_test}",
                                    origin=RequirementOrigin.CONDITIONAL_RECOMMENDATION,
                                    clause_heading="Testing & Acceptance Criteria",
                                    clause_text=(
                                        f"Routine, type, and acceptance tests shall be performed in accordance with {test_num} "
                                        f"('{test_item.title or 'Testing Standard'}')."
                                    ),
                                    standard_id=test_num,
                                    standard_number=test_num,
                                    title=test_item.title,
                                    role="TESTING",
                                    regulatory_status=RegulatoryStatus.VOLUNTARY,
                                    is_mandatory=False,
                                    confidence_score=0.9,
                                    trust_level="INFERRED",
                                    evidence_sources=[{"source_dataset": "relationships.json"}],
                                ))

        # Enforce Rule 5 & 6: Never invent technical limits or tolerances.
        # Add explicit UNKNOWN record if no technical parameters were extracted or available.
        if not technical_parameters:
            technical_parameters.append({
                "parameter": "Operating Ratings, Tolerances & Performance Parameters",
                "value": "UNKNOWN",
                "status": "Insufficient verified evidence in provided tender/records",
                "note": "Do not assume or invent unverified technical limits.",
            })

        # Build full markdown text
        scope_text = "\n".join(scope_lines) if scope_lines else "- Supply of materials as per applicable Indian Standards."
        full_text = self._build_specification_markdown(
            title=spec_title,
            scope_of_work=scope_text,
            applicable_standards=applicable_standards,
            technical_parameters=technical_parameters,
            testing_standards=testing_standards,
            safety_standards=safety_standards,
            compliance_clauses=compliance_clauses,
        )

        structured_content = TechnicalSpecificationContent(
            title=spec_title,
            scope_of_work=scope_text,
            applicable_standards=applicable_standards,
            technical_parameters=technical_parameters,
            testing_and_acceptance=testing_standards,
            safety_and_environmental=safety_standards,
            mandatory_compliance_clauses=compliance_clauses,
            full_text=full_text,
            provenance_summary=provenance_summary,
        ).model_dump()

        # Gather provenance summary
        for item in (applicable_standards + testing_standards + safety_standards + compliance_clauses):
            provenance_summary.extend(item.evidence_sources)

        return full_text, structured_content, provenance_summary

    # =========================================================================
    # 2. TENDER CLAUSE & CORRECTIVE CLAUSE GENERATION
    # =========================================================================
    def generate_tender_clause(
        self,
        tender_id: Optional[int] = None,
        query_text: Optional[str] = None,
        title: Optional[str] = None,
    ) -> Tuple[str, Dict[str, Any], List[Dict[str, Any]]]:
        """
        Generates formal procurement clauses ready for insertion into Section 2 of tenders.
        """
        clause_title = title or "STANDARDS COMPLIANCE & ACCEPTANCE CLAUSE"
        incorporated_standards: List[str] = []
        evidence_sources: List[Dict[str, Any]] = []
        clause_paragraphs: List[str] = []
        mand_cert_text: Optional[str] = None

        if tender_id:
            tender = self.db.query(TenderDocument).filter(TenderDocument.id == tender_id).first()
            if not tender:
                raise ValueError(f"Tender ID {tender_id} not found.")

            audit_report = self.gap_analyzer.analyze_tender(tender)

            # Check outdated standards first
            for outdated in audit_report.expected_vs_present.outdated_standards:
                old_num = outdated.get("standard_id", "")
                succ_num = outdated.get("superseded_by", "")
                incorporated_standards.append(succ_num or old_num)
                clause_paragraphs.append(
                    f"Clause 2.X [Standards Conformance]: The equipment supplied shall strictly conform to "
                    f"active standard {succ_num}, superseding the withdrawn/legacy standard {old_num} referenced "
                    f"in prior revisions. Equipment manufactured under withdrawn standards shall not be accepted."
                )
                evidence_sources.append({
                    "rule": "supersession_rectification",
                    "outdated_standard": old_num,
                    "active_standard": succ_num,
                })

            # Check missing standards
            for missing in audit_report.expected_vs_present.missing_standards:
                m_num = missing.get("standard_id", "")
                incorporated_standards.append(m_num)
                clause_paragraphs.append(
                    f"Clause 2.Y [Product Conformance]: Goods specified under '{missing.get('clause_text', 'equipment')}' "
                    f"shall fully conform to {m_num} ('{missing.get('title', '')}')."
                )
                evidence_sources.append({
                    "rule": "missing_standard_stipulation",
                    "standard_id": m_num,
                    "confidence_score": missing.get("confidence_score", 0.9),
                })

            # Check certification gaps
            for cert_gap in audit_report.expected_vs_present.certification_gaps:
                std_num = cert_gap.get("standard_id", "")
                qco_num = cert_gap.get("qco_order_number", "Gazette QCO")
                mand_cert_text = (
                    f"Clause 2.Z [Mandatory BIS Certification / ISI Mark]: As per the statutory Quality Control Order "
                    f"({qco_num}), the bidder must be a licensed manufacturer holding a valid BIS Licence (CML Number) "
                    f"for {std_num}. The BIS standard mark (ISI Mark) must be visibly embossed/printed on the product "
                    f"and packaging. Non-certified bids shall be summarily rejected."
                )
                clause_paragraphs.append(mand_cert_text)
                evidence_sources.append({
                    "rule": "mandatory_qco_certification",
                    "standard_id": std_num,
                    "qco_order": qco_num,
                })

        if not clause_paragraphs:
            # Fallback or query-based clause
            q = query_text or "Procurement Requirement"
            rec = self.recommendation_engine.recommend(RecommendationRequest(query_text=q, max_primary=1))
            if rec.primary_standards:
                p = rec.primary_standards[0]
                incorporated_standards.append(p.standard_id)
                clause_paragraphs.append(
                    f"Clause 2.1 [Standards Compliance]: The goods supplied under this tender shall strictly comply "
                    f"with Indian Standard {p.standard_id} ('{p.title}'). Bidders shall submit full type test certificates "
                    f"conforming to the requirements of the governing standard."
                )
                evidence_sources.append({
                    "source_dataset": "standards.csv",
                    "standard_id": p.standard_id,
                })
            else:
                clause_paragraphs.append(
                    "Clause 2.1 [Standards Compliance]: UNKNOWN: Insufficient verified evidence in provided tender/records "
                    "to formulate specific standards clause."
                )

        full_text = "\n\n".join(clause_paragraphs)
        structured = TenderClauseContent(
            title=clause_title,
            clause_type="MANDATORY_CORRECTIVE_CLAUSE" if tender_id else "STANDARD_SPECIFICATION_CLAUSE",
            clause_text=full_text,
            incorporated_standards=list(set(incorporated_standards)),
            mandatory_certification_clause=mand_cert_text,
            evidence_sources=evidence_sources,
        ).model_dump()

        return full_text, structured, evidence_sources

    # =========================================================================
    # 3. COMPLIANCE CHECKLIST GENERATION
    # =========================================================================
    def generate_compliance_checklist(
        self,
        tender_id: Optional[int] = None,
        query_text: Optional[str] = None,
        title: Optional[str] = None,
    ) -> Tuple[str, Dict[str, Any], List[Dict[str, Any]]]:
        """
        Generates a tabular and structured compliance checklist for procurement evaluation.
        """
        checklist_items: List[ComplianceChecklistItem] = []
        evidence_sources: List[Dict[str, Any]] = []
        seen = set()

        if tender_id:
            tender = self.db.query(TenderDocument).filter(TenderDocument.id == tender_id).first()
            if not tender:
                raise ValueError(f"Tender ID {tender_id} not found.")

            audit_report = self.gap_analyzer.analyze_tender(tender)

            # Check present standards
            for present in audit_report.expected_vs_present.present_standards:
                std_ident = present.get("canonical_id") or present.get("standard_id") or ""
                std = self._find_standard(present.get("standard_id") or std_ident)
                if not std:
                    continue

                std_num = std.standard_id
                clean_num = std_num.upper().replace(" ", "")
                if clean_num in seen:
                    continue
                seen.add(clean_num)

                comp = self.compliance_service.evaluate_compliance(std.id) if std else None
                req_level_str = comp.requirement_level.value if comp and comp.requirement_level else "UNKNOWN"
                is_mand = (req_level_str == "MANDATORY")
                qco_order = self._get_qco_order_number(comp)

                checklist_items.append(ComplianceChecklistItem(
                    item_id=f"chk-{clean_num}",
                    standard_number=std_num,
                    standard_title=std.title if std else "Procurement Standard",
                    role="PRIMARY",
                    origin=RequirementOrigin.TENDER_DERIVED,
                    regulatory_status=req_level_str,
                    mandatory_certification=is_mand,
                    qco_number=qco_order,
                    verification_method="Verify valid CML licence number on BIS portal (manakonline.in)",
                    action_required=(
                        "Mandatory ISI Mark certification proof required before technical bid opening"
                        if is_mand else "Submit manufacturer declaration / test certificate"
                    ),
                    evidence_records=[{
                        "source_dataset": "tender_document / qco_records",
                        "regulatory_status": req_level_str,
                        "qco_order_number": qco_order,
                    }],
                ))
                evidence_sources.append({"standard_id": std_num, "status": req_level_str})

            # Check testing gaps
            for tg in audit_report.expected_vs_present.testing_gaps:
                allied_num = tg.get("allied_standard_id", "")
                clean_allied = allied_num.upper().replace(" ", "")
                if clean_allied not in seen:
                    seen.add(clean_allied)
                    allied_title = tg.get("allied_title") or tg.get("allied_standard_id") or "Testing Standard"
                    checklist_items.append(ComplianceChecklistItem(
                        item_id=f"chk-test-{clean_allied}",
                        standard_number=allied_num,
                        standard_title=str(allied_title),
                        role="TESTING",
                        origin=RequirementOrigin.CONDITIONAL_RECOMMENDATION,
                        regulatory_status="VOLUNTARY",
                        mandatory_certification=False,
                        verification_method="Submit NABL-accredited laboratory test report",
                        action_required="Ensure acceptance tests conform to this standard",
                        evidence_records=[{"relationship": "TESTING", "governing_standard": tg.get("primary_standard")}],
                    ))

        # Markdown representation
        md_lines = [
            f"# {title or 'PROCUREMENT COMPLIANCE VERIFICATION CHECKLIST'}",
            "",
            "| Item | Indian Standard | Role | Regulatory Status | Mandatory Certification | Verification Method | Action Required |",
            "|:---|:---|:---|:---|:---|:---|:---|",
        ]
        for idx, item in enumerate(checklist_items, 1):
            mand_str = "YES (Mandatory)" if item.mandatory_certification else "No"
            md_lines.append(
                f"| {idx} | **{item.standard_number}**<br>{item.standard_title} | {item.role} | "
                f"`{item.regulatory_status}` | {mand_str} | {item.verification_method} | {item.action_required} |"
            )

        full_text = "\n".join(md_lines)
        structured = {
            "title": title or "PROCUREMENT COMPLIANCE VERIFICATION CHECKLIST",
            "total_items": len(checklist_items),
            "items": [item.model_dump() for item in checklist_items],
        }

        return full_text, structured, evidence_sources

    # =========================================================================
    # 4. AUDIT CORRECTION GENERATION
    # =========================================================================
    def generate_audit_correction(
        self,
        tender_id: int,
        title: Optional[str] = None,
    ) -> Tuple[str, Dict[str, Any], List[Dict[str, Any]]]:
        """
        Generates an audit-driven corrective package rectifying all detected tender gaps.
        """
        tender = self.db.query(TenderDocument).filter(TenderDocument.id == tender_id).first()
        if not tender:
            raise ValueError(f"Tender ID {tender_id} not found.")

        audit_report = self.gap_analyzer.analyze_tender(tender)
        corrected_clauses: List[Dict[str, Any]] = []
        evidence_sources: List[Dict[str, Any]] = []

        # 1. Superseded standards correction
        for out in audit_report.expected_vs_present.outdated_standards:
            old_std = out.get("standard_id", "")
            succ_std = out.get("superseded_by", "")
            corrected_clauses.append({
                "gap_type": "OUTDATED_REFERENCE",
                "issue": f"Tender cites obsolete standard {old_std}",
                "original_clause": f"Specifications stipulating {old_std}",
                "corrected_clause": (
                    f"All equipment shall strictly comply with current standard {succ_std}. "
                    f"Citations of obsolete standard {old_std} are hereby superseded and shall not be accepted."
                ),
                "trust_level": "INFERRED",
                "evidence": {"source_dataset": "standard_relationships", "superseded_by": succ_std},
            })
            evidence_sources.append({"rule": "supersession_replacement", "old": old_std, "new": succ_std})

        # 2. Missing standards correction
        for miss in audit_report.expected_vs_present.missing_standards:
            std_num = miss.get("standard_id", "")
            clause = miss.get("clause_text", "Equipment clause")
            corrected_clauses.append({
                "gap_type": "MISSING_REFERENCE",
                "issue": f"Requirement '{clause}' lacks governing standard reference",
                "original_clause": clause,
                "corrected_clause": f"{clause} Conformance to Indian Standard {std_num} is mandatory.",
                "trust_level": "INFERRED",
                "evidence": {"source_dataset": "recommendation_engine", "recommended_standard": std_num},
            })
            evidence_sources.append({"rule": "missing_standard_insertion", "standard_id": std_num})

        # 3. Certification gaps correction
        for cert in audit_report.expected_vs_present.certification_gaps:
            std_num = cert.get("standard_id", "")
            qco = cert.get("qco_order_number", "Applicable QCO")
            corrected_clauses.append({
                "gap_type": "CERTIFICATION_GAP",
                "issue": f"Standard {std_num} falls under mandatory QCO but tender omits certification clause",
                "original_clause": f"Clause referencing {std_num}",
                "corrected_clause": (
                    f"In accordance with {qco}, bidders must provide proof of valid BIS Licence (ISI Mark) "
                    f"for {std_num} at the time of tender submission."
                ),
                "trust_level": "INFERRED",
                "evidence": {"source_dataset": "qco_records", "qco_order": qco},
            })
            evidence_sources.append({"rule": "mandatory_certification_added", "standard_id": std_num})

        # Build clean corrective document
        doc_lines = [
            f"# {title or f'TENDER AUDIT CORRECTIVE SPECIFICATION: {tender.filename}'}",
            "",
            f"**Tender Reference:** {tender.tender_number or tender.id}",
            f"**Audit Coverage Score:** {audit_report.coverage_percentage}",
            f"**Total Corrections Made:** {len(corrected_clauses)}",
            "",
            "## Summary of Corrected Clauses",
            "",
        ]

        for idx, corr in enumerate(corrected_clauses, 1):
            doc_lines.append(f"### Correction {idx}: {corr['gap_type']}")
            doc_lines.append(f"**Identified Issue:** {corr['issue']}")
            doc_lines.append(f"**Original Text:** *\"{corr['original_clause']}\"*")
            doc_lines.append(f"**Corrected Specification:**")
            doc_lines.append(f"> {corr['corrected_clause']}")
            doc_lines.append("")

        full_text = "\n".join(doc_lines)
        structured = AuditCorrectionContent(
            tender_id=tender.id,
            total_corrections_made=len(corrected_clauses),
            corrected_clauses=corrected_clauses,
            clean_specification_text=full_text,
            audit_reference={"coverage_score": audit_report.coverage_score},
        ).model_dump()

        return full_text, structured, evidence_sources

    # =========================================================================
    # HELPER UTILITIES
    # =========================================================================
    def _find_standard(self, standard_num_or_id: Any) -> Optional[Standard]:
        """Looks up a standard in canonical DB by standard_id, is_number, or integer ID."""
        if standard_num_or_id is None:
            return None
        if isinstance(standard_num_or_id, int):
            return self.db.query(Standard).filter(Standard.id == standard_num_or_id).first()
        clean = str(standard_num_or_id).strip()
        if not clean:
            return None
        if clean.isdigit():
            std_by_int = self.db.query(Standard).filter(Standard.id == int(clean)).first()
            if std_by_int:
                return std_by_int
        # Direct standard_id
        std = self.db.query(Standard).filter(Standard.standard_id == clean).first()
        if std:
            return std
        # Prefix match
        return self.db.query(Standard).filter(
            (Standard.standard_id.ilike(f"{clean}%")) | (Standard.is_number.ilike(f"{clean}%"))
        ).first()

    def _get_qco_order_number(self, comp_info: Optional[Any]) -> Optional[str]:
        """
        Extract the first QCO order number from a ComplianceIntelligenceReport's qco_records list.
        Returns None if no QCO records exist.
        """
        if not comp_info or not hasattr(comp_info, 'qco_records'):
            return None
        for qco in (comp_info.qco_records or []):
            order_num = qco.get("qco_order_number") or qco.get("order_number")
            if order_num:
                return str(order_num)
        return None

    def _extract_successor_from_currency(
        self,
        currency_result: Optional[Any],
    ) -> Tuple[Optional[str], Optional[Any]]:
        """
        Extract the first successor standard number and ID from a CurrencyCheckResult.
        Supersession info is stored in warnings of type SUPERSEDED_WARNING,
        inside evidence.successors (a list of dicts from Module 4).
        Returns (successor_standard_number, successor_standard_id) or (None, None).
        """
        if not currency_result or not hasattr(currency_result, 'warnings'):
            return None, None
        for w in currency_result.warnings:
            if w.warning_type and w.warning_type.value == "SUPERSEDED_WARNING":
                successors = w.evidence.get("successors", []) if isinstance(w.evidence, dict) else []
                if successors:
                    first = successors[0]
                    succ_num = first.get("canonical_id") or str(first.get("standard_id", ""))
                    succ_id = first.get("standard_id")
                    return succ_num, succ_id
        return None, None

    def _build_specification_markdown(
        self,
        title: str,
        scope_of_work: str,
        applicable_standards: List[GeneratedRequirementItem],
        technical_parameters: List[Dict[str, Any]],
        testing_standards: List[GeneratedRequirementItem],
        safety_standards: List[GeneratedRequirementItem],
        compliance_clauses: List[GeneratedRequirementItem],
    ) -> str:
        """Assembles structured markdown specification text."""
        lines = [
            f"# {title}",
            "",
            "## 1. SCOPE OF PROCUREMENT",
            scope_of_work,
            "",
            "## 2. APPLICABLE INDIAN STANDARDS",
            "The equipment and materials supplied under this contract shall comply with the latest editions of the following standards:",
            "",
        ]

        if applicable_standards:
            for item in applicable_standards:
                mand_tag = "**[MANDATORY]**" if item.is_mandatory else "[STANDARD]"
                lines.append(f"- {mand_tag} **{item.standard_id}**: {item.title or 'Indian Standard'}")
                lines.append(f"  *{item.clause_text}*")
        else:
            lines.append("- *No specific Indian Standards identified from verified project records.*")

        lines.extend([
            "",
            "## 3. TECHNICAL PARAMETERS & SPECIFICATIONS",
            "| Parameter | Specified Value | Trust Level | Status / Notes |",
            "|:---|:---|:---|:---|",
        ])
        for param in technical_parameters:
            lines.append(
                f"| {param.get('parameter')} | **{param.get('value')}** | "
                f"`{param.get('trust_level', 'UNKNOWN')}` | {param.get('note', param.get('status', ''))} |"
            )

        lines.extend([
            "",
            "## 4. TESTING AND ACCEPTANCE CRITERIA",
        ])
        if testing_standards:
            for test in testing_standards:
                lines.append(f"- **{test.standard_id}**: {test.clause_text}")
        else:
            lines.append("- *Testing criteria: UNKNOWN — Insufficient verified evidence in provided records.*")

        lines.extend([
            "",
            "## 5. SAFETY AND ENVIRONMENTAL REQUIREMENTS",
        ])
        if safety_standards:
            for safe in safety_standards:
                lines.append(f"- **{safe.standard_id}**: {safe.clause_text}")
        else:
            lines.append("- *Safety standards: Normative statutory safety provisions apply.*")

        lines.extend([
            "",
            "## 6. MANDATORY STATUTORY & BIS CERTIFICATION CLAUSES",
        ])
        if compliance_clauses:
            for comp in compliance_clauses:
                lines.append(f"### {comp.clause_heading}")
                lines.append(f"> {comp.clause_text}")
                lines.append("")
        else:
            lines.append("- *No mandatory QCO enforcement order identified for the cited standards in database records.*")

        lines.extend([
            "",
            "---",
            "*Disclaimer: This specification was generated automatically by ARISTEA-PROCURE decision support engine. "
            "All cited standards, versions, and QCO requirements are grounded strictly in canonical BIS datasets.*",
        ])

        return "\n".join(lines)
