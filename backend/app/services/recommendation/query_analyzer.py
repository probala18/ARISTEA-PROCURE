"""
Query & Intent Analyzer for Module 6 — Recommendation Engine.
Analyzes query intent, language, ambiguity, out-of-scope boundaries, and extracted attributes.
"""
import re
from typing import List, Dict, Any, Tuple, Optional
from backend.app.services.recommendation.schemas import IntentType, ClarificationPrompt
from backend.app.core.normalizers import parse_standard_id


class QueryAnalyzer:
    """Parses natural language procurement queries into structured intent and constraints."""

    OUT_OF_SCOPE_KEYWORDS = {
        "weather", "temperature", "forecast", "climate", "cricket", "football",
        "movie", "cinema", "song", "recipe", "cooking", "restaurant", "flight",
        "train status", "stock price", "cryptocurrency", "bitcoin", "horoscope",
        "joke", "president", "prime minister", "election",
    }

    AMBIGUOUS_PATTERNS = {
        "cables": {
            "patterns": [r"\bcables?\b"],
            "missing_discriminators": [
                "Operating voltage rating (e.g., up to 1100 V vs high voltage / 11 kV)",
                "Insulation material (e.g., PVC vs XLPE vs elastomeric/rubber)",
                "Conductor type (e.g., copper vs aluminium)",
                "Application environment (e.g., domestic fixed wiring, flexible cord, underground armored)",
            ],
            "suggestions": [
                {"standard": "IS 694", "type": "PVC Insulated Cables up to 1100 V (domestic/flexible)"},
                {"standard": "IS 1554", "type": "PVC Insulated Heavy Duty Electrical Cables"},
                {"standard": "IS 7098", "type": "Cross-linked Polyethylene (XLPE) Insulated Cables"},
            ],
        },
        "testing_unspecified": {
            "patterns": [r"^(what|which)\s+testing\s+is\s+required\??$", r"^testing\s+required\??$"],
            "missing_discriminators": [
                "Target product or equipment (e.g., induction motor, electrical cable, cement)",
                "Applicable Indian Standard number (e.g., IS 12615, IS 694)",
                "Test category (e.g., type testing, routine acceptance testing, safety testing)",
            ],
            "suggestions": [
                {"context": "Motors", "standard": "IS 12615 / IS 12802"},
                {"context": "Cables", "standard": "IS 694 / IS 10810"},
                {"context": "Cement", "standard": "IS 269 / IS 4031"},
            ],
        },
        "pipes": {
            "patterns": [r"\bpipes?\b"],
            "missing_discriminators": [
                "Pipe material (e.g., UPVC, HDPE, Galvanized Iron, Ductile Iron)",
                "Intended fluid and application (e.g., potable drinking water, agricultural, sewage/drainage)",
                "Pressure class / nominal diameter",
            ],
            "suggestions": [
                {"standard": "IS 4985", "type": "Unplasticized PVC pipes for potable water"},
                {"standard": "IS 4984", "type": "HDPE pipes for water supply"},
            ],
        },
        "cement": {
            "patterns": [r"^\s*cement\s+(standard|requirement)?\s*\??$"],
            "missing_discriminators": [
                "Cement grade/type (e.g., Ordinary Portland 43/53, Portland Slag, Portland Pozzolana)",
                "Structural application (e.g., general concrete, marine, pre-stressed)",
            ],
            "suggestions": [
                {"standard": "IS 269", "type": "Ordinary Portland Cement"},
                {"standard": "IS 455", "type": "Portland Slag Cement"},
                {"standard": "IS 1489", "type": "Portland Pozzolana Cement"},
            ],
        },
    }

    def detect_language(self, text: str) -> str:
        """Detects language based on script/unicode ranges."""
        if re.search(r"[\u0900-\u097F]", text):
            return "hi"
        if re.search(r"[\u0B80-\u0BFF]", text):
            return "ta"
        if re.search(r"[\u0C00-\u0C7F]", text):
            return "te"
        return "en"

    def extract_standard_numbers(self, text: str) -> List[str]:
        """Extracts cited IS numbers from natural language."""
        pattern = r"\b(?:IS|is)(?:/IEC)?\s*\d+(?:\s*(?:Part|part|Pt)\s*\d+)?(?::\d{4})?\b"
        matches = re.findall(pattern, text)
        cleaned = []
        for m in matches:
            parsed = parse_standard_id(m)
            if parsed and parsed.get("standard_id"):
                cleaned.append(parsed["standard_id"])
            elif parsed and parsed.get("is_number"):
                cleaned.append(parsed["is_number"])
            else:
                cleaned.append(m)
        return list(dict.fromkeys(cleaned))

    def check_out_of_scope(self, text: str) -> Tuple[bool, str]:
        """Checks if the query is unrelated to standards, procurement, or testing."""
        lower = text.lower()
        for kw in self.OUT_OF_SCOPE_KEYWORDS:
            if re.search(r"\b" + re.escape(kw) + r"\b", lower):
                # Ensure no BIS / standard keywords override it
                # Note: Do NOT match standalone English word 'is' (e.g., 'What is the weather')
                if not re.search(r"\b(?:is\s*\d+|bis|standards?|specifications?|certifications?|isi\s*mark|qco|tender)\b", lower):
                    return True, f"Query relates to non-engineering/non-standards topic: '{kw}'."
        return False, ""

    HINDI_TERM_MAP = {
        "केबल": "cables",
        "तार": "wires",
        "सर्टिफिकेशन": "certification",
        "प्रमाणीकरण": "certification",
        "मानक": "standard",
        "मोटर": "motor",
        "सीमेंट": "cement",
        "परीक्षण": "testing",
        "प्रयोगशाला": "laboratory",
        "जरूरी": "mandatory",
        "अनिवार्य": "mandatory",
    }

    def normalize_multilingual_query(self, text: str) -> str:
        """Translates common Indic procurement terms into English for cross-lingual retrieval."""
        norm = text
        for indic_word, en_word in self.HINDI_TERM_MAP.items():
            norm = norm.replace(indic_word, en_word)
        return norm

    def check_ambiguity(
        self, text: str, extracted_stds: List[str]
    ) -> Tuple[bool, List[str], List[Dict[str, Any]]]:
        """
        Determines if a query is genuinely underspecified and requires technical discriminators.
        """
        # If an exact standard is given, it's not ambiguous
        if extracted_stds:
            return False, [], []

        lower = text.lower()

        # Check explicit ambiguous patterns
        for key, conf in self.AMBIGUOUS_PATTERNS.items():
            for pat in conf["patterns"]:
                if re.search(pat, lower):
                    # Check if technical discriminators are already supplied
                    has_voltage = bool(re.search(r"\b(\d+\s*(?:v|kv|volt)|high voltage|low voltage|1100\s*v)\b", lower))
                    has_material = bool(re.search(r"\b(pvc|xlpe|copper|aluminium|hdpe|upvc|slag|pozzolana)\b", lower))
                    has_application = bool(re.search(r"\b(domestic|industrial|armoured|drinking|potable|fire|sewage)\b", lower))
                    is_specific_inquiry = bool(re.search(r"\b(laborator|where to test|where can i test|certification|mandatory|licen[cs]e)\b", lower))

                    if key == "cables" and (has_voltage or has_material or has_application or is_specific_inquiry):
                        continue
                    if key == "pipes" and (has_material or has_application):
                        continue
                    if key == "cement" and has_material:
                        continue

                    return True, conf["missing_discriminators"], conf["suggestions"]

        # Check ultra-short underspecified queries (< 3 words)
        words = lower.split()
        if len(words) <= 2 and words[0] in {"standard", "testing", "cable", "motor", "cement", "pipe"}:
            return True, [
                "Product category or equipment type",
                "Technical ratings, materials, or capacity",
                "Operating context or application",
            ], []

        return False, [], []

    def classify_intent(
        self,
        text: str,
        extracted_stds: List[str],
        is_ambiguous: bool,
        is_oos: bool,
    ) -> IntentType:
        """Classifies the query into structured intent types."""
        if is_oos:
            return IntentType.OUT_OF_SCOPE

        lower = text.lower()

        # Check for technical comparison
        if re.search(r"\b(difference between|compare|versus|vs\.?)\b", lower) and len(extracted_stds) >= 2:
            return IntentType.TECHNICAL_QUESTION

        # Check for direct standard lookup
        if extracted_stds and re.search(r"^(what is|tell me about|details of|scope of)?\s*(is|is/iec)\b", lower):
            return IntentType.STANDARD_LOOKUP

        # Check for certification / legal QCO questions
        if re.search(r"\b(mandatory|certification|scheme-?i|isi mark|qco|licence|license|सर्टिफिकेशन|अनिवार्य)\b", lower):
            return IntentType.CERTIFICATION_REQUIREMENT

        # Check for laboratory / testing questions
        if re.search(r"\b(laborator|lab\b|where to test|where can i test|testing facility)\b", lower):
            return IntentType.TESTING_REQUIREMENT

        if re.search(r"\b(testing|test method|test procedure|tested under)\b", lower):
            return IntentType.TESTING_REQUIREMENT

        # Check for BIS services overview
        if re.search(r"\b(services offered by bis|services of bis|what does bis do|what is bis)\b", lower):
            return IntentType.GENERAL_BIS_QUERY

        # Ambiguous query flag
        if is_ambiguous:
            return IntentType.AMBIGUOUS_QUERY

        # Default procurement recommendation
        return IntentType.PRODUCT_STANDARD_RECOMMENDATION

    def extract_attributes(self, text: str) -> Dict[str, Any]:
        """Extracts technical attributes from natural language query."""
        attrs: Dict[str, Any] = {}
        lower = text.lower()

        # Voltage
        volt_match = re.search(r"(\d+)\s*(kv|v|volts|volt)", lower)
        if volt_match:
            attrs["voltage"] = f"{volt_match.group(1)} {volt_match.group(2).upper()}"

        # Frequency / Power
        power_match = re.search(r"(\d+(?:\.\d+)?)\s*(kw|hp|mw|kva)", lower)
        if power_match:
            attrs["power_rating"] = f"{power_match.group(1)} {power_match.group(2).upper()}"

        # Materials
        materials = []
        for mat in ["pvc", "xlpe", "copper", "aluminium", "aluminum", "steel", "hdpe", "upvc", "cast iron"]:
            if re.search(r"\b" + mat + r"\b", lower):
                materials.append(mat.upper())
        if materials:
            attrs["materials"] = materials

        # Application
        applications = []
        for app in ["domestic", "industrial", "agricultural", "fire safety", "flexible", "submersible", "heavy duty"]:
            if re.search(r"\b" + app + r"\b", lower):
                applications.append(app.capitalize())
        if applications:
            attrs["application"] = applications

        return attrs

    def analyze(self, text: str) -> Dict[str, Any]:
        """Full end-to-end query analysis."""
        lang = self.detect_language(text)
        extracted_stds = self.extract_standard_numbers(text)
        is_oos, oos_reason = self.check_out_of_scope(text)
        is_ambig, discriminators, suggestions = self.check_ambiguity(text, extracted_stds)
        intent = self.classify_intent(text, extracted_stds, is_ambig, is_oos)
        attributes = self.extract_attributes(text)

        clarification_prompt = None
        if is_ambig:
            clarification_prompt = ClarificationPrompt(
                is_ambiguous=True,
                query=text,
                explanation="The query specifies a broad product family without technical parameters required to identify a single definitive standard.",
                missing_discriminators=discriminators,
                suggested_options=suggestions,
            )

        return {
            "language": lang,
            "extracted_standards": extracted_stds,
            "is_out_of_scope": is_oos,
            "out_of_scope_reason": oos_reason,
            "is_ambiguous": is_ambig,
            "clarification_prompt": clarification_prompt,
            "intent": intent,
            "attributes": attributes,
        }
