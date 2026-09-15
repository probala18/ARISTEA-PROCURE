import sys
import os
import json
import csv
sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, r"c:\Users\BALASUNDAR M\Documents\SIH 2026")

from backend.app.core.database import get_engine
from backend.app.models import Standard
from sqlalchemy.orm import sessionmaker

engine = get_engine("sqlite:///./sih_bis.db")
Session = sessionmaker(bind=engine)
session = Session()

try:
    total_stds = session.query(Standard).count()
    print(f"Total standards in DB: {total_stds}")
    
    # Check breakdown by source_file
    from collections import Counter
    source_files = Counter(s.source_file for s in session.query(Standard).all())
    print("Standards by source_file:", dict(source_files))
    
    # Check provenance sources
    prov_sources = Counter()
    for s in session.query(Standard).all():
        if s.source_provenance and "sources" in s.source_provenance:
            for src in s.source_provenance["sources"]:
                prov_sources[src.get("file")] += 1
        elif s.source_file:
            prov_sources[s.source_file] += 1
    print("Standards by provenance sources:", dict(prov_sources))

    # Let's inspect csvfiles/standards.csv and csvfiles/sample_standards.json
    csv_path = r"c:\Users\BALASUNDAR M\Documents\SIH 2026\csvfiles\standards.csv"
    with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        std_csv_rows = list(reader)
    print(f"\ncsvfiles/standards.csv total rows: {len(std_csv_rows)}")

    json_path = r"c:\Users\BALASUNDAR M\Documents\SIH 2026\csvfiles\sample_standards.json"
    with open(json_path, "r", encoding="utf-8") as f:
        sample_json_rows = json.load(f)
    print(f"csvfiles/sample_standards.json total records: {len(sample_json_rows)}")

    # Let's also check bis_standards.csv
    bis_path = r"c:\Users\BALASUNDAR M\Documents\SIH 2026\csvfiles\bis_standards.csv"
    with open(bis_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        bis_csv_rows = list(reader)
    print(f"csvfiles/bis_standards.csv total rows: {len(bis_csv_rows)}")

    # Let's check the user's mention of "bis_standards (234) + standards(1) (78)"
    # Where does 234 and 78 come from?
    # Could standards.csv have 234 rows and sample_standards have 78, or vice versa?
    print(f"standards.csv rows: {len(std_csv_rows)}")
    print(f"sample_standards.json items: {len(sample_json_rows)}")

finally:
    session.close()
