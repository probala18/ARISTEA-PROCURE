"""
Procurement need parser for ARISTEA Autopilot.
Extracts deterministic procurement facts (quantity, budget, location, components,
brand-restrictive wording) from a free-text need. Never invents values: anything
not present in the text is left as None.
"""
import re
from typing import Any, Dict, List, Optional

INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat",
    "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh",
    "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh",
    "Uttarakhand", "West Bengal", "Delhi", "Jammu and Kashmir", "Ladakh", "Puducherry",
    "Chandigarh", "Andaman and Nicobar", "Lakshadweep",
]

# Brand names that commonly leak into Indian tenders and restrict competition (GFR 2017 Rule 144).
KNOWN_BRANDS = [
    "philips", "havells", "bajaj", "crompton", "syska", "wipro", "polycab", "finolex", "kei",
    "anchor", "legrand", "schneider", "siemens", "abb", "tata", "jsw", "ultratech", "acc",
    "ambuja", "exide", "amaron", "luminous", "microtek", "hp", "dell", "lenovo", "samsung",
    "lg", "sony", "godrej", "voltas", "daikin", "kirloskar", "jindal", "astral", "supreme",
]

UNIT_PATTERN = (
    r"nos?\.?|numbers?|units?|pieces?|pcs|sets?|km|kilomet(?:er|re)s?|metres?|meters?|m|"
    r"tonnes?|tons?|mt|bags?|litres?|liters?|kg|kilograms?|kits?|rolls?|coils?"
)

_SPLIT_PATTERN = re.compile(r"\bwith\b|\band\b|\bplus\b|\balong with\b|[,;+&]", re.IGNORECASE)
_NOISE_PATTERN = re.compile(
    r"\b(?:we|need|needs|require|required|requirement|procure|procurement|purchase|buy|supply|of|"
    r"for|the|a|an|to|in|at|on|our|some|approx|approximately|about|project|scheme|"
    r"village|district|city|rural|urban|road|roads|budget|total|cost|worth)\b",
    re.IGNORECASE,
)


def _parse_budget(text: str) -> Optional[Dict[str, Any]]:
    m = re.search(
        r"(?:₹|rs\.?|inr|budget(?:\s+of)?|worth|cost(?:\s+of)?)\s*([\d,]+(?:\.\d+)?)\s*(lakhs?|lacs?|crores?|cr|l|k|thousand)?",
        text,
        re.IGNORECASE,
    )
    if not m:
        return None
    try:
        value = float(m.group(1).replace(",", ""))
    except ValueError:
        return None
    unit = (m.group(2) or "").lower()
    multiplier = 1.0
    if unit.startswith(("lakh", "lac")) or unit == "l":
        multiplier = 1e5
    elif unit.startswith("cr"):
        multiplier = 1e7
    elif unit in ("k", "thousand"):
        multiplier = 1e3
    return {"raw": m.group(0).strip(), "amount_inr": value * multiplier}


def _parse_quantity(text: str) -> Optional[Dict[str, Any]]:
    stripped = re.sub(r"(?:₹|rs\.?|inr)\s*[\d,]+(?:\.\d+)?\s*\w*", " ", text, flags=re.IGNORECASE)
    stripped = re.sub(r"\b\d+\s*(?:kv|v|volts?|w|kw|kva|hp|mm|grade)\b", " ", stripped, flags=re.IGNORECASE)
    m = re.search(rf"\b(\d[\d,]*)\s*({UNIT_PATTERN})?\b", stripped, re.IGNORECASE)
    if not m:
        return None
    try:
        value = int(m.group(1).replace(",", ""))
    except ValueError:
        return None
    return {"value": value, "unit": (m.group(2) or "nos").lower()}


def _parse_location(text: str) -> Optional[str]:
    lower = text.lower()
    for state in INDIAN_STATES:
        if state.lower() in lower:
            return state
    return None


def _detect_brands(text: str) -> List[str]:
    lower = text.lower()
    return [b for b in KNOWN_BRANDS if re.search(rf"\b{re.escape(b)}\b", lower)]


def _extract_components(text: str, location: Optional[str]) -> List[str]:
    """Splits a compound need ('street lights with LED luminaires and batteries') into components."""
    cleaned = re.sub(r"(?:₹|rs\.?|inr|budget)\s*[\d,]+(?:\.\d+)?\s*(?:lakhs?|lacs?|crores?|cr|l|k)?", " ", text, flags=re.IGNORECASE)
    if location:
        cleaned = re.sub(re.escape(location), " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(rf"\b\d[\d,]*\s*(?:{UNIT_PATTERN})?\b(?!\s*(?:kv|v|volt|w|kw|grade|mm))", " ", cleaned, flags=re.IGNORECASE)

    components: List[str] = []
    for seg in _SPLIT_PATTERN.split(cleaned):
        seg = _NOISE_PATTERN.sub(" ", seg)
        seg = re.sub(r"\s+", " ", seg).strip(" .-:")
        if len(re.findall(r"[^\W\d_]{3,}", seg)) >= 1 and len(seg) >= 4:
            if seg.lower() not in (c.lower() for c in components):
                components.append(seg)
    return components[:6]


def parse_need(text: str) -> Dict[str, Any]:
    location = _parse_location(text)
    return {
        "quantity": _parse_quantity(text),
        "budget": _parse_budget(text),
        "location": location,
        "components": _extract_components(text, location),
        "brands_mentioned": _detect_brands(text),
    }
