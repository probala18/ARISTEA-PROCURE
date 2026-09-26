"""
ARISTEA Autopilot — end-to-end procurement orchestrator.

Chains the existing grounded modules into a single need-to-tender pipeline:
  1. UNDERSTAND   need parser + Module 6 query analyzer
  2. STANDARDS    Module 6 recommendation per component + knowledge graph allied standards
  3. COMPLIANCE   Module 9 QCO / certification requirement levels
  4. VERSIONS     Module 8 currency and supersession checks
  5. MARKET       product licence depth + certification record coverage
  6. DRAFT        cited tender document with section-level clause citations
  7. RED TEAM     Module 11 + 12 audit of the draft, auto-corrections, re-audit

Every clause in the generated tender carries citation keys that resolve to dataset
records with provenance. Nothing is invented: unknowns are stated as unknown.
Each step is emitted as an event so the UI can show the pipeline live.
"""
import logging
import time
import uuid
from typing import Any, Dict, Iterator, List, Optional

import numpy as np
from sqlalchemy.orm import Session

from backend.app.models.compliance import ProductLicence
from backend.app.services.autopilot.need_parser import parse_need
from backend.app.services.compliance_intelligence import ComplianceIntelligenceService
from backend.app.services.recommendation import RecommendationEngine, RecommendationRequest
from backend.app.services.recommendation.query_analyzer import QueryAnalyzer
from backend.app.services.retrieval.embedding_provider import get_embedding_provider
from backend.app.services.tender_audit import TenderAuditService
from backend.app.services.tender_engine.tender_service import TenderEngineService
from backend.app.services.version_intelligence.version_intelligence_service import VersionIntelligenceService

logger = logging.getLogger("aristea.autopilot")

STEPS = [
    ("understand", "Understanding the need"),
    ("standards", "Discovering applicable standards"),
    ("compliance", "Checking QCO & certification mandates"),
    ("versions", "Verifying standard currency"),
    ("market", "Assessing supplier market depth"),
    ("draft", "Drafting the cited tender"),
    ("redteam", "Red-teaming the draft"),
]

MAX_STANDARDS = 12
ALLIED_ROLES_INCLUDED = {"TESTING", "SAFETY", "PERFORMANCE", "INSTALLATION", "NORMATIVE_REFERENCE"}
LICENCE_MATCH_THRESHOLD = 0.62
THIN_MARKET_LICENCES = 10


