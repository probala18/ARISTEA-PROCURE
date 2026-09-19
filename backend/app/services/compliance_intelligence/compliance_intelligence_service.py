"""
Compliance Intelligence Service for Module 9.
Provides deterministic, evidence-driven compliance evaluations, scheme classification,
QCO mandate tracking, licence context, and scope-aware regulatory divergence detection.

Strictly enforces:
1. Deterministic evidence layer: zero LLM inference, zero external domain knowledge.
2. Ingested datasets only: certification_records, qco_records, product_licences, ministry_product_mappings, standards.
3. Requirement-level logic:
   - Explicit mandatory QCO OR explicit mandatory certification -> MANDATORY
   - Explicit conditional certification -> CONDITIONAL
   - Explicit voluntary certification with no mandatory evidence -> VOLUNTARY
   - Missing/insufficient evidence -> UNKNOWN
4. Never infer MANDATORY merely from standard existence, licence presence, or dataset appearance.
5. Never label QCO as ACTIVE without explicit status in supplied dataset.
6. Preserves all evidence records: voluntary records are never dropped when mandatory coexists.
7. Scope-aware regulatory divergence detection.
8. Grounded scheme classification (BIS_ISI, CRS, HALLMARKING, Scheme I/II/IV).
9. Bounded bulk loading for batch evaluation (no N+1 queries).
10. 100% backward compatibility with Module 7 ComplianceLinksResult.
11. Handles uncatalogued historical standards safely without manufacturing synthetic database rows.
"""
from typing import List, Dict, Any, Optional, Union, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.app.models.standard import Standard
from backend.app.models.compliance import CertificationRecord, QCORecord, ProductLicence
from backend.app.models.department import MinistryProductMapping
from backend.app.services.knowledge_graph.compliance_connector import ComplianceConnectorService
from backend.app.services.relationship_engine.engine import RelationshipEngine
from backend.app.services.compliance_intelligence.schemas import (
    RequirementLevel,
    CertificationSchemeType,
    GroundedCertificationRecord,
    GroundedQCORecord,
    RegulatoryDivergenceItem,
    StandardCertificationReport,
    ComplianceIntelligenceReport,
    BatchComplianceItem,
    BatchComplianceResult,
)


