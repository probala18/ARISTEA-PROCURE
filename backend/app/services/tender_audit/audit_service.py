"""
Tender Audit Orchestrator Service (Module 12).
Provides interface for auditing tender documents, caching results in tender_audit_results,
and retrieving existing audit reports.
"""
import logging
from typing import Optional
from sqlalchemy.orm import Session

from backend.app.models.tender import TenderDocument, TenderAuditResult
from backend.app.services.tender_audit.schemas import (
    TenderAuditReport,
    ExpectedVsPresentComparison,
    TenderGapItem,
)
from backend.app.services.tender_audit.gap_analyzer import TenderGapAnalyzer

logger = logging.getLogger(__name__)


class TenderAuditService:
    """Service orchestrating evidence-based tender auditing."""

    def __init__(self, db_session: Session):
        self.db = db_session
        self.analyzer = TenderGapAnalyzer(db_session)

    def audit_tender(self, tender_id: int, force_recompute: bool = False) -> TenderAuditReport:
        """
        Executes audit on specified tender document and persists audit results.
        If already audited and force_recompute=False, returns cached audit report.
        """
        tender = self.db.query(TenderDocument).filter(TenderDocument.id == tender_id).first()
        if not tender:
            raise ValueError(f"Tender document ID {tender_id} not found.")

        # Check existing audit cache if not forced
        if not force_recompute:
            existing_audit = self.db.query(TenderAuditResult).filter(
                TenderAuditResult.tender_id == tender_id
            ).first()
            if existing_audit and existing_audit.audit_report:
                try:
                    return TenderAuditReport(**existing_audit.audit_report)
                except Exception as e:
                    logger.warning(f"Failed to deserialize cached audit result for tender {tender_id}: {e}")

        # Run fresh gap analysis
        report = self.analyzer.analyze_tender(tender)

        # Persist or update audit result
        audit_record = self.db.query(TenderAuditResult).filter(
            TenderAuditResult.tender_id == tender_id
        ).first()

        report_dict = report.model_dump(mode="json")

        if not audit_record:
            audit_record = TenderAuditResult(
                tender_id=tender.id,
                audit_summary={"summary_text": report.audit_summary},
                expected_standards=report.expected_vs_present.expected_standards,
                missing_standards=report.expected_vs_present.missing_standards,
                outdated_standards=report.expected_vs_present.outdated_standards,
                testing_gaps=report.expected_vs_present.testing_gaps,
                safety_gaps=report.expected_vs_present.safety_gaps,
                certification_gaps=report.expected_vs_present.certification_gaps,
                coverage_score=report.coverage_score,
                audit_report=report_dict,
            )
            self.db.add(audit_record)
        else:
            audit_record.audit_summary = {"summary_text": report.audit_summary}
            audit_record.expected_standards = report.expected_vs_present.expected_standards
            audit_record.missing_standards = report.expected_vs_present.missing_standards
            audit_record.outdated_standards = report.expected_vs_present.outdated_standards
            audit_record.testing_gaps = report.expected_vs_present.testing_gaps
            audit_record.safety_gaps = report.expected_vs_present.safety_gaps
            audit_record.certification_gaps = report.expected_vs_present.certification_gaps
            audit_record.coverage_score = report.coverage_score
            audit_record.audit_report = report_dict

        # Update tender status
        tender.status = "AUDITED"
        self.db.commit()
        self.db.refresh(audit_record)

        return report