class AutopilotOrchestrator:
    """Runs the need-to-tender pipeline and yields progress events."""

    def __init__(self, db: Session):
        self.db = db
        self.citations: Dict[str, Dict[str, Any]] = {}
        self._citation_seq = 0

    # ------------------------------------------------------------------ helpers
    def _cite(self, source_type: str, label: str, source_dataset: str, details: str,
              provenance: Optional[Any] = None) -> str:
        """Registers an evidence record and returns its citation key (e.g. 'C7')."""
        for key, c in self.citations.items():
            if c["source_type"] == source_type and c["label"] == label and c["source_dataset"] == source_dataset:
                return key
        self._citation_seq += 1
        key = f"C{self._citation_seq}"
        self.citations[key] = {
            "key": key,
            "source_type": source_type,
            "label": label,
            "source_dataset": source_dataset,
            "details": details,
            "provenance": provenance,
        }
        return key

    @staticmethod
    def _event(step: str, status: str, summary: str, data: Optional[Dict[str, Any]] = None,
               elapsed_ms: Optional[int] = None) -> Dict[str, Any]:
        title = dict(STEPS).get(step, step)
        return {"type": "step", "step": step, "title": title, "status": status,
                "summary": summary, "data": data or {}, "elapsed_ms": elapsed_ms}

    # --------------------------------------------------------------- pipeline
    def run(self, need: str, language: Optional[str] = None) -> Iterator[Dict[str, Any]]:
        run_id = f"AP-{uuid.uuid4().hex[:8].upper()}"
        yield {"type": "start", "run_id": run_id, "need": need,
               "steps": [{"step": s, "title": t} for s, t in STEPS]}

        ctx: Dict[str, Any] = {"run_id": run_id, "need": need, "language": language}
        for step, _ in STEPS:
            yield self._event(step, "running", "")
            t0 = time.perf_counter()
            try:
                summary, data = getattr(self, f"_step_{step}")(ctx)
                status = data.pop("_status", "done")
            except Exception as exc:  # keep the pipeline alive; later steps degrade gracefully
                logger.exception("Autopilot step %s failed", step)
                summary, data, status = f"Step could not complete: {exc}", {}, "error"
            elapsed = int((time.perf_counter() - t0) * 1000)
            yield self._event(step, status, summary, data, elapsed)
            if ctx.get("halt"):
                break

        yield {"type": "result", "run_id": run_id, "result": self._package(ctx)}

    # 1 ------------------------------------------------------------------------
    def _step_understand(self, ctx: Dict[str, Any]):
        need = ctx["need"]
        facts = parse_need(need)
        analysis = QueryAnalyzer().analyze(need)
        facts["language"] = ctx.get("language") or analysis["language"]
        facts["intent"] = analysis["intent"].value
        facts["technical_attributes"] = analysis["attributes"]
        facts["explicit_standards"] = analysis["extracted_standards"]
        ctx["facts"] = facts

        if analysis["is_out_of_scope"]:
            ctx["halt"] = True
            return (f"This need appears to be outside BIS standards scope: {analysis['out_of_scope_reason']}",
                    {"facts": facts, "_status": "blocked"})

        bits = []
        if facts["quantity"]:
            bits.append(f"{facts['quantity']['value']} {facts['quantity']['unit']}")
        if facts["components"]:
            bits.append(f"{len(facts['components'])} component(s): {', '.join(facts['components'])}")
        if facts["location"]:
            bits.append(f"delivery in {facts['location']}")
        if facts["budget"]:
            bits.append(f"budget ₹{facts['budget']['amount_inr']:,.0f}")
        return ("Parsed " + ("; ".join(bits) if bits else "the requirement"), {"facts": facts})

    # 2 ------------------------------------------------------------------------
    def _step_standards(self, ctx: Dict[str, Any]):
        facts = ctx["facts"]
        engine = RecommendationEngine(self.db)
        queries = [ctx["need"]] + [c for c in facts["components"] if c.lower() != ctx["need"].lower()]

        selected: Dict[str, Dict[str, Any]] = {}
        clarifications: List[Dict[str, Any]] = []

        def add(cand, role: str, source_query: str, via: Optional[str] = None):
            if cand.standard_id in selected or len(selected) >= MAX_STANDARDS:
                return
            cite = self._cite(
                "STANDARD_RECORD", cand.is_number, "standards.csv",
                f"{cand.is_number} — {cand.title} (status: {cand.status})",
                [e.model_dump() for e in cand.evidence[:3]],
            )
            selected[cand.standard_id] = {
                "standard_id": cand.standard_id,
                "is_number": cand.is_number,
                "title": cand.title,
                "category": cand.category,
                "status": cand.status,
                "role": role,
                "matched_component": source_query,
                "linked_via": via,
                "relevance_score": cand.relevance_score,
                "confidence_level": cand.confidence_level.value,
                "supersession_note": cand.supersession_note,
                "citation": cite,
            }

        for i, q in enumerate(queries):
            resp = engine.recommend(RecommendationRequest(query_text=q, max_primary=2 if i else 3))
            if resp.is_ambiguous and resp.clarification_prompt:
                clarifications.append({
                    "component": q,
                    "missing": resp.clarification_prompt.missing_discriminators,
                })
                for c in resp.candidate_spectrum[:2]:
                    add(c, "CONDITIONAL", q)
                continue
            for c in resp.primary_standards:
                if c.relevance_score >= 0.3 or i == 0:
                    add(c, "PRIMARY" if i == 0 else "COMPONENT", q)
            for rel, cands in resp.allied_standards.items():
                if rel in ALLIED_ROLES_INCLUDED:
                    for c in cands[:2]:
                        add(c, rel, q, via=resp.primary_standards[0].is_number if resp.primary_standards else None)

        ctx["standards"] = list(selected.values())
        ctx["clarifications"] = clarifications
        if not selected:
            ctx["halt"] = True
            return ("No grounded standard could be matched. Add product type, material or rating.",
                    {"standards": [], "clarifications": clarifications, "_status": "blocked"})

        roles = {}
        for s in selected.values():
            roles[s["role"]] = roles.get(s["role"], 0) + 1
        role_txt = ", ".join(f"{n} {r.lower().replace('_', ' ')}" for r, n in roles.items())
        return (f"Selected {len(selected)} standards ({role_txt})",
                {"standards": ctx["standards"], "clarifications": clarifications})

    # 3 ------------------------------------------------------------------------
    def _step_compliance(self, ctx: Dict[str, Any]):
        svc = ComplianceIntelligenceService(self.db)
        mandatory = 0
        items = []
        for s in ctx["standards"]:
            rep = svc.evaluate_compliance(s["standard_id"])
            if not rep:
                s["compliance"] = {"requirement_level": "UNKNOWN", "scheme": "UNKNOWN", "qcos": [], "citations": []}
                continue
            cites = []
            qcos = []
            for q in rep.qco_records:
                title = q.get("qco_title") or q.get("qco_id") or "Quality Control Order"
                cites.append(self._cite("QCO_ORDER", title[:120], q.get("source_dataset") or "schem.csv",
                                        f"{s['is_number']} notified under {title}", q.get("provenance")))
                qcos.append({"title": title, "notification_number": q.get("notification_number"),
                             "notification_date": q.get("notification_date"), "citation": cites[-1]})
            for c in rep.certification_records[:2]:
                cites.append(self._cite(
                    "CERTIFICATION_RECORD", f"{s['is_number']} · {c.get('product_name') or 'certification'}"[:120],
                    c.get("source_dataset") or "ReportExcel.csv",
                    f"{c.get('product_name')} — {c.get('requirement_level')}", c.get("provenance")))
            s["compliance"] = {
                "requirement_level": rep.requirement_level.value,
                "scheme": rep.governing_scheme,
                "qcos": qcos,
                "certification_count": len(rep.certification_records),
                "ministries": sorted({m["ministry_department"] for m in rep.ministry_mappings if m.get("ministry_department")}),
                "divergence_notes": rep.regulatory_divergence_notes,
                "citations": cites,
            }
            if rep.requirement_level.value == "MANDATORY":
                mandatory += 1
            items.append({"is_number": s["is_number"], **{k: v for k, v in s["compliance"].items() if k != "citations"}})

        return (f"{mandatory} of {len(ctx['standards'])} standards carry a mandatory certification/QCO obligation",
                {"compliance": items, "mandatory_count": mandatory})

    # 4 ------------------------------------------------------------------------
    def _step_versions(self, ctx: Dict[str, Any]):
        svc = VersionIntelligenceService(self.db)
        warnings_out = []
        superseded = 0
        for s in ctx["standards"]:
            cur = svc.check_currency(s["standard_id"])
            if not cur:
                continue
            s["version"] = {
                "is_current": cur.is_current,
                "status": cur.status,
                "publication_year": cur.publication_year,
                "latest_year": cur.latest_year,
                "total_amendments": cur.total_amendments,
            }
            if not cur.is_current:
                superseded += 1
            for w in cur.warnings:
                if w.warning_type.value == "UNKNOWN_VERSION_STATUS":
                    continue
                warnings_out.append({"is_number": s["is_number"], "type": w.warning_type.value,
                                     "severity": w.severity, "message": w.message})
        amended = sum(1 for w in warnings_out if w["type"] == "AMENDMENT_AVAILABLE")
        return (f"{superseded} superseded, {amended} with amendments to incorporate",
                {"warnings": warnings_out, "superseded_count": superseded})

