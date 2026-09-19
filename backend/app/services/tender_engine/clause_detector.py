"""
Clause and Section Detection for Tender Documents (Module 11).
Segments parsed pages into structured sections and individual technical clauses.
Extracts:
- Section titles, numbers, and classified types (TECHNICAL_SPEC, ELIGIBILITY, BOQ, etc.)
- Clause numbers, source text, mandatory status, and technical attributes
"""
import re
from typing import List, Dict, Any, Optional, Tuple

from backend.app.services.tender_engine.schemas import (
    SectionType,
    ExtractedSection,
    ExtractedClause,
)
from backend.app.services.tender_engine.parsers import ParsedPage


class ClauseDetector:
    """Detects and classifies document sections and numbered/bulleted clauses."""

    SECTION_PATTERNS = [
        # SECTION 1 / Section I / Section 3.0: Title
        re.compile(r"^(?:SECTION|PART|CHAPTER)\s+([0-9IVXLCDM\.]+)\s*[:\-\.]?\s*(.*)$", re.IGNORECASE),
        # 1.0 TECHNICAL SPECIFICATIONS / 2. SCOPE OF WORK
        re.compile(r"^([0-9]{1,2}\.0?)\s+([A-Z\s]{4,60})$"),
        # Markdown headings: # Section Title
        re.compile(r"^#{1,3}\s+(.*)$"),
    ]

    CLAUSE_PATTERNS = [
        # Clause 3.1.2: Text or Clause 4: Text
        re.compile(r"^(?:Clause|Item|Para|Requirement)\s+([0-9]+(?:\.[0-9]+)*)\s*[:\-\.]?\s*(.*)$", re.IGNORECASE),
        # 1.1 Text or 3.2.1 Text
        re.compile(r"^([0-9]+(?:\.[0-9]+)+)\s*[:\-\.]?\s+(.*)$"),
        # Numbered list: 1. Text, 2. Text
        re.compile(r"^([0-9]+)\.\s+(.*)$"),
        # Bullet / alphabetic list: a) Text, (i) Text
        re.compile(r"^(\([a-z0-9ivx]+\)|[a-z]\))\s+(.*)$", re.IGNORECASE),
    ]

    MANDATORY_KEYWORDS = [
        "shall", "must", "mandatory", "required", "compulsory", "shall comply", 
        "strictly required", "essential", "shall be certified", "must adhere"
    ]

    SECTION_TYPE_MAPPINGS = {
        SectionType.TECHNICAL_SPEC: [
            "technical spec", "specifications", "technical requirement", "product requirement",
            "material requirement", "equipment specification", "standards applicable", "applicable standards"
        ],
        SectionType.TESTING_AND_COMPLIANCE: [
            "testing", "inspection", "quality assurance", "compliance", "certification", 
            "test certificate", "factory acceptance", "routine test", "type test"
        ],
        SectionType.SCOPE_OF_WORK: [
            "scope of work", "scope of supply", "work description", "general scope"
        ],
        SectionType.ELIGIBILITY: [
            "eligibility", "qualification", "bidder eligibility", "pre-qualification", "experience"
        ],
        SectionType.BOQ: [
            "bill of quantities", "boq", "schedule of items", "price schedule", "quantity"
        ],
        SectionType.GENERAL_TERMS: [
            "general terms", "general conditions", "instruction to bidders", "commercial terms",
            "contract conditions", "legal terms"
        ],
    }

    def classify_section_type(self, title: str, content_snippet: str = "") -> SectionType:
        """Determines SectionType based on title and snippet keywords."""
        combined = f"{title.lower()} {content_snippet.lower()[:300]}"
        for s_type, keywords in self.SECTION_TYPE_MAPPINGS.items():
            if any(k in combined for k in keywords):
                return s_type
        return SectionType.OTHER

    def is_section_header(self, line: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Checks if a line is a section header. Returns (is_header, section_num, section_title)."""
        stripped = line.strip()
        if not stripped or len(stripped) > 120:
            return False, None, None

        for pat in self.SECTION_PATTERNS:
            m = pat.match(stripped)
            if m:
                groups = m.groups()
                if len(groups) == 2:
                    return True, groups[0].strip(), groups[1].strip()
                elif len(groups) == 1:
                    return True, None, groups[0].strip()

        # Check for ALL CAPS common headings
        upper_stripped = stripped.upper()
        for s_type, keywords in self.SECTION_TYPE_MAPPINGS.items():
            for kw in keywords:
                if upper_stripped == kw.upper():
                    return True, None, stripped

        return False, None, None

    def is_clause_start(self, line: str) -> Tuple[bool, Optional[str], str]:
        """Checks if a line starts a new clause. Returns (is_clause, clause_num, remainder_text)."""
        stripped = line.strip()
        for pat in self.CLAUSE_PATTERNS:
            m = pat.match(stripped)
            if m:
                groups = m.groups()
                clause_num = groups[0]
                remainder = groups[1] if len(groups) > 1 else ""
                return True, clause_num, remainder
        return False, None, stripped

    def extract_technical_attributes(self, text: str) -> Dict[str, Any]:
        """Extracts key engineering parameters and specifications from clause text."""
        attrs = {}
        # Voltage: e.g. 1.1 kV, 415 V, 11kV
        volt_m = re.search(r"(\b[0-9]+(?:\.[0-9]+)?\s*(?:kV|kVA|V|volts?)\b)", text, re.IGNORECASE)
        if volt_m:
            attrs["voltage_rating"] = volt_m.group(1)

        # Power/Rating: e.g. 55 kW, 75 HP, 10 MVA
        power_m = re.search(r"(\b[0-9]+(?:\.[0-9]+)?\s*(?:kW|HP|MW|kVA|MVA)\b)", text, re.IGNORECASE)
        if power_m:
            attrs["power_rating"] = power_m.group(1)

        # Temperature: e.g. 70 deg C, 90°C
        temp_m = re.search(r"(\b[0-9]+\s*(?:deg\s*C|°C|celsius)\b)", text, re.IGNORECASE)
        if temp_m:
            attrs["temperature_rating"] = temp_m.group(1)

        # Dimensions / Size: e.g. 4 sq mm, 2.5 mm2, 50mm
        size_m = re.search(r"(\b[0-9]+(?:\.[0-9]+)?\s*(?:sq\.?\s*mm|mm2|mm)\b)", text, re.IGNORECASE)
        if size_m:
            attrs["size_dimension"] = size_m.group(1)

        return attrs

    def extract_product_keywords(self, text: str) -> List[str]:
        """Extracts common procurement product keywords."""
        known_products = [
            "cable", "cables", "conductor", "motor", "motors", "transformer", "switchgear",
            "pump", "pumps", "cement", "steel", "pvc", "xlpe", "aluminium", "copper",
            "pipe", "pipes", "valve", "valves", "insulator", "battery", "solar", "led",
            "luminaire", "wire", "wires", "bearing", "generator", "turbine"
        ]
        text_lower = text.lower()
        found = [p for p in known_products if re.search(rf"\b{p}\b", text_lower)]
        return found

    def segment_sections_and_clauses(self, pages: List[ParsedPage]) -> List[ExtractedSection]:
        """
        Segments parsed document pages into structured sections containing clauses.
        Preserves exact page numbers, section headers, and clause boundaries.
        """
        sections: List[ExtractedSection] = []
        
        current_sec_num: Optional[str] = None
        current_sec_title: Optional[str] = None
        current_sec_page: int = pages[0].page_number if pages else 1
        current_sec_lines: List[str] = []
        current_clauses: List[ExtractedClause] = []

        active_clause_num: Optional[str] = None
        active_clause_page: int = current_sec_page
        active_clause_lines: List[str] = []

        def flush_active_clause():
            nonlocal active_clause_num, active_clause_page, active_clause_lines
            if active_clause_lines:
                c_text = " ".join(active_clause_lines).strip()
                if c_text:
                    is_mand = any(kw in c_text.lower() for kw in self.MANDATORY_KEYWORDS)
                    attrs = self.extract_technical_attributes(c_text)
                    kw = self.extract_product_keywords(c_text)
                    current_clauses.append(ExtractedClause(
                        clause_number=active_clause_num,
                        page_number=active_clause_page,
                        text=c_text,
                        extracted_intent="TECHNICAL_REQUIREMENT" if attrs or kw else "GENERAL_CLAUSE",
                        product_keywords=kw,
                        technical_attributes=attrs,
                        is_mandatory=is_mand,
                    ))
            active_clause_num = None
            active_clause_lines = []

        def flush_current_section():
            nonlocal current_sec_num, current_sec_title, current_sec_page, current_sec_lines, current_clauses
            flush_active_clause()
            sec_content = "\n".join(current_sec_lines).strip()
            # Only create section if title was set or clauses/content exist
            if current_sec_title is not None and (sec_content or current_clauses):
                stype = self.classify_section_type(current_sec_title, sec_content)
                sections.append(ExtractedSection(
                    section_number=current_sec_num or str(len(sections) + 1),
                    section_title=current_sec_title,
                    page_number=current_sec_page,
                    section_type=stype,
                    content=sec_content or (current_clauses[0].text if current_clauses else ""),
                    clauses=list(current_clauses),
                ))
            elif current_sec_title is None and current_clauses:
                # Clauses appeared before any section header
                sections.append(ExtractedSection(
                    section_number="1",
                    section_title="General Specifications",
                    page_number=current_sec_page,
                    section_type=SectionType.TECHNICAL_SPEC,
                    content=sec_content or current_clauses[0].text,
                    clauses=list(current_clauses),
                ))
            current_sec_lines = []
            current_clauses = []

        for page in pages:
            lines = page.text.splitlines()
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    continue

                is_sec, s_num, s_title = self.is_section_header(stripped)
                if is_sec:
                    flush_current_section()
                    current_sec_num = s_num or str(len(sections) + 1)
                    current_sec_title = s_title or "Section"
                    current_sec_page = page.page_number
                    current_sec_lines.append(stripped)
                    continue

                is_clause, c_num, remainder = self.is_clause_start(stripped)
                if is_clause:
                    flush_active_clause()
                    active_clause_num = c_num
                    active_clause_page = page.page_number
                    active_clause_lines.append(remainder if remainder else stripped)
                    current_sec_lines.append(stripped)
                else:
                    if active_clause_lines:
                        active_clause_lines.append(stripped)
                    current_sec_lines.append(stripped)

        # Flush final open clause and section
        flush_current_section()

        # If document had no detected sections, wrap into a single default section
        if not sections:
            all_text = "\n\n".join([p.text for p in pages if p.text.strip()])
            sections.append(ExtractedSection(
                section_number="1",
                section_title="General Tender Specifications",
                page_number=1,
                section_type=SectionType.TECHNICAL_SPEC,
                content=all_text,
                clauses=[],
            ))

        return sections
