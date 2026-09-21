"""
Version Intelligence Service for Module 8.
Consolidates version records, amendments, supersession lineage, and currency intelligence.

Strictly enforces:
1. Module 4's SupersessionChainService is the single source of truth for supersession relationships.
2. StandardVersion table (Module 2) is the source for version and amendment records — no duplicated tables.
3. Standard.status is the primary status signal.
4. OUTDATED_VERSION_WARNING is NOT triggered merely because latest_year != publication_year.
   A later latest year indicates a revision, amendment, or version gap.
5. Evidence-grounded concepts: CURRENT, SUPERSEDED, AMENDMENT_AVAILABLE, VERSION_GAP, UNKNOWN_VERSION_STATUS.
6. For SUPERSEDED_WARNING, successor info is included only when Module 4 explicitly establishes it.
7. For AMENDMENT_AVAILABLE, identifies the actual StandardVersion amendment record(s).
8. Every version, amendment, warning, and supersession carries source provenance.
9. Distinguishes 'latest version information available in dataset' from 'legally current standard'.
10. Dual lookup: canonical standard ID, normalized standard number, or integer DB PK.
11. Historical/uncatalogued references are handled safely without manufacturing synthetic Standard rows.
"""
import json
from typing import List, Dict, Any, Optional, Union
from sqlalchemy.orm import Session

from backend.app.models.standard import Standard
from backend.app.models.version import StandardVersion
from backend.app.services.knowledge_graph.supersession_service import SupersessionChainService
from backend.app.services.relationship_engine.engine import RelationshipEngine
from backend.app.services.version_intelligence.schemas import (
    WarningType,
    AmendmentRecord,
    VersionWarning,
    CurrencyCheckResult,
    VersionIntelligenceReport,
    BatchCurrencyItem,
    BatchCurrencyResult,
)


