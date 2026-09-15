"""
Standard ID normalizer and shared data transformation utilities for PS 26108.

Handles:
- Standard number parsing and normalization (IS, IS/IEC, with/without space, parts, sections, years)
- Status normalization
- Whitespace / case cleanup / text sanitization
- Safe type conversions
- Relationship type mapping
- Certification type normalization
"""
import re
from typing import Optional, Dict, Any

def parse_standard_id(raw_id: str, assume_is_prefix: bool = True) -> Optional[Dict[str, Any]]:
    """Parse a raw standard identifier into structured canonical components.
    
    Handles:
    - 'IS 694:2010', 'IS694', 'IS 694'
    - 'IS 1 : 1968'
    - 'IS/IEC 60947: Part 2:2016' -> 'IS/IEC 60947 (Part 2):2016'
    - 'IS 15999 (Part 2/Sec 1)'
    - '4003 (Part 1):1978' (with assume_is_prefix=True)
    - '2028:2004'
    
    Returns dict with keys:
    - prefix: 'IS', 'IS/IEC', 'IS/ISO'
    - number: base numeric string e.g. '694'
    - part: part number string e.g. '1', '2'
    - section: section number string e.g. '1'
    - year: int or None
    - canonical_id: e.g. 'IS 12615:2018'
    - is_number: e.g. 'IS 12615'
    - raw: original raw string
    """
    if not raw_id or not str(raw_id).strip():
        return None
    
    raw = str(raw_id).strip()
    cleaned = re.sub(r'\s+', ' ', raw)
    
    # 1. Check for IS / IEC / ISO prefix
    prefix = None
    m_pref = re.match(r'^(IS\s*/\s*IEC|IS/ISO|IS)(?=[0-9\s:\-\./]|$)', cleaned, re.IGNORECASE)
    if m_pref:
        pref_str = m_pref.group(1).upper()
        if 'IEC' in pref_str:
            prefix = 'IS/IEC'
        elif 'ISO' in pref_str:
            prefix = 'IS/ISO'
        else:
            prefix = 'IS'
        rest = cleaned[m_pref.end():].strip(' :-\t\r\n')
    else:
        # If no IS prefix, check if it starts with digits
        if assume_is_prefix or re.match(r'^\d{2,6}(?:\b|[\s:\(])', cleaned):
            prefix = 'IS'
            rest = cleaned
        else:
            return {
                'prefix': None,
                'number': None,
                'part': None,
                'section': None,
                'year': None,
                'canonical_id': raw,
                'is_number': raw,
                'raw': raw,
            }

    # 2. Extract 4-digit publication year if present at the end
    year = None
    m_yr = re.search(r'[:\-]\s*(\d{4})\s*$', rest)
    if m_yr:
        year = int(m_yr.group(1))
        rest = rest[:m_yr.start()].strip()

    # 3. Match base number
    m_num = re.match(r'^(\d+)', rest)
    if not m_num:
        return {
            'prefix': prefix,
            'number': None,
            'part': None,
            'section': None,
            'year': year,
            'canonical_id': raw,
            'is_number': raw,
            'raw': raw,
        }
    
    number = m_num.group(1)
    sub = rest[m_num.end():].strip(' :-,()')
    
    part = None
    section = None
    if sub:
        # Match Part
        m_pt = re.search(r'(?:Part|Pt\.?)\s*(\d+)', sub, re.IGNORECASE)
        if m_pt:
            part = m_pt.group(1)
        # Match Section
        m_sec = re.search(r'(?:Sec(?:tion|\.?)?)\s*(\d+)', sub, re.IGNORECASE)
        if m_sec:
            section = m_sec.group(1)
            
    # Build standard number (is_number) without year
    is_number = f'{prefix} {number}'
    if part and section:
        is_number += f' (Part {part}/Sec {section})'
    elif part:
        is_number += f' (Part {part})'
    elif section:
        is_number += f' (Sec {section})'
        
    canonical_id = is_number
    if year:
        canonical_id += f':{year}'
        
    return {
        'prefix': prefix,
        'number': number,
        'part': part,
        'section': section,
        'year': year,
        'canonical_id': canonical_id,
        'is_number': is_number,
        'raw': raw,
    }


def normalize_standard_id(raw_id: str, assume_is_prefix: bool = True) -> str:
    """Return canonical standard_id string from raw input."""
    parsed = parse_standard_id(raw_id, assume_is_prefix=assume_is_prefix)
    if parsed:
        return parsed['canonical_id']
    return str(raw_id).strip() if raw_id else ''


