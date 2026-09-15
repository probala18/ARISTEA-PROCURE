import sys
import os
import json
sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, r"c:\Users\BALASUNDAR M\Documents\SIH 2026")

from backend.app.core.database import get_engine
from backend.app.models import Standard, StandardRelationship
from sqlalchemy.orm import sessionmaker

engine = get_engine("sqlite:///./sih_bis.db")
Session = sessionmaker(bind=engine)
session = Session()

try:
    all_stds = session.query(Standard).all()
    # Build various lookup maps
    by_std_id = {s.standard_id: s for s in all_stds}
    by_is_num = {}
    for s in all_stds:
        by_is_num.setdefault(s.is_number, []).append(s)
    
    unresolved = session.query(StandardRelationship).filter(StandardRelationship.target_standard_id.is_(None)).all()
    print(f"Total unresolved: {len(unresolved)}")
    
    categorized = {
        "A": [],  # Target genuinely does not exist in any supplied dataset
        "B": [],  # Target exists but standard-ID normalization failed
        "C": [],  # Target exists under a different part/section representation
        "D": [],  # Target is present only as a textual relationship and cannot be resolved from supplied data
        "E": [],  # Other data-quality issue
    }
    
    # Read raw files to check existence anywhere in datasets
    data_dir = r"c:\Users\BALASUNDAR M\Documents\SIH 2026\csvfiles"
    raw_files = [f for f in os.listdir(data_dir) if f.endswith(('.csv', '.json'))]
    file_contents = {}
    for rf in raw_files:
        with open(os.path.join(data_dir, rf), "r", encoding="utf-8", errors="ignore") as f:
            file_contents[rf] = f.read()

    for r in unresolved:
        src = session.query(Standard).get(r.source_standard_id)
        src_str = src.standard_id if src else str(r.source_standard_id)
        target = r.target_standard_number
        
        # Check if target is base IS number of an existing multi-part standard (Category C)
        # e.g., target is 'IS 2386', but DB has 'IS 2386 (Part 1):1963', 'IS 2386 (Part 4):1963'
        # Or target is 'IS 101', DB has 'IS 101 (Part 1/Sec 1):1986'
        parts_in_db = [s.standard_id for s in all_stds if s.is_number.startswith(target + " (Part") or s.standard_id.startswith(target + " (Part")]
        
        # Check if target matches exactly if we normalize differently (Category B)
        # Check if target appears anywhere in raw files as a defined standard
        in_datasets = [fn for fn, content in file_contents.items() if target in content]
        
        item_info = {
            "id": r.id,
            "source": src_str,
            "target": target,
            "type": r.relationship_type,
            "dataset": r.source_dataset,
            "parts_in_db": parts_in_db,
            "found_in_files": in_datasets
        }
        
        if parts_in_db:
            # Target is a series/base standard cited generally without part number, whereas DB stores specific parts
            categorized["C"].append(item_info)
        elif not any(target in fc for fc in file_contents.values()):
            categorized["A"].append(item_info)
        else:
            # It appears in file_contents, but does it exist as a defined standard entity, or only as a citation / text?
            # Let's check if it exists in standards.csv or sample_standards.json as a primary entry
            exists_as_primary = False
            for s in all_stds:
                if target.lower() == s.standard_id.lower() or target.lower() == s.is_number.lower():
                    exists_as_primary = True
                    break
            
            if exists_as_primary:
                categorized["B"].append(item_info)
            else:
                # Is it only mentioned in relationships.json or sample_standards normative_references, but not defined as a standard?
                # Check if it appears in certification.csv, schem.csv etc.
                categorized["A"].append(item_info)

    print("\n--- CLASSIFICATION SUMMARY ---")
    for cat, items in categorized.items():
        print(f"Category {cat}: {len(items)} items")

    print("\n--- CATEGORY C (Different part/section representation) ---")
    for it in categorized["C"]:
        print(f"  Target: '{it['target']}' cited by {it['source']} -> Parts in DB: {it['parts_in_db']}")

    print("\n--- CATEGORY A (Target standard genuinely does not exist in any supplied dataset) ---")
    for it in categorized["A"]:
        print(f"  Target: '{it['target']}' cited by {it['source']} ({it['dataset']}) -> Appears in: {it['found_in_files']}")

    with open("scratch/classification_result.json", "w", encoding="utf-8") as f:
        json.dump(categorized, f, indent=2)

finally:
    session.close()