class VersionIntelligenceService:
    """Service providing version, amendment, supersession, and dataset currency intelligence."""

    def __init__(self, session: Session):
        self.session = session
        self.engine = RelationshipEngine(session)
        self.supersession_service = SupersessionChainService(session)

    def resolve_standard(self, identifier_or_id: Union[int, str]) -> Optional[Standard]:
        """
        Resolves integer DB ID, canonical standard ID (e.g. 'IS 12615:2018'),
        or normalized standard number (e.g. 'IS 12615') to canonical Standard entity.
        Returns None if not catalogued. Never manufactures synthetic Standard rows.
        """
        return self.engine.resolve_standard(identifier_or_id)

    def get_amendments(self, standard_id_or_number: Union[int, str]) -> List[AmendmentRecord]:
        """
        Retrieves amendment-specific records from StandardVersion where
        amendment_number or amendment_year is set.
        Preserves full provenance (source_dataset, source_provenance).
        """
        std = self.resolve_standard(standard_id_or_number)
        if not std:
            return []

        rows = (
            self.session.query(StandardVersion)
            .filter(
                StandardVersion.standard_id == std.id,
                (
                    (StandardVersion.amendment_number.isnot(None))
                    | (StandardVersion.amendment_year.isnot(None))
                    | (StandardVersion.change_description.isnot(None))
                ),
            )
            .order_by(StandardVersion.amendment_number.asc().nullslast(), StandardVersion.amendment_year.asc().nullslast())
            .all()
        )

        records: List[AmendmentRecord] = []
        for r in rows:
            prov = r.source_provenance
            if isinstance(prov, str):
                try:
                    prov = json.loads(prov)
                except Exception:
                    prov = {"raw": prov}

            # An amendment record must have at least one amendment signal or change description
            records.append(
                AmendmentRecord(
                    id=r.id,
                    standard_id=r.standard_id,
                    is_number=r.is_number,
                    amendment_number=r.amendment_number,
                    amendment_year=r.amendment_year,
                    change_description=r.change_description,
                    current_state=r.current_state or "CURRENT",
                    source_dataset=r.source_dataset or "standards.csv",
                    source_provenance=prov,
                )
            )
        return records

    def check_currency(self, standard_id_or_number: Union[int, str]) -> Optional[CurrencyCheckResult]:
        """
        Performs dataset-backed version/status intelligence check.
        Primary status signal is Standard.status (CURRENT vs SUPERSEDED).
        Never claims to independently establish legal or regulatory currency.
        """
        std = self.resolve_standard(standard_id_or_number)
        if not std:
            return None

        # Fetch all version records for this standard from StandardVersion table
        versions = (
            self.session.query(StandardVersion)
            .filter(StandardVersion.standard_id == std.id)
            .all()
        )

        warnings: List[VersionWarning] = []
        amendment_records = self.get_amendments(std.id)

        # 1. Primary status signal: Standard.status
        is_current = (std.status == "CURRENT")

        # 2. Check for missing version records: UNKNOWN_VERSION_STATUS
        if len(versions) == 0:
            warnings.append(
                VersionWarning(
                    warning_type=WarningType.UNKNOWN_VERSION_STATUS,
                    message=(
                        f"No version records were ingested for standard '{std.standard_id}' "
                        f"in the active dataset. Version status cannot be verified from dataset."
                    ),
                    severity="INFO",
                    evidence={
                        "standard_id": std.standard_id,
                        "standard_pk": std.id,
                        "version_records_count": 0,
                    },
                    source_dataset=std.source_file or "unknown",
                )
            )

        # 3. Supersession Warning: grounded in Standard.status and Module 4 supersession graph
        if std.status == "SUPERSEDED":
            chain = self.supersession_service.get_supersession_chain(std.id)
            # Successor standards from Module 4 graph
            successors = chain.superseded_by
            if successors:
                succ_names = [s.get("canonical_id") or str(s.get("standard_id")) for s in successors]
                msg = (
                    f"Standard '{std.standard_id}' is marked SUPERSEDED in the dataset. "
                    f"Successor standard(s) identified in graph: {', '.join(succ_names)}."
                )
            else:
                msg = (
                    f"Standard '{std.standard_id}' is marked SUPERSEDED in the dataset, "
                    f"but no successor standard is explicitly recorded in the graph."
                )

            warnings.append(
                VersionWarning(
                    warning_type=WarningType.SUPERSEDED_WARNING,
                    message=msg,
                    severity="CRITICAL",
                    evidence={
                        "status": std.status,
                        "successors": successors,
                        "has_cycle": chain.has_cycle,
                        "provenance": {
                            "source_table": "standards",
                            "field": "status",
                            "source_file": std.source_file,
                        },
                    },
                    source_dataset=std.source_file or "standards.csv",
                )
            )

        # 4. Amendment Available Warning: identify actual StandardVersion amendment records
        if amendment_records:
            evidence_amendments = [
                {
                    "id": a.id,
                    "amendment_number": a.amendment_number,
                    "amendment_year": a.amendment_year,
                    "change_description": a.change_description,
                    "source_dataset": a.source_dataset,
                    "source_provenance": a.source_provenance,
                }
                for a in amendment_records
            ]
            warnings.append(
                VersionWarning(
                    warning_type=WarningType.AMENDMENT_AVAILABLE,
                    message=(
                        f"Standard '{std.standard_id}' has {len(amendment_records)} amendment record(s) "
                        f"available in the dataset."
                    ),
                    severity="INFO",
                    evidence={
                        "amendment_count": len(amendment_records),
                        "amendments": evidence_amendments,
                    },
                    source_dataset=amendment_records[0].source_dataset,
                )
            )

        # 5. Version Gap Detection (Constraint #4: NOT labeled as OUTDATED_VERSION_WARNING)
        # Check if latest_year in version records differs from publication_year, or gap exists
        latest_year_candidates = [
            v.latest_year for v in versions if v.latest_year is not None
        ] + [v.version_year for v in versions if v.version_year is not None]
        if std.publication_year is not None:
            latest_year_candidates.append(std.publication_year)

        latest_year = max(latest_year_candidates) if latest_year_candidates else std.publication_year

        # Check if version records show a revision/year gap
        for v in versions:
            if v.latest_year is not None and std.publication_year is not None and v.latest_year != std.publication_year:
                warnings.append(
                    VersionWarning(
                        warning_type=WarningType.VERSION_GAP,
                        message=(
                            f"Dataset indicates a version/year interval for '{std.standard_id}': "
                            f"publication year ({std.publication_year}) differs from latest recorded year ({v.latest_year})."
                        ),
                        severity="INFO",
                        evidence={
                            "publication_year": std.publication_year,
                            "latest_year": v.latest_year,
                            "version_id": v.id,
                            "source_dataset": v.source_dataset,
                        },
                        source_dataset=v.source_dataset,
                    )
                )
                break

        return CurrencyCheckResult(
            standard_id=std.standard_id,
            canonical_id=std.standard_id,
            is_number=std.is_number,
            title=std.title or "",
            status=std.status or "CURRENT",
            publication_year=std.publication_year,
            latest_year=latest_year,
            is_current=is_current,
            warnings=warnings,
            total_amendments=len(amendment_records),
        )

    def get_version_report(self, standard_id_or_number: Union[int, str]) -> Optional[VersionIntelligenceReport]:
        """
        Consolidates complete version intelligence report:
        - Version records from StandardVersion
        - Amendment records with full provenance
        - Supersession chain from Module 4 SupersessionChainService
        - Currency check with evidence-grounded warnings
        """
        std = self.resolve_standard(standard_id_or_number)
        if not std:
            return None

        # Fetch all StandardVersion records
        versions = (
            self.session.query(StandardVersion)
            .filter(StandardVersion.standard_id == std.id)
            .order_by(StandardVersion.version_year.desc().nullslast(), StandardVersion.id.asc())
            .all()
        )

        version_data = [
            {
                "id": v.id,
                "standard_id": v.standard_id,
                "is_number": v.is_number,
                "version_year": v.version_year,
                "latest_year": v.latest_year,
                "amendment_number": v.amendment_number,
                "amendment_year": v.amendment_year,
                "change_description": v.change_description,
                "current_state": v.current_state,
                "superseded_by": v.superseded_by,
                "superseded_state": v.superseded_state,
                "effective_date": v.effective_date,
                "source_dataset": v.source_dataset,
                "source_provenance": v.source_provenance,
                "created_at": v.created_at.isoformat() if v.created_at else None,
            }
            for v in versions
        ]

        amendments = self.get_amendments(std.id)
        currency = self.check_currency(std.id)

        # Supersession chain from Module 4
        chain = self.supersession_service.get_supersession_chain(std.id)
        supersession_data = {
            "standard_id": chain.standard_id,
            "canonical_id": chain.canonical_id,
            "current_status": chain.current_status,
            "supersedes": chain.supersedes,
            "superseded_by": chain.superseded_by,
            "has_cycle": chain.has_cycle,
        }

        return VersionIntelligenceReport(
            standard_id=std.standard_id,
            canonical_id=std.standard_id,
            is_number=std.is_number,
            title=std.title or "",
            status=std.status or "CURRENT",
            publication_year=std.publication_year,
            latest_year=currency.latest_year if currency else std.publication_year,
            version_records=version_data,
            amendments=amendments,
            supersession=supersession_data,
            warnings=currency.warnings if currency else [],
            source_file=std.source_file or "standards.csv",
        )

    def batch_version_check(self, identifiers: List[Union[int, str]]) -> BatchCurrencyResult:
        """
        Performs batch currency checks across multiple standards.
        Safely reports missing identifiers without raising exceptions.
        """
        results: List[BatchCurrencyItem] = []
        total_found = 0
        total_current = 0
        total_with_warnings = 0

        for ident in identifiers:
            ident_str = str(ident).strip()
            currency = self.check_currency(ident)
            if currency:
                total_found += 1
                if currency.is_current:
                    total_current += 1
                if currency.warnings:
                    total_with_warnings += 1
                results.append(
                    BatchCurrencyItem(
                        identifier=ident_str,
                        found=True,
                        result=currency,
                        error=None,
                    )
                )
            else:
                results.append(
                    BatchCurrencyItem(
                        identifier=ident_str,
                        found=False,
                        result=None,
                        error=f"Standard '{ident_str}' not found in database.",
                    )
                )

        return BatchCurrencyResult(
            total_requested=len(identifiers),
            total_found=total_found,
            total_current=total_current,
            total_with_warnings=total_with_warnings,
            results=results,
        )