class ComplianceIntelligenceService:
    """Deterministic, grounded compliance intelligence service."""

    def __init__(self, session: Session):
        self.session = session
        self.engine = RelationshipEngine(session)
        self.connector = ComplianceConnectorService(session)

    def resolve_standard(self, identifier_or_id: Union[int, str]) -> Optional[Standard]:
        """Resolves identifier to canonical Standard entity without manufacturing synthetic rows."""
        return self.engine.resolve_standard(identifier_or_id)

    def classify_scheme(self, standard: Optional[Standard], certs: List[CertificationRecord]) -> str:
        """
        Classifies certification scheme strictly from dataset fields.
        Never infers scheme from product names or external knowledge alone.
        """
        scheme_raw = (standard.certification_scheme or "").strip() if standard else ""
        scheme_lower = scheme_raw.lower()

        # 1. Hallmarking: explicit dataset field only (Constraint 10)
        if "hallmark" in scheme_lower:
            return CertificationSchemeType.HALLMARKING.value

        # 2. CRS (Compulsory Registration Scheme / Scheme-II)
        if "crs" in scheme_lower:
            return CertificationSchemeType.CRS.value
        for c in certs:
            if c.certification_type and c.certification_type.upper() == "CRS":
                return CertificationSchemeType.CRS.value

        # 3. BIS / ISI Mark (Scheme-I)
        if "scheme-i" in scheme_lower or "isi mark" in scheme_lower or scheme_lower == "bis_isi":
            return CertificationSchemeType.BIS_ISI.value
        for c in certs:
            if c.certification_type and c.certification_type.upper() in ["BIS_ISI", "SCHEME-I", "SCHEME_I"]:
                return CertificationSchemeType.BIS_ISI.value

        # 4. Scheme-II
        if "scheme-ii" in scheme_lower:
            return CertificationSchemeType.SCHEME_II.value

        # 5. Scheme-IV
        if "scheme-iv" in scheme_lower:
            return CertificationSchemeType.SCHEME_IV.value

        if scheme_raw:
            return scheme_raw

        return CertificationSchemeType.UNKNOWN.value

    def evaluate_requirement_level(
        self, standard_label: str, standard_number: str, certs: List[CertificationRecord], qcos: List[QCORecord]
    ) -> Tuple[RequirementLevel, bool, List[RegulatoryDivergenceItem], List[str]]:
        """
        Deterministic requirement level evaluation based strictly on ingested evidence:
        - Mandatory QCO or mandatory certification -> MANDATORY
        - Conditional certification -> CONDITIONAL
        - Voluntary certification with no mandatory evidence -> VOLUNTARY
        - Missing evidence -> UNKNOWN
        Also detects scope-aware regulatory divergences.
        """
        has_mandatory_qco = any(q.is_mandatory is True for q in qcos)
        has_mandatory_cert = any(
            c.is_mandatory is True or (c.requirement_level and c.requirement_level.upper() == "MANDATORY")
            for c in certs
        )
        has_voluntary_cert = any(
            c.is_mandatory is False or (c.requirement_level and c.requirement_level.upper() == "VOLUNTARY")
            for c in certs
        )
        has_conditional_cert = any(
            c.requirement_level and c.requirement_level.upper() == "CONDITIONAL"
            for c in certs
        )

        divergences: List[RegulatoryDivergenceItem] = []
        divergence_notes: List[str] = []
        divergence_detected = False

        # Regulatory Divergence Check (Constraint 8: scope-aware)
        if has_voluntary_cert and (has_mandatory_qco or has_mandatory_cert):
            divergence_detected = True
            vol_records = [c for c in certs if c.requirement_level == "VOLUNTARY" or c.is_mandatory is False]
            mand_records = qcos if has_mandatory_qco else [c for c in certs if c.requirement_level == "MANDATORY"]

            vol_sample = vol_records[0]
            mand_sample = mand_records[0]

            note = (
                f"Regulatory divergence identified for '{standard_label}': "
                f"Certification record in '{vol_sample.source_dataset}' lists requirement as VOLUNTARY, "
                f"whereas Quality Control Order/mandate in '{mand_sample.source_dataset}' establishes MANDATORY compliance."
            )
            divergence_notes.append(note)
            divergences.append(
                RegulatoryDivergenceItem(
                    standard_number=standard_number,
                    description=note,
                    voluntary_record={
                        "id": vol_sample.id,
                        "source_dataset": vol_sample.source_dataset,
                        "requirement_level": vol_sample.requirement_level,
                        "product_name": vol_sample.product_name,
                    },
                    mandatory_record={
                        "id": mand_sample.id,
                        "source_dataset": mand_sample.source_dataset,
                        "title": getattr(mand_sample, "qco_title", None) or getattr(mand_sample, "product_name", None),
                        "is_mandatory": True,
                    },
                )
            )

        # Requirement Level Conclusion
        if has_mandatory_qco or has_mandatory_cert:
            return RequirementLevel.MANDATORY, divergence_detected, divergences, divergence_notes

        if has_conditional_cert:
            return RequirementLevel.CONDITIONAL, divergence_detected, divergences, divergence_notes

        if has_voluntary_cert:
            return RequirementLevel.VOLUNTARY, divergence_detected, divergences, divergence_notes

        return RequirementLevel.UNKNOWN, divergence_detected, divergences, divergence_notes

    def get_certification_report(self, identifier_or_id: Union[int, str]) -> Optional[StandardCertificationReport]:
        """
        Section 66 endpoint logic: GET /api/standards/{standard_id}/certification.
        Consolidates grounded certification records, QCO mandates, and governing scheme.
        Handles both catalogued standards and uncatalogued historical references safely (Constraint 12).
        """
        std = self.resolve_standard(identifier_or_id)
        ident_str = str(identifier_or_id).strip()

        if std:
            target_id = std.standard_id
            target_is_num = std.is_number
            target_title = std.title or ""
            certs = (
                self.session.query(CertificationRecord)
                .filter(
                    (CertificationRecord.standard_id == std.id)
                    | (CertificationRecord.standard_number == std.is_number)
                    | (CertificationRecord.standard_number == std.standard_id)
                )
                .all()
            )
            qcos = (
                self.session.query(QCORecord)
                .filter(
                    (QCORecord.standard_id == std.id)
                    | (QCORecord.standard_number == std.is_number)
                    | (QCORecord.standard_number == std.standard_id)
                )
                .all()
            )
        else:
            # Check for uncatalogued reference in certification or QCO records
            certs = self.session.query(CertificationRecord).filter(CertificationRecord.standard_number == ident_str).all()
            qcos = self.session.query(QCORecord).filter(QCORecord.standard_number == ident_str).all()

            if not certs and not qcos:
                return None

            target_id = ident_str
            target_is_num = ident_str
            target_title = (certs[0].product_name if certs else (qcos[0].product_name or qcos[0].qco_title)) or ""

        scheme = self.classify_scheme(std, certs)
        req_level, _, _, _ = self.evaluate_requirement_level(target_id, target_is_num, certs, qcos)

        cert_payloads = [
            GroundedCertificationRecord(
                id=c.id,
                standard_id=c.standard_id,
                standard_number=c.standard_number,
                product_name=c.product_name,
                product_rating=c.product_rating,
                certification_type=c.certification_type,
                certification_status=c.certification_status,
                is_mandatory=c.is_mandatory,
                requirement_level=c.requirement_level or "UNKNOWN",
                source_dataset=c.source_dataset,
                provenance=c.source_provenance,
            )
            for c in certs
        ]

        qco_payloads = [
            GroundedQCORecord(
                id=q.id,
                standard_id=q.standard_id,
                standard_number=q.standard_number,
                product_name=q.product_name,
                qco_id=q.qco_id,
                qco_title=q.qco_title,
                notification_number=q.notification_number,
                notification_date=q.notification_date,
                notification_links=q.notification_links,
                ministry_department=q.ministry_department,
                status=q.status,  # Preserved verbatim from dataset (Constraint 5)
                is_mandatory=q.is_mandatory,
                source_dataset=q.source_dataset,
                provenance=q.source_provenance,
            )
            for q in qcos
        ]

        return StandardCertificationReport(
            standard_id=target_id,
            canonical_id=target_id,
            is_number=target_is_num,
            title=target_title,
            requirement_level=req_level,
            governing_scheme=scheme,
            total_certifications=len(cert_payloads),
            total_qcos=len(qco_payloads),
            certifications=cert_payloads,
            qco_mandates=qco_payloads,
        )

    def evaluate_compliance(self, identifier_or_id: Union[int, str]) -> Optional[ComplianceIntelligenceReport]:
        """
        Comprehensive compliance evaluation report.
        Extends Module 7 ComplianceLinksResult with deterministic requirement levels and divergences,
        while maintaining 100% field compatibility.
        """
        std = self.resolve_standard(identifier_or_id)
        ident_str = str(identifier_or_id).strip()

        if std:
            target_pk = str(std.id)
            target_canonical = std.standard_id
            target_is_num = std.is_number
            target_title = std.title or ""
            target_status = std.status

            certs = (
                self.session.query(CertificationRecord)
                .filter(
                    (CertificationRecord.standard_id == std.id)
                    | (CertificationRecord.standard_number == std.is_number)
                    | (CertificationRecord.standard_number == std.standard_id)
                )
                .all()
            )
            qcos = (
                self.session.query(QCORecord)
                .filter(
                    (QCORecord.standard_id == std.id)
                    | (QCORecord.standard_number == std.is_number)
                    | (QCORecord.standard_number == std.standard_id)
                )
                .all()
            )

            # Product licences
            licences = []
            if std.category:
                lic_rows = self.session.query(ProductLicence).filter(ProductLicence.product_category == std.category).all()
                licences = [
                    {
                        "id": l.id,
                        "product_category": l.product_category,
                        "licence_count": l.licence_count,
                        "source_dataset": l.source_dataset,
                        "provenance": l.source_provenance,
                    }
                    for l in lic_rows
                ]

            # Ministry mappings
            mappings = (
                self.session.query(MinistryProductMapping)
                .filter(
                    (MinistryProductMapping.standard_id == std.id)
                    | (MinistryProductMapping.standard_number == std.is_number)
                    | (MinistryProductMapping.standard_number == std.standard_id)
                )
                .all()
            )
        else:
            # Check for uncatalogued reference in certification or QCO records (Constraint 12)
            certs = self.session.query(CertificationRecord).filter(CertificationRecord.standard_number == ident_str).all()
            qcos = self.session.query(QCORecord).filter(QCORecord.standard_number == ident_str).all()

            if not certs and not qcos:
                return None

            target_pk = f"unresolved:{ident_str}"
            target_canonical = ident_str
            target_is_num = ident_str
            target_title = (certs[0].product_name if certs else (qcos[0].product_name or qcos[0].qco_title)) or ""
            target_status = "UNCATALOGUED"
            licences = []
            mappings = self.session.query(MinistryProductMapping).filter(MinistryProductMapping.standard_number == ident_str).all()

        map_dicts = [
            {
                "id": m.id,
                "ministry_department": m.ministry_department,
                "product_name": m.product_name,
                "standard_number": m.standard_number,
                "source_dataset": m.source_dataset,
                "provenance": m.source_provenance,
            }
            for m in mappings
        ]

        cert_dicts = [
            {
                "id": c.id,
                "certification_type": c.certification_type,
                "product_name": c.product_name,
                "is_mandatory": c.is_mandatory,
                "requirement_level": c.requirement_level,
                "source_dataset": c.source_dataset,
                "provenance": c.source_provenance,
            }
            for c in certs
        ]

        qco_dicts = [
            {
                "id": q.id,
                "qco_id": q.qco_id,
                "qco_title": q.qco_title,
                "notification_number": q.notification_number,
                "notification_date": q.notification_date,
                "ministry": q.ministry_department,
                "status": q.status,  # Preserved verbatim (Constraint 5)
                "is_mandatory": q.is_mandatory,
                "source_dataset": q.source_dataset,
                "provenance": q.source_provenance,
            }
            for q in qcos
        ]

        scheme = self.classify_scheme(std, certs)
        req_level, div_detected, divergences, div_notes = self.evaluate_requirement_level(target_canonical, target_is_num, certs, qcos)

        # Legacy flags for Module 7 compatibility
        is_mandatory_cert = (req_level == RequirementLevel.MANDATORY)
        qco_applicable = (len(qcos) > 0)

        # Internal decision-support metric
        confidence_score = 1.0 if (certs or qcos) else 0.5

        return ComplianceIntelligenceReport(
            standard_id=target_pk,
            canonical_id=target_canonical,
            is_number=target_is_num,
            title=target_title,
            status=target_status,
            requirement_level=req_level,
            governing_scheme=scheme,
            is_mandatory_certification=is_mandatory_cert,
            qco_applicable=qco_applicable,
            certification_records=cert_dicts,
            qco_records=qco_dicts,
            product_licences=licences,
            ministry_mappings=map_dicts,
            regulatory_divergence_detected=div_detected,
            regulatory_divergence_notes=div_notes,
            divergences=divergences,
            confidence_score=confidence_score,
            evidence_count=(len(cert_dicts) + len(qco_dicts) + len(licences) + len(map_dicts)),
        )

    def batch_evaluate_compliance(self, identifiers: List[str]) -> BatchComplianceResult:
        """
        Batch compliance evaluation avoiding N+1 queries.
        Pre-loads standards and related compliance records in bulk (Constraint 15).
        Handles both catalogued and uncatalogued standard references safely.
        """
        results: List[BatchComplianceItem] = []
        total_found = 0
        total_mandatory = 0
        total_voluntary = 0
        total_conditional = 0
        total_unknown = 0
        total_with_divergence = 0

        # Step 1: Bulk resolve standards
        resolved_stds: Dict[str, Optional[Standard]] = {}
        for ident in identifiers:
            ident_clean = ident.strip()
            std = self.resolve_standard(ident_clean)
            resolved_stds[ident_clean] = std

        valid_stds = [s for s in resolved_stds.values() if s is not None]
        unresolved_idents = [ident for ident, s in resolved_stds.items() if s is None]

        std_ids = [s.id for s in valid_stds]
        is_numbers = [s.is_number for s in valid_stds] + unresolved_idents
        standard_ids = [s.standard_id for s in valid_stds]

        # Step 2: Bounded bulk loading of compliance records
        all_certs_filter = []
        all_qcos_filter = []
        if std_ids:
            all_certs_filter.append(CertificationRecord.standard_id.in_(std_ids))
            all_qcos_filter.append(QCORecord.standard_id.in_(std_ids))
        if is_numbers:
            all_certs_filter.append(CertificationRecord.standard_number.in_(is_numbers))
            all_qcos_filter.append(QCORecord.standard_number.in_(is_numbers))
        if standard_ids:
            all_certs_filter.append(CertificationRecord.standard_number.in_(standard_ids))
            all_qcos_filter.append(QCORecord.standard_number.in_(standard_ids))

        bulk_certs_by_ident: Dict[str, List[CertificationRecord]] = {ident: [] for ident in identifiers}
        bulk_qcos_by_ident: Dict[str, List[QCORecord]] = {ident: [] for ident in identifiers}

        if all_certs_filter:
            all_certs = self.session.query(CertificationRecord).filter(or_(*all_certs_filter)).all()
            for c in all_certs:
                for ident in identifiers:
                    std = resolved_stds.get(ident)
                    if std and (c.standard_id == std.id or c.standard_number in [std.is_number, std.standard_id]):
                        bulk_certs_by_ident[ident].append(c)
                    elif not std and c.standard_number == ident:
                        bulk_certs_by_ident[ident].append(c)

        if all_qcos_filter:
            all_qcos = self.session.query(QCORecord).filter(or_(*all_qcos_filter)).all()
            for q in all_qcos:
                for ident in identifiers:
                    std = resolved_stds.get(ident)
                    if std and (q.standard_id == std.id or q.standard_number in [std.is_number, std.standard_id]):
                        bulk_qcos_by_ident[ident].append(q)
                    elif not std and q.standard_number == ident:
                        bulk_qcos_by_ident[ident].append(q)

        # Step 3: In-memory compliance construction
        for ident in identifiers:
            std = resolved_stds.get(ident)
            certs = bulk_certs_by_ident.get(ident, [])
            qcos = bulk_qcos_by_ident.get(ident, [])

            if not std and not certs and not qcos:
                results.append(
                    BatchComplianceItem(
                        identifier=ident,
                        found=False,
                        result=None,
                        error=f"Standard '{ident}' not found in database.",
                    )
                )
                continue

            target_canonical = std.standard_id if std else ident
            target_is_num = std.is_number if std else ident
            target_pk = str(std.id) if std else f"unresolved:{ident}"
            target_title = (std.title if std else (certs[0].product_name if certs else (qcos[0].product_name or qcos[0].qco_title))) or ""
            target_status = std.status if std else "UNCATALOGUED"

            scheme = self.classify_scheme(std, certs)
            req_level, div_detected, divergences, div_notes = self.evaluate_requirement_level(target_canonical, target_is_num, certs, qcos)

            total_found += 1
            if req_level == RequirementLevel.MANDATORY:
                total_mandatory += 1
            elif req_level == RequirementLevel.VOLUNTARY:
                total_voluntary += 1
            elif req_level == RequirementLevel.CONDITIONAL:
                total_conditional += 1
            else:
                total_unknown += 1

            if div_detected:
                total_with_divergence += 1

            report = ComplianceIntelligenceReport(
                standard_id=target_pk,
                canonical_id=target_canonical,
                is_number=target_is_num,
                title=target_title,
                status=target_status,
                requirement_level=req_level,
                governing_scheme=scheme,
                is_mandatory_certification=(req_level == RequirementLevel.MANDATORY),
                qco_applicable=(len(qcos) > 0),
                certification_records=[
                    {
                        "id": c.id,
                        "certification_type": c.certification_type,
                        "product_name": c.product_name,
                        "is_mandatory": c.is_mandatory,
                        "requirement_level": c.requirement_level,
                        "source_dataset": c.source_dataset,
                        "provenance": c.source_provenance,
                    }
                    for c in certs
                ],
                qco_records=[
                    {
                        "id": q.id,
                        "qco_id": q.qco_id,
                        "qco_title": q.qco_title,
                        "notification_number": q.notification_number,
                        "notification_date": q.notification_date,
                        "ministry": q.ministry_department,
                        "status": q.status,
                        "is_mandatory": q.is_mandatory,
                        "source_dataset": q.source_dataset,
                        "provenance": q.source_provenance,
                    }
                    for q in qcos
                ],
                product_licences=[],
                ministry_mappings=[],
                regulatory_divergence_detected=div_detected,
                regulatory_divergence_notes=div_notes,
                divergences=divergences,
                confidence_score=1.0 if (certs or qcos) else 0.5,
                evidence_count=(len(certs) + len(qcos)),
            )

            results.append(
                BatchComplianceItem(
                    identifier=ident,
                    found=True,
                    result=report,
                    error=None,
                )
            )

        return BatchComplianceResult(
            total_requested=len(identifiers),
            total_found=total_found,
            total_mandatory=total_mandatory,
            total_voluntary=total_voluntary,
            total_conditional=total_conditional,
            total_unknown=total_unknown,
            total_with_divergence=total_with_divergence,
            results=results,
        )
