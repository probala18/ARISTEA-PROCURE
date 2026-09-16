import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from sqlalchemy.orm import sessionmaker
from backend.app.core.database import get_engine
from backend.app.models import Standard, StandardRelationship

@pytest.fixture(scope="module")
def db_session():
    engine = get_engine("sqlite:///./sih_bis.db")
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_canonical_standard_count_arithmetic(db_session):
    """
    Asserts exact standard count arithmetic:
    234 rows in standards.csv:
      - 4 duplicate rows merged (IS 13252 Pt 1, IS 1239 Pt 1)
      -> 230 unique standards from standards.csv
    78 records in sample_standards.json:
      - 40 overlapping records enrich existing standards with provenance
      - 38 new unique standards added
    Total canonical standards in DB = 230 + 38 = 268.
    """
    total_stds = db_session.query(Standard).count()
    assert total_stds == 268

    csv_stds = db_session.query(Standard).filter_by(source_file="standards.csv").count()
    json_stds = db_session.query(Standard).filter_by(source_file="sample_standards.json").count()
    assert csv_stds == 230
    assert json_stds == 38

def test_relationship_fk_resolution_metrics(db_session):
    """
    Asserts relationship FK resolution metrics:
    Total relationships: 111 (27 explicit + 84 derived)
    Resolved: 75 (67.57%)
    Unresolved: 36 (32.43%)
    """
    total = db_session.query(StandardRelationship).count()
    resolved = db_session.query(StandardRelationship).filter(StandardRelationship.target_standard_id.isnot(None)).count()
    unresolved = db_session.query(StandardRelationship).filter(StandardRelationship.target_standard_id.is_(None)).count()

    assert total == 111
    assert resolved == 75
    assert unresolved == 36
    assert round(resolved / total * 100, 1) == 67.6

def test_unresolved_relationships_classification(db_session):
    """
    Verifies classification of all 36 unresolved relationships:
    - Category A (Genuinely does not exist in supplied standards catalog): 11 items
    - Category B (Normalization failure): 0 items
    - Category C (Different part/section representation / series citation): 25 items
    - All 36 preserve verbatim target_standard_number and provenance.
    """
    all_stds = db_session.query(Standard).all()
    unresolved = db_session.query(StandardRelationship).filter(StandardRelationship.target_standard_id.is_(None)).all()
    assert len(unresolved) == 36

    cat_a = []
    cat_c = []

    for r in unresolved:
        assert r.target_standard_number is not None
        assert len(r.target_standard_number.strip()) > 0
        assert r.source_provenance is not None

        target = r.target_standard_number
        parts = [s for s in all_stds if s.is_number.startswith(target + " (Part") or s.standard_id.startswith(target + " (Part")]
        if parts:
            cat_c.append(r)
        else:
            cat_a.append(r)

    assert len(cat_c) == 25
    assert len(cat_a) == 11
