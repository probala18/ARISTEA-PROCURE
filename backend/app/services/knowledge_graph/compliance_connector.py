"""
Compliance Connector Service for Module 4.
Links knowledge graph nodes to:
- Certification records (ISI/CRS schemes, licence counts, voluntary vs mandatory)
- QCO records (Quality Control Orders, gazette dates, enforcing ministries)
- Product licence counts
- Ministry / Department procurement mappings
Detects regulatory divergence (e.g. Voluntary in ReportExcel vs Mandatory in QCO).
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.models.standard import Standard
from backend.app.models.compliance import CertificationRecord, QCORecord, ProductLicence
from backend.app.models.department import MinistryProductMapping
from backend.app.services.knowledge_graph.graph_models import ComplianceLinksResult


class ComplianceConnectorService:
    """Connects standard graph nodes to regulatory, compliance, and ministerial records."""

    def __init__(self, session: Session):
        self.session = session

    def get_compliance_links(self, standard_id: int) -> ComplianceLinksResult:
        """
        Gathers all grounded compliance evidence for the specified standard:
        - Certification records
        - QCO mandate records
        - Product licences
        - Ministry product mappings
        - Flags regulatory divergence
        """
        std = self.session.query(Standard).get(standard_id)
        if not std:
            return ComplianceLinksResult(
                standard_id=str(standard_id),
                canonical_id="UNKNOWN",
            )

        # 1. Certification records
        certs = (
            self.session.query(CertificationRecord)
            .filter(
                (CertificationRecord.standard_id == std.id) |
                (CertificationRecord.standard_number == std.is_number) |
                (CertificationRecord.standard_number == std.standard_id)
            )
            .all()
        )
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

        # 2. QCO records
        qcos = (
            self.session.query(QCORecord)
            .filter(
                (QCORecord.standard_id == std.id) |
                (QCORecord.standard_number == std.is_number) |
                (QCORecord.standard_number == std.standard_id)
            )
            .all()
        )
        qco_dicts = [
            {
                "id": q.id,
                "qco_name": q.qco_title or q.qco_id,
                "ministry": q.ministry_department,
                "notification_number": q.notification_number,
                "notification_date": q.notification_date,
                "is_mandatory": q.is_mandatory,
                "source_dataset": q.source_dataset,
                "provenance": q.source_provenance,
            }
            for q in qcos
        ]

        # 3. Product Licences (matched via category or product keywords)
        lic_query = self.session.query(ProductLicence)
        if std.category:
            lic_query = lic_query.filter(
                (ProductLicence.product_category.ilike(f"%{std.category}%")) |
                (ProductLicence.product_category.ilike(f"%{std.is_number}%"))
            )
        else:
            lic_query = lic_query.filter(ProductLicence.product_category.ilike(f"%{std.is_number}%"))
        licences = lic_query.all()
        lic_dicts = [
            {
                "id": l.id,
                "product_category": l.product_category,
                "licence_count": l.licence_count,
                "source_dataset": l.source_dataset,
            }
            for l in licences
        ]

        # 4. Ministry Product Mappings
        mappings = (
            self.session.query(MinistryProductMapping)
            .filter(
                (MinistryProductMapping.standard_id == std.id) |
                (MinistryProductMapping.standard_number == std.is_number) |
                (MinistryProductMapping.standard_number == std.standard_id)
            )
            .all()
        )
        min_dicts = [
            {
                "id": m.id,
                "ministry_name": m.ministry_name,
                "department_name": m.department_name,
                "product_category": m.product_category,
                "procurement_context": m.procurement_context,
                "source_dataset": m.source_dataset,
            }
            for m in mappings
        ]

        # 5. Regulatory Divergence Audit
        divergence_detected = False
        divergence_notes = []

        # Check if certification is marked Voluntary in ReportExcel while QCO list mandates it
        has_voluntary_cert = any(c.requirement_level == "VOLUNTARY" for c in certs)
        has_mandatory_qco = any(q.is_mandatory for q in qcos) or std.qco_applicable

        if has_voluntary_cert and has_mandatory_qco:
            divergence_detected = True
            divergence_notes.append(
                f"Standard '{std.standard_id}' has voluntary certification in ReportExcel.csv but is covered by mandatory QCO order in schem.csv."
            )

        return ComplianceLinksResult(
            standard_id=str(std.id),
            canonical_id=std.standard_id,
            is_mandatory_certification=std.is_mandatory_certification,
            qco_applicable=std.qco_applicable,
            certification_records=cert_dicts,
            qco_records=qco_dicts,
            product_licences=lic_dicts,
            ministry_mappings=min_dicts,
            regulatory_divergence_detected=divergence_detected,
            regulatory_divergence_notes=divergence_notes,
        )
