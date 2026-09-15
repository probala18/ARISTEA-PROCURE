import sys
import os
import json
import csv
sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, r"c:\Users\BALASUNDAR M\Documents\SIH 2026")

from backend.app.core.normalizers import parse_standard_id, clean_text

# 1. Investigate standards.csv (234 rows)
csv_path = r"c:\Users\BALASUNDAR M\Documents\SIH 2026\csvfiles\standards.csv"
with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
    reader = csv.DictReader(f)
    std_csv_rows = list(reader)

print(f"Total rows in standards.csv: {len(std_csv_rows)}")

# Let's see what happened to each of the 234 rows
parsed_csv_map = {}
duplicate_csv_rows = []
skipped_csv_rows = []

for idx, row in enumerate(std_csv_rows):
    raw_id = row.get("standard_id")
    if not raw_id or not clean_text(raw_id):
        skipped_csv_rows.append((idx, row, "empty standard_id"))
        continue
    parsed = parse_standard_id(raw_id)
    if not parsed:
        skipped_csv_rows.append((idx, row, "unparseable standard_id"))
        continue
    cid = parsed["canonical_id"]
    if cid in parsed_csv_map:
        duplicate_csv_rows.append((idx, cid, row, parsed_csv_map[cid]))
    else:
        parsed_csv_map[cid] = (idx, row)

print(f"Unique canonical IDs in standards.csv: {len(parsed_csv_map)}")
print(f"Duplicate rows in standards.csv: {len(duplicate_csv_rows)}")
print(f"Skipped rows in standards.csv: {len(skipped_csv_rows)}")
for d in duplicate_csv_rows:
    print(f"  Duplicate row #{d[0]} (canonical: '{d[1]}') matches row #{d[3][0]}")

# 2. Investigate sample_standards.json (78 records)
json_path = r"c:\Users\BALASUNDAR M\Documents\SIH 2026\csvfiles\sample_standards.json"
with open(json_path, "r", encoding="utf-8") as f:
    sample_json_rows = json.load(f)

print(f"\nTotal records in sample_standards.json: {len(sample_json_rows)}")

# Let's see how sample_standards.json matches with standards.csv
overlapping_with_csv = []
unique_to_json = []

for idx, item in enumerate(sample_json_rows):
    raw_is = item.get("is_number")
    part = clean_text(item.get("part"))
    section = clean_text(item.get("section"))
    pub_year = item.get("year_of_publication")
    
    composed_id = raw_is
    if part:
        composed_id += f" (Part {part})"
    if section:
        composed_id += f"/Sec {section}"
    if pub_year:
        composed_id += f":{pub_year}"

    parsed = parse_standard_id(composed_id)
    cid = parsed["canonical_id"] if parsed else composed_id
    is_num = parsed["is_number"] if parsed else raw_is

    # Does it match any canonical ID or is_number in standards.csv?
    # In standards_importer:
    # std = ctx.session.query(Standard).filter(
    #     (Standard.standard_id == canonical_id) |
    #     (Standard.standard_id == is_number) |
    #     ((Standard.is_number == is_number) & (Standard.publication_year == pub_year)) |
    #     (Standard.is_number == is_number)
    # ).first()
    
    matched_csv_id = None
    if cid in parsed_csv_map:
        matched_csv_id = cid
    else:
        # Check if is_num matches any in parsed_csv_map
        for csv_cid in parsed_csv_map:
            csv_parsed = parse_standard_id(csv_cid)
            if csv_parsed and csv_parsed["is_number"] == is_num:
                matched_csv_id = csv_cid
                break

    if matched_csv_id:
        overlapping_with_csv.append((idx, is_num, cid, matched_csv_id))
    else:
        unique_to_json.append((idx, is_num, cid))

print(f"Records in sample_standards.json overlapping with standards.csv: {len(overlapping_with_csv)}")
print(f"Records unique to sample_standards.json: {len(unique_to_json)}")
print(f"\nExact arithmetic: 234 - {len(duplicate_csv_rows)} (duplicates in csv) = {len(parsed_csv_map)} standards from CSV.")
print(f"Then from sample_standards.json (78 total): {len(overlapping_with_csv)} enriched existing CSV standards + {len(unique_to_json)} new standards added.")
print(f"Total canonical standards = {len(parsed_csv_map)} + {len(unique_to_json)} = {len(parsed_csv_map) + len(unique_to_json)}")

