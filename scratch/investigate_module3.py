import sys
import os
import json
sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, r"c:\Users\BALASUNDAR M\Documents\SIH 2026")

from sqlalchemy.orm import sessionmaker
from backend.app.core.database import get_engine
from backend.app.models import Standard, StandardRelationship
from backend.app.core.normalizers import parse_standard_id

engine = get_engine("sqlite:///./sih_bis.db")
Session = sessionmaker(bind=engine)
session = Session()

try:
    total_rel = session.query(StandardRelationship).count()
    resolved_rel = session.query(StandardRelationship).filter(StandardRelationship.target_standard_id.isnot(None)).all()
    unresolved_rel = session.query(StandardRelationship).filter(StandardRelationship.target_standard_id.is_(None)).all()
    
    print(f"Total relationships: {total_rel}")
    print(f"Resolved: {len(resolved_rel)}")
    print(f"Unresolved: {len(unresolved_rel)}")
    print(f"Resolution percentage: {len(resolved_rel)/total_rel*100:.2f}%\n")
    
    all_standards = session.query(Standard).all()
    all_std_ids = {s.standard_id: s for s in all_standards}
    all_is_numbers = {s.is_number: s for s in all_standards}
    
    print(f"Total canonical standards in DB: {len(all_standards)}")
    
    # Check each unresolved relationship
    print("--- INVESTIGATING UNRESOLVED RELATIONSHIPS ---")
    unresolved_list = []
    
    for r in unresolved_rel:
        src = session.query(Standard).filter_by(id=r.source_standard_id).first()
        src_id = src.standard_id if src else "Unknown"
        target_raw = r.target_standard_number
        parsed = parse_standard_id(target_raw)
        
        # Check if matches exist anywhere
        # 1. Check in all_std_ids or all_is_numbers
        found_id = None
        found_reason = None
        
        # Does any standard contain target_raw or part of it?
        matching_stds = []
        for s in all_standards:
            # Check substrings or normalized versions
            if target_raw.lower() in s.standard_id.lower() or target_raw.lower() in s.title.lower():
                matching_stds.append(s.standard_id)
            elif parsed and parsed['is_number'].lower() == s.is_number.lower():
                matching_stds.append(s.standard_id)
                
        unresolved_list.append({
            "id": r.id,
            "source": src_id,
            "source_dataset": r.source_dataset,
            "relation_type": r.relationship_type,
            "target_raw": target_raw,
            "parsed": parsed,
            "matching_stds_in_db": matching_stds
        })
        
        print(f"[{r.source_dataset}] ({src_id}) --[{r.relationship_type}]--> '{target_raw}' | Parsed: {parsed} | Possible matches in DB: {matching_stds}")

    # Now let's check all 12 dataset files to see if any of these target_raw appear anywhere in the raw data files!
    data_dir = r"c:\Users\BALASUNDAR M\Documents\SIH 2026"
    raw_files = [
        "bis_standards.csv",
        "bis_standards.json",
        "certification.csv",
        "manifest.json",
        "productlicence.csv",
        "query_dataset.json",
        "relationships(1).json",
        "ReportExcel.csv",
        "sample_standards.json",
        "schem.csv",
        "standards(1).csv",
        "upcomming.csv"
    ]
    
    print("\n--- CHECKING RAW DATASET FILES FOR UNRESOLVED TARGETS ---")
    raw_file_contents = {}
    for rf in raw_files:
        p = os.path.join(data_dir, rf)
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                raw_file_contents[rf] = f.read()

    for item in unresolved_list:
        target = item["target_raw"]
        target_clean = target.replace(" ", "")
        files_found = []
        for rf, content in raw_file_contents.items():
            if target in content or (len(target) > 4 and target_clean in content.replace(" ", "")):
                files_found.append(rf)
        item["files_found_in"] = files_found

    with open("scratch/unresolved_detailed_audit.json", "w", encoding="utf-8") as f:
        json.dump(unresolved_list, f, indent=2)

    print("\nSaved detailed audit to scratch/unresolved_detailed_audit.json")

finally:
    session.close()
