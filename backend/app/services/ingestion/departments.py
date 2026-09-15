"""
Helper for managing Department and Technical Committee entities during ingestion.
"""
import re
from typing import Optional
from backend.app.models.department import Department
from backend.app.services.ingestion.context import IngestionContext
from backend.app.core.normalizers import clean_text

def parse_department_string(dept_str: str):
    """Parse 'ETD 15 (Rotating Machinery)' into code='ETD 15', name='Rotating Machinery'."""
    if not dept_str:
        return None, None
    s = clean_text(dept_str)
    if not s:
        return None, None

    m = re.match(r'^([A-Za-z]+\s*\d+)(?:\s*\((.*?)\))?$', s)
    if m:
        code = re.sub(r'\s+', ' ', m.group(1).upper()).strip()
        name = m.group(2).strip() if m.group(2) else code
        return code, name

    # Fallback: check if standard committee code pattern
    m2 = re.match(r'^([A-Za-z]+[-_ ]?\d+)', s)
    if m2:
        code = m2.group(1).upper().replace('-', ' ').replace('_', ' ')
        code = re.sub(r'\s+', ' ', code).strip()
        rest = s[m2.end():].strip(' ()-:')
        name = rest if rest else code
        return code, name

    return s.upper()[:50], s


def get_or_create_department(raw_dept: str, ctx: IngestionContext, ministry: Optional[str] = None) -> Optional[int]:
    """Get or create Department entity and return its primary key ID."""
    if not raw_dept:
        return None

    code, name = parse_department_string(raw_dept)
    if not code:
        return None

    # Check cache
    if code in ctx.department_code_map:
        return ctx.department_code_map[code]

    # Query DB
    dept = ctx.session.query(Department).filter_by(code=code).first()
    if dept:
        if name and dept.name == dept.code and name != code:
            dept.name = name
        if ministry and not dept.ministry:
            dept.ministry = ministry
        ctx.department_code_map[code] = dept.id
        return dept.id

    # Create new
    dept = Department(
        code=code,
        name=name or code,
        ministry=ministry,
        description=f"Technical Committee {code}",
    )
    ctx.session.add(dept)
    ctx.session.flush()
    ctx.department_code_map[code] = dept.id
    ctx.stats.departments_created += 1
    return dept.id