def extract_is_number(raw_id: str, assume_is_prefix: bool = True) -> str:
    """Return is_number (without year) from raw input."""
    parsed = parse_standard_id(raw_id, assume_is_prefix=assume_is_prefix)
    if parsed:
        return parsed['is_number']
    return str(raw_id).strip() if raw_id else ''


# ──────────────────────────────────────────────
# Status Normalization
# ──────────────────────────────────────────────

_STATUS_MAP = {
    'active': 'CURRENT',
    'current': 'CURRENT',
    'valid': 'CURRENT',
    'superseded': 'SUPERSEDED',
    'obsolete': 'SUPERSEDED',
    'withdrawn': 'SUPERSEDED',
    'revised': 'SUPERSEDED',
}

def normalize_status(raw_status: str) -> str:
    """Normalize standard status to CURRENT or SUPERSEDED."""
    if not raw_status:
        return 'CURRENT'
    cleaned = clean_text(str(raw_status))
    if not cleaned:
        return 'CURRENT'
    return _STATUS_MAP.get(cleaned.lower(), cleaned.upper())


# ──────────────────────────────────────────────
# Relationship Type Mapping
# ──────────────────────────────────────────────

_REL_TYPE_MAP = {
    'testing_standards': 'TESTING',
    'safety_standards': 'SAFETY',
    'performance_standards': 'PERFORMANCE',
    'supersedes': 'SUPERSEDES',
    'superseded_by': 'SUPERSEDES',
    'superseded_by_current': 'SUPERSEDES',
    'allied_systems': 'ALLIED',
    'allied_standards': 'ALLIED',
    'subcomponent_standards': 'SUBCOMPONENT',
    'normative_references': 'NORMATIVE_REFERENCE',
    'normative_reference': 'NORMATIVE_REFERENCE',
    'installation': 'INSTALLATION',
    'terminology': 'TERMINOLOGY',
    'related_product': 'RELATED_PRODUCT',
    'application': 'APPLICATION',
    'requires_testing': 'TESTING',
    'requires_safety': 'SAFETY',
    'performance_rating': 'PERFORMANCE',
    'efficiency_verification': 'PERFORMANCE',
    'installation_safety': 'INSTALLATION',
    'vfd_application': 'APPLICATION',
}

def normalize_relationship_type(raw_type: str) -> str:
    """Normalize relationship type label to canonical enum string."""
    if not raw_type:
        return 'OTHER'
    cleaned = str(raw_type).strip().lower().replace('-', '_').replace(' ', '_')
    return _REL_TYPE_MAP.get(cleaned, cleaned.upper())


# ──────────────────────────────────────────────
# Text Cleanup & Safe Types
# ──────────────────────────────────────────────

def clean_text(value: Any) -> Optional[str]:
    """Normalize whitespace and strip BOM / encoding artifacts."""
    if value is None:
        return None
    s = str(value)
    # Remove BOM and common encoding artifacts
    cleaned = (
        s.replace('\ufeff', '')
        .replace('\ufffd', '')
        .replace('Ã¯Â¿Â½', '')
        .replace('\u2013', '-')
        .replace('\u2014', '-')
        .strip()
    )
    # Collapse multiple whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned if cleaned else None


def safe_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    """Safely convert to int."""
    if value is None:
        return default
    try:
        # Handle string floats like '2018.0'
        return int(float(str(value).strip()))
    except (ValueError, TypeError):
        return default


def safe_bool(value: Any, default: Optional[bool] = None) -> Optional[bool]:
    """Safely convert to bool."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    if s in ('true', '1', 'yes', 'y', 't', 'mandatory'):
        return True
    if s in ('false', '0', 'no', 'n', 'f', 'voluntary'):
        return False
    return default


def normalize_certification_type(raw: Any) -> Optional[str]:
    """Normalize certification scheme / type labels."""
    if not raw:
        return None
    cleaned = clean_text(raw)
    if not cleaned:
        return None
    upper = cleaned.upper()
    if 'ISI' in upper or 'SCHEME-I' in upper or 'SCHEME I' in upper:
        if 'CRS' not in upper:
            return 'BIS_ISI'
    if 'CRS' in upper or 'SCHEME-II' in upper or 'SCHEME II' in upper:
        return 'CRS'
    if 'HALLMARK' in upper:
        return 'HALLMARKING'
    if 'SCHEME-IV' in upper or 'SCHEME IV' in upper or 'CODE OF PRACTICE' in upper:
        return 'CODE_OF_PRACTICE'
    return cleaned