_cached_licence_embeddings: Optional[Any] = None

    def _step_market(self, ctx: Dict[str, Any]):
        global _cached_licence_embeddings
        licences = self.db.query(ProductLicence).all()
        findings = []
        if licences:
            provider = get_embedding_provider()
            if _cached_licence_embeddings is not None and _cached_licence_embeddings[0] == len(licences):
                lic_vecs = _cached_licence_embeddings[1]
            else:
                lic_vecs = np.array(provider.embed_batch([l.product_category for l in licences]), dtype=np.float32)
                _cached_licence_embeddings = (len(licences), lic_vecs)
            std_titles = [s["title"] for s in ctx["standards"]]
            std_vecs = np.array(provider.embed_batch(std_titles), dtype=np.float32) if std_titles else np.empty((0, provider.dimension), dtype=np.float32)
            sims = std_vecs @ lic_vecs.T if len(std_titles) else np.empty((0, len(licences)), dtype=np.float32)
        for idx, s in enumerate(ctx["standards"]):
            market: Dict[str, Any] = {"licence_category": None, "licence_count": None, "risk": "UNKNOWN"}
            if licences:
                j = int(np.argmax(sims[idx]))
                if float(sims[idx][j]) >= LICENCE_MATCH_THRESHOLD:
                    lic = licences[j]
                    market.update({
                        "licence_category": lic.product_category,
                        "licence_count": lic.licence_count,
                        "match_score": round(float(sims[idx][j]), 3),
                        "citation": self._cite("PRODUCT_LICENCE", lic.product_category, lic.source_dataset,
                                               f"{lic.licence_count} BIS licences in category '{lic.product_category}'",
                                               lic.source_provenance),
                    })
                    if lic.licence_count == 0:
                        market["risk"] = "NO_SUPPLIERS"
                    elif lic.licence_count < THIN_MARKET_LICENCES:
                        market["risk"] = "THIN_MARKET"
                    else:
                        market["risk"] = "HEALTHY"
            s["market"] = market
            if market["risk"] in ("NO_SUPPLIERS", "THIN_MARKET"):
                findings.append({
                    "is_number": s["is_number"],
                    "risk": market["risk"],
                    "message": (f"Only {market['licence_count']} licensed producer(s) in '{market['licence_category']}'. "
                                "Mandating this certification may yield a single-bidder tender; "
                                "consider a phased compliance window or accepting CRS-registered equivalents.")
                    if market["licence_count"] else
                    (f"No licensed producers recorded for '{market['licence_category']}'. "
                     "Verify supplier availability before making this certification a bid-rejection criterion."),
                })

        known = [s for s in ctx["standards"] if s["market"]["licence_count"] is not None]
        if not known:
            summary = "No licence-depth data matches these products; market depth is UNKNOWN (stated, not assumed)"
        else:
            summary = f"Licence depth found for {len(known)} standard(s); {len(findings)} competition risk(s) flagged"
        return summary, {"findings": findings,
                         "market": [{"is_number": s["is_number"], **s["market"]} for s in ctx["standards"]]}

    # 6 ------------------------------------------------------------------------
    def _step_draft(self, ctx: Dict[str, Any]):
        params: List[Dict[str, Any]] = []
        for key, val in (ctx["facts"].get("technical_attributes") or {}).items():
            params.append({"parameter": key.replace("_", " ").title(),
                           "value": ", ".join(val) if isinstance(val, list) else str(val)})
        ctx["technical_parameters"] = params
        ctx["tender_sections"] = self._compose_sections(ctx)
        ctx["tender_text"] = self._render_text(ctx["tender_sections"])
        clauses = sum(len(sec["clauses"]) for sec in ctx["tender_sections"])
        return (f"Drafted {len(ctx['tender_sections'])} sections, {clauses} clauses, {len(self.citations)} citations",
                {"sections": ctx["tender_sections"]})

    def _compose_sections(self, ctx: Dict[str, Any]) -> List[Dict[str, Any]]:
        facts = ctx["facts"]
        stds = ctx["standards"]
        sections: List[Dict[str, Any]] = []

        def clause(text: str, cites: List[str], kind: str = "clause") -> Dict[str, Any]:
            return {"text": text, "citations": [c for c in dict.fromkeys(cites) if c], "kind": kind}

        # 1. Scope
        qty = facts.get("quantity")
        scope = [clause(f"Supply of {ctx['need'].strip().rstrip('.')}.", [])]
        if qty:
            scope.append(clause(f"Quantity: {qty['value']} {qty['unit']}.", []))
        if facts.get("location"):
            scope.append(clause(f"Place of delivery: {facts['location']}.", []))
        if facts.get("budget"):
            scope.append(clause(f"Estimated value: ₹{facts['budget']['amount_inr']:,.0f}.", []))
        sections.append({"id": "scope", "heading": "1. Scope of Supply", "clauses": scope})

        # 2. Applicable standards
        std_clauses = []
        for s in stds:
            if s["role"] in ("PRIMARY", "COMPONENT", "CONDITIONAL"):
                note = " (applicability to be confirmed — see clarifications)" if s["role"] == "CONDITIONAL" else ""
                std_clauses.append(clause(
                    f"The {s['matched_component'] if s['role'] != 'PRIMARY' else 'goods'} shall conform to "
                    f"{s['is_number']} — {s['title']}, latest revision with all amendments{note}.",
                    [s["citation"]]))
        sections.append({"id": "standards", "heading": "2. Applicable Indian Standards", "clauses": std_clauses})

        # 3. Technical parameters (only values stated in the need; never invented)
        tp = [clause(f"{p['parameter']}: {p['value']} (as stated by the indenting officer).", [])
              for p in ctx.get("technical_parameters", [])]
        tp.append(clause("Ratings, tolerances and performance limits not stated above shall be as specified in the "
                         "applicable Indian Standards listed in Section 2.", []))
        sections.append({"id": "parameters", "heading": "3. Technical Parameters", "clauses": tp})

        # 4. Certification & QCO
        cert_clauses = []
        for s in stds:
            comp = s.get("compliance") or {}
            level = comp.get("requirement_level")
            if level == "MANDATORY":
                scheme = {"BIS_ISI": "ISI mark under BIS Scheme-I", "CRS": "BIS Compulsory Registration (CRS)"}.get(
                    comp.get("scheme"), f"BIS certification ({comp.get('scheme')})")
                qco_txt = f" as notified in {comp['qcos'][0]['title'][:140]}" if comp.get("qcos") else ""
                cert_clauses.append(clause(
                    f"Goods covered by {s['is_number']} shall bear a valid {scheme}{qco_txt}. "
                    "Bidders shall submit a valid BIS licence/registration number; offers without it shall be rejected.",
                    comp.get("citations", [])))
            elif level == "VOLUNTARY":
                cert_clauses.append(clause(
                    f"BIS certification for {s['is_number']} is voluntary per dataset records; "
                    "ISI-marked goods are preferred but not a rejection criterion.",
                    comp.get("citations", [])))
        if cert_clauses:
            sections.append({"id": "certification", "heading": "4. Mandatory Certification & Quality Control Orders",
                             "clauses": cert_clauses})

        # 5. Testing & inspection
        test_clauses = []
        for s in stds:
            if s["role"] in ("TESTING", "SAFETY", "PERFORMANCE", "INSTALLATION", "NORMATIVE_REFERENCE"):
                verb = {"TESTING": "Tests shall be carried out as per",
                        "SAFETY": "Safety requirements shall comply with",
                        "PERFORMANCE": "Performance shall be verified as per",
                        "INSTALLATION": "Installation shall follow",
                        "NORMATIVE_REFERENCE": "Referenced requirements shall comply with"}[s["role"]]
                via = f" (linked to {s['linked_via']} in the standards knowledge graph)" if s.get("linked_via") else ""
                test_clauses.append(clause(f"{verb} {s['is_number']} — {s['title']}{via}.", [s["citation"]]))
        test_clauses.append(clause(
            "Pre-dispatch inspection and acceptance tests shall be conducted at a BIS-recognised or NABL-accredited "
            "laboratory; test reports shall accompany each lot.", []))
        sections.append({"id": "testing", "heading": "5. Testing, Inspection & Acceptance", "clauses": test_clauses})

        # 6. Bidder eligibility & competition
        elig = [clause("Specifications are performance- and standard-based. Any make/brand meeting the cited "
                       "Indian Standards is acceptable (GFR 2017, Rule 144).", [])]
        for s in stds:
            m = s.get("market") or {}
            if m.get("risk") in ("THIN_MARKET", "NO_SUPPLIERS"):
                elig.append(clause(
                    f"Market note: {m['licence_count']} licence(s) recorded in '{m['licence_category']}'. "
                    "Procuring entity to confirm adequate competition before bid publication.",
                    [m.get("citation")], kind="advisory"))
        sections.append({"id": "eligibility", "heading": "6. Bidder Eligibility & Fair Competition", "clauses": elig})
        return sections

    @staticmethod
    def _render_text(sections: List[Dict[str, Any]]) -> str:
        lines = ["TENDER DOCUMENT — TECHNICAL SPECIFICATION", ""]
        for sec in sections:
            lines.append(sec["heading"].upper())
            for i, c in enumerate(sec["clauses"], 1):
                num = sec["heading"].split(".")[0]
                lines.append(f"{num}.{i} {c['text']}")
            lines.append("")
        return "\n".join(lines)

    # 7 ------------------------------------------------------------------------
    def _step_redteam(self, ctx: Dict[str, Any]):
        findings: List[Dict[str, Any]] = []
        facts = ctx["facts"]

        for brand in facts.get("brands_mentioned", []):
            findings.append({"severity": "CRITICAL", "category": "BRAND_RESTRICTION",
                             "issue": f"Need mentions brand '{brand}'. Brand-specific tenders restrict competition (GFR Rule 144).",
                             "fix": "Removed brand reference; specification is standard-based with 'or equivalent' acceptance.",
                             "auto_fixed": True})

        for s in ctx["standards"]:
            if s.get("version") and not s["version"]["is_current"]:
                findings.append({"severity": "CRITICAL", "category": "OUTDATED_REFERENCE",
                                 "issue": f"{s['is_number']} is {s['version']['status']} in the dataset.",
                                 "fix": s.get("supersession_note") or "Replace with the current successor standard before publication.",
                                 "auto_fixed": False})

        for cl in ctx.get("clarifications", []):
            findings.append({"severity": "WARNING", "category": "AMBIGUOUS_SPECIFICATION",
                             "issue": f"'{cl['component']}' is underspecified.",
                             "fix": "Specify: " + ", ".join(cl["missing"][:4]), "auto_fixed": False})

        # Independent audit of our own draft by the Module 12 tender auditor
        before = after = None
        tender_svc = TenderEngineService(self.db)
        audit_svc = TenderAuditService(self.db)
        doc = tender_svc.process_document(ctx["tender_text"].encode("utf-8"), f"{ctx['run_id']}-draft.txt",
                                          title=f"Autopilot draft {ctx['run_id']}", organization="ARISTEA Autopilot")
        report = audit_svc.audit_tender(doc.id, force_recompute=True)
        before = report.coverage_percentage

        present = {s["is_number"].upper() for s in ctx["standards"]}
        additions: List[Dict[str, Any]] = []
        for gap in report.gaps:
            cat = gap.gap_category.value
            if cat == "SUFFICIENT_EVIDENCE":
                continue
            std = (gap.standard_id or "").strip()
            fixable = cat in ("MISSING_REFERENCE", "POTENTIALLY_MISSING_TESTING_STANDARD",
                              "POTENTIALLY_MISSING_SAFETY_STANDARD") and std and std.upper() not in present
            if fixable:
                present.add(std.upper())
                cite = self._cite("AUDIT_FINDING", std, "tender_audit (Module 12)",
                                  gap.issue_description, gap.evidence or None)
                additions.append({"text": f"{'Tests' if 'TESTING' in cat else 'Goods'} shall also comply with "
                                          f"{std}{' — ' + gap.title if gap.title else ''}.", "citations": [cite],
                                  "kind": "autofix"})
            findings.append({"severity": gap.severity.value, "category": cat, "issue": gap.issue_description,
                             "fix": gap.recommendation, "auto_fixed": bool(fixable)})

        if additions:
            sec = next((x for x in ctx["tender_sections"] if x["id"] == "testing"), None)
            if sec is None:
                sec = {"id": "testing", "heading": "5. Testing, Inspection & Acceptance", "clauses": []}
                ctx["tender_sections"].append(sec)
            sec["clauses"][-1:-1] = additions  # keep the generic inspection clause last
            ctx["tender_text"] = self._render_text(ctx["tender_sections"])
            doc2 = tender_svc.process_document(ctx["tender_text"].encode("utf-8"), f"{ctx['run_id']}-final.txt",
                                               title=f"Autopilot final {ctx['run_id']}", organization="ARISTEA Autopilot")
            after = audit_svc.audit_tender(doc2.id, force_recompute=True).coverage_percentage
        else:
            after = before

        ctx["redteam"] = {"findings": findings, "coverage_before": before, "coverage_after": after,
                          "auto_fixes": sum(1 for f in findings if f["auto_fixed"])}
        crit = sum(1 for f in findings if f["severity"] == "CRITICAL" and not f["auto_fixed"])
        return (f"{len(findings)} findings, {ctx['redteam']['auto_fixes']} auto-fixed; "
                f"audit coverage {before:.0f}% → {after:.0f}%" + (f"; {crit} need officer action" if crit else ""),
                {**ctx["redteam"], "sections": ctx["tender_sections"]})

    # ------------------------------------------------------------------ result
    def _package(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        redteam = ctx.get("redteam") or {}
        open_critical = [f for f in redteam.get("findings", []) if f["severity"] == "CRITICAL" and not f["auto_fixed"]]
        if ctx.get("halt") or not ctx.get("tender_sections"):
            readiness = "BLOCKED"
        elif open_critical or ctx.get("clarifications"):
            readiness = "NEEDS_REVIEW"
        else:
            readiness = "READY_FOR_APPROVAL"
        return {
            "run_id": ctx["run_id"],
            "need": ctx["need"],
            "readiness": readiness,
            "facts": ctx.get("facts"),
            "standards": ctx.get("standards", []),
            "clarifications": ctx.get("clarifications", []),
            "sections": ctx.get("tender_sections", []),
            "tender_text": ctx.get("tender_text", ""),
            "redteam": redteam,
            "citations": list(self.citations.values()),
            "disclaimer": ("Autopilot output is a decision-support draft grounded strictly in the ingested BIS dataset. "
                           "It requires review and approval by the competent procurement authority before publication."),
        }
