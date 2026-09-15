"""
Master Ingestion Pipeline Orchestrator for PS 26108.
Coordinates the end-to-end loading, validation, linkage resolution,
conflict tracking, and reporting across all 12 supplied datasets.
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session
from backend.app.core.database import Base, get_engine
from backend.app.models import (
    Standard,
    StandardRelationship,
    CertificationRecord,
    QCORecord,
    MinistryProductMapping,
)
from backend.app.services.ingestion.context import IngestionContext
from backend.app.services.ingestion.manifest_importer import import_manifest
from backend.app.services.ingestion.standards_importer import (
    import_standards_csv,
    import_sample_standards_json,
)
from backend.app.services.ingestion.relationships_importer import import_relationships_json
from backend.app.services.ingestion.compliance_importer import (
    import_schem_csv,
    import_certification_csv,
    import_bis_standards_csv,
    import_report_excel_csv,
)
from backend.app.services.ingestion.product_licence_importer import import_product_licences
from backend.app.services.ingestion.ministry_importer import import_ministry_mappings
from backend.app.services.ingestion.queries_importer import import_evaluation_queries

logger = logging.getLogger("ingestion.pipeline")


class IngestionPipeline:
    """Master orchestrator for multi-source BIS data ingestion."""

    def __init__(self, session: Session, data_dir: str):
        self.session = session
        self.data_dir = data_dir
        self.ctx = IngestionContext(session)

    def _resolve_file(self, filename: str) -> str:
        """Resolve path to a dataset file inside data_dir or search fallback."""
        direct = os.path.join(self.data_dir, filename)
        if os.path.exists(direct):
            return direct
        # Fallback check in Skill-Connect/csvfiles or csvfiles
        for alt_sub in ["Skill-Connect/csvfiles", "csvfiles", "Skill-Connect", "."]:
            p = os.path.join(alt_sub, filename)
            if os.path.exists(p):
                return p
        return direct

    def run(self) -> Dict[str, Any]:
        """Execute the complete 12-dataset ingestion pipeline."""
        start_time = datetime.utcnow()
        logger.info("Starting BIS Dataset Ingestion Pipeline...")

        # Step 1: Manifest
        manifest_file = self._resolve_file("manifest.json")
        import_manifest(manifest_file, self.ctx)
        self.session.flush()

        # Step 2: standards.csv
        standards_csv = self._resolve_file("standards.csv")
        import_standards_csv(standards_csv, self.ctx)
        self.session.flush()

        # Step 3: sample_standards.json
        sample_json = self._resolve_file("sample_standards.json")
        import_sample_standards_json(sample_json, self.ctx)
        self.session.flush()

        # Step 4: relationships.json
        rel_json = self._resolve_file("relationships.json")
        import_relationships_json(rel_json, self.ctx)
        self.session.flush()

        # Step 5: schem.csv
        schem_csv = self._resolve_file("schem.csv")
        import_schem_csv(schem_csv, self.ctx)
        self.session.flush()

        # Step 6: certification.csv
        cert_csv = self._resolve_file("certification.csv")
        import_certification_csv(cert_csv, self.ctx)
        self.session.flush()

        # Step 7: bis_standards.csv
        bis_std_csv = self._resolve_file("bis_standards.csv")
        import_bis_standards_csv(bis_std_csv, self.ctx)
        self.session.flush()

        # Step 8: ReportExcel.csv
        report_excel_csv = self._resolve_file("ReportExcel.csv")
        import_report_excel_csv(report_excel_csv, self.ctx)
        self.session.flush()

        # Step 9: productlicence.csv & bis_standards.json
        prod_lic_csv = self._resolve_file("productlicence.csv")
        bis_std_json = self._resolve_file("bis_standards.json")
        import_product_licences(prod_lic_csv, bis_std_json, self.ctx)
        self.session.flush()

        # Step 10: upcomming.csv
        upcomming_csv = self._resolve_file("upcomming.csv")
        import_ministry_mappings(upcomming_csv, self.ctx)
        self.session.flush()

        # Step 11: query_dataset.json
        query_json = self._resolve_file("query_dataset.json")
        import_evaluation_queries(query_json, self.ctx)
        self.session.flush()

        # Step 12: Post-ingestion foreign key resolution pass
        self._resolve_pending_foreign_keys()

        # Commit transaction
        self.session.commit()
        end_time = datetime.utcnow()
        duration_s = (end_time - start_time).total_seconds()

        logger.info(f"Ingestion completed successfully in {duration_s:.2f} seconds.")
        return self.generate_report_dict(duration_s)

    def _resolve_pending_foreign_keys(self):
        """Second-pass to resolve foreign keys for records whose standards were added later."""
        logger.info("Resolving pending foreign key linkages...")

        # 1. Unlinked StandardRelationships
        unlinked_rels = (
            self.session.query(StandardRelationship)
            .filter(StandardRelationship.target_standard_id.is_(None))
            .all()
        )
        resolved_rels = 0
        for rel in unlinked_rels:
            std_id = self.ctx.find_standard_id(rel.target_standard_number)
            if std_id:
                rel.target_standard_id = std_id
                resolved_rels += 1

        # 2. Unlinked CertificationRecords
        unlinked_certs = (
            self.session.query(CertificationRecord)
            .filter(CertificationRecord.standard_id.is_(None))
            .all()
        )
        resolved_certs = 0
        for cert in unlinked_certs:
            std_id = self.ctx.find_standard_id(cert.standard_number)
            if std_id:
                cert.standard_id = std_id
                resolved_certs += 1

        # 3. Unlinked QCORecords
        unlinked_qco = (
            self.session.query(QCORecord)
            .filter(QCORecord.standard_id.is_(None))
            .all()
        )
        resolved_qco = 0
        for qco in unlinked_qco:
            std_id = self.ctx.find_standard_id(qco.standard_number)
            if std_id:
                qco.standard_id = std_id
                resolved_qco += 1

        # 4. Unlinked MinistryProductMappings
        unlinked_min = (
            self.session.query(MinistryProductMapping)
            .filter(MinistryProductMapping.standard_id.is_(None))
            .all()
        )
        resolved_min = 0
        for mp in unlinked_min:
            std_id = self.ctx.find_standard_id(mp.standard_number)
            if std_id:
                mp.standard_id = std_id
                resolved_min += 1

        self.session.flush()
        logger.info(
            f"Pass 2 resolved: {resolved_rels} relationships, {resolved_certs} certs, "
            f"{resolved_qco} QCOs, {resolved_min} ministry mappings."
        )

    def generate_report_dict(self, duration_seconds: float) -> Dict[str, Any]:
        """Compile comprehensive statistics and audit summary."""
        s = self.ctx.stats

        total_standards = self.session.query(Standard).count()
        total_explicit_rels = (
            self.session.query(StandardRelationship)
            .filter_by(is_explicit_source=True)
            .count()
        )
        total_derived_rels = (
            self.session.query(StandardRelationship)
            .filter_by(is_explicit_source=False)
            .count()
        )
        total_certs = self.session.query(CertificationRecord).count()
        total_qcos = self.session.query(QCORecord).count()
        linked_qcos = (
            self.session.query(QCORecord)
            .filter(QCORecord.standard_id.isnot(None))
            .count()
        )
        linked_certs = (
            self.session.query(CertificationRecord)
            .filter(CertificationRecord.standard_id.isnot(None))
            .count()
        )

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "duration_seconds": duration_seconds,
            "files_processed": s.files_processed,
            "entity_counts": {
                "total_standards": total_standards,
                "standards_created": s.standards_created,
                "standards_updated": s.standards_updated,
                "departments_created": s.departments_created,
                "explicit_relationships": total_explicit_rels,
                "derived_relationships": total_derived_rels,
                "standard_versions": s.versions_created,
                "qco_records": total_qcos,
                "qco_linked_to_standards": linked_qcos,
                "certification_records": total_certs,
                "certification_linked_to_standards": linked_certs,
                "product_licence_categories": s.product_licences_created,
                "ministry_product_mappings": s.ministry_mappings_created,
                "evaluation_queries": s.queries_created,
                "source_documents": s.source_documents_created,
            },
            "unresolved_relationships_count": len(s.unresolved_relationships),
            "unresolved_relationships_sample": s.unresolved_relationships[:20],
            "conflicts_identified_count": len(s.conflicts),
            "conflicts_sample": [
                {
                    "entity": f"{c.entity_type}:{c.entity_id}",
                    "field": c.field_name,
                    "existing": f"{c.existing_source}={c.existing_value}",
                    "incoming": f"{c.incoming_source}={c.incoming_value}",
                    "resolution": c.resolution,
                }
                for c in s.conflicts[:20]
            ],
            "ambiguities_identified_count": len(s.ambiguities),
            "ambiguities_sample": [
                {
                    "standard_number": a.standard_number,
                    "title": a.title,
                    "description": a.description,
                }
                for a in s.ambiguities[:20]
            ],
        }

    def generate_markdown_report(self, report_dict: Dict[str, Any]) -> str:
        """Format the ingestion report into professional GitHub-Flavored Markdown."""
        lines = [
            "# BIS AI Recommendation Engine — Dataset Ingestion & Validation Report",
            "",
            f"**Execution Timestamp**: `{report_dict['timestamp']}`  ",
            f"**Total Duration**: `{report_dict['duration_seconds']:.2f} seconds`  ",
            "",
            "## 1. Datasets Processed (12 of 12 Authoritative Files)",
            "",
            "| Dataset File | Processed Records | Role / Target Entity |",
            "|:---|:---:|:---|",
        ]

        roles = {
            "manifest.json": "Source Document Provenance (`SourceDocument`)",
            "standards.csv": "Core Indian Standards (`Standard`, `StandardVersion`)",
            "sample_standards.json": "Detailed Standards, Normative Refs (`Standard`, `StandardRelationship`)",
            "relationships.json": "Explicit Domain Knowledge Graph Edges (`StandardRelationship`)",
            "schem.csv": "Quality Control Orders / QCO Compliance (`QCORecord`)",
            "certification.csv": "ISI Mark Certification Products (`CertificationRecord`)",
            "bis_standards.csv": "Compulsory Registration Scheme / IT (`CertificationRecord`, `ProcurementAlias`)",
            "ReportExcel.csv": "Mandatory vs Voluntary Status (`CertificationRecord`)",
            "productlicence.csv": "Product Licence Counts (`ProductLicence`)",
            "bis_standards.json": "Licence Count Cross-Verification (`ProductLicence`)",
            "upcomming.csv": "Ministry / Department Product Standards (`MinistryProductMapping`, `ProcurementAlias`)",
            "query_dataset.json": "Benchmark Evaluation Queries (`EvaluationQuery`)",
        }

        for fname, cnt in report_dict["files_processed"].items():
            role = roles.get(fname, "Domain Data")
            lines.append(f"| `{fname}` | {cnt:,} | {role} |")

        ec = report_dict["entity_counts"]
        lines.extend([
            "",
            "## 2. Ingested Database Entities & Statistics",
            "",
            "| Entity Name | Database Table | Count | Linkage / Notes |",
            "|:---|:---|:---:|:---|",
            f"| **Indian Standards** | `standards` | **{ec['total_standards']:,}** | {ec['standards_created']} created, {ec['standards_updated']} merged |",
            f"| **Explicit Relationships** | `standard_relationships` | **{ec['explicit_relationships']:,}** | Source: `relationships.json` (`is_explicit_source=True`) |",
            f"| **Derived Relationships** | `standard_relationships` | **{ec['derived_relationships']:,}** | Source: `normative_references`, `supersedes` (`is_explicit_source=False`) |",
            f"| **Standard Versions & Amendments** | `standard_versions` | **{ec['standard_versions']:,}** | Version history and formal amendment tracking |",
            f"| **Quality Control Orders (QCO)** | `qco_records` | **{ec['qco_records']:,}** | {ec['qco_linked_to_standards']} linked to standards table |",
            f"| **Certification Records** | `certification_records` | **{ec['certification_records']:,}** | {ec['certification_linked_to_standards']} linked to standards table |",
            f"| **Product Licences** | `product_licences` | **{ec['product_licence_categories']:,}** | Factual counts (strictly non-equated to mandatory) |",
            f"| **Ministry Product Mappings** | `ministry_product_mappings` | **{ec['ministry_product_mappings']:,}** | Government departmental context |",
            f"| **Technical Committees / Departments** | `departments` | **{ec['departments_created']:,}** | ETD, CED, MED technical bodies |",
            f"| **Source Documents** | `source_documents` | **{ec['source_documents']:,}** | Document provenance anchors from manifest |",
            f"| **Evaluation Queries** | `evaluation_queries` | **{ec['evaluation_queries']:,}** | Ground-truth test benchmark suite |",
            "",
            "## 3. Provenance & Conflict Resolution Audit",
            "",
            f"- **Total Identified Conflicts**: `{report_dict['conflicts_identified_count']}`",
            "- **Policy**: Non-silent conflict tracking. All field discrepancies between different datasets are recorded in `source_provenance['conflicts']` and preserved for auditability.",
            "",
        ])

        if report_dict["conflicts_sample"]:
            lines.extend([
                "| Entity | Field | Existing Source & Value | Incoming Source & Value | Resolution |",
                "|:---|:---|:---|:---|:---|",
            ])
            for c in report_dict["conflicts_sample"][:10]:
                lines.append(f"| `{c['entity']}` | `{c['field']}` | `{c['existing']}` | `{c['incoming']}` | {c['resolution']} |")
            lines.append("")

        lines.extend([
            "## 4. Compliance Ambiguity Identification",
            "",
            f"- **Total Ambiguities Flagged**: `{report_dict['ambiguities_identified_count']}`",
            "- **Key Regulatory Ambiguity**: Standards marked as `'Voluntary'` in `ReportExcel.csv` that also appear under an active Quality Control Order in `schem.csv`.",
            "- **System Recommendation**: When tenders specify these standards, the AI engine flags them with high-priority audit alerts indicating the regulatory divergence.",
            "",
        ])

        if report_dict["ambiguities_sample"]:
            lines.extend([
                "| Standard Number | Standard Title | Regulatory Divergence Description |",
                "|:---|:---|:---|",
            ])
            for a in report_dict["ambiguities_sample"][:10]:
                lines.append(f"| `{a['standard_number']}` | {a['title'][:45]}... | {a['description']} |")
            lines.append("")

        lines.extend([
            "## 5. Unresolved Cross-References",
            "",
            f"- **Total Unresolved Cross-References**: `{report_dict['unresolved_relationships_count']}`",
            "- **Status**: Safely preserved as string targets in `StandardRelationship` with `target_standard_id = NULL` to prevent data loss when external standards are cited.",
            "",
            "---",
            "*Report generated automatically by PS 26108 Ingestion Pipeline.*",
        ])

        return "\n".join(lines)
