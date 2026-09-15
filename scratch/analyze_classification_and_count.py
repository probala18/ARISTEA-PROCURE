import sys
import os
import json
import csv
sys.stdout.reconfigure(encoding='utf-8')

# 1. Investigate standards count
data_dir = r"c:\Users\BALASUNDAR M\Documents\SIH 2026"

# Load bis_standards.csv
bis_csv_path = os.path.join(data_dir, "bis_standards.csv")
bis_rows = []
with open(bis_csv_path, mode="r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for r in reader:
        bis_rows.append(r)

# Load standards(1).csv
std1_csv_path = os.path.join(data_dir, "standards(1).csv")
std1_rows = []
with open(std1_csv_path, mode="r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for r in reader:
        std1_rows.append(r)

print(f"bis_standards.csv row count: {len(bis_rows)}")
print(f"standards(1).csv row count: {len(std1_rows)}")

# Also check bis_standards.json and sample_standards.json
sample_path = os.path.join(data_dir, "sample_standards.json")
with open(sample_path, "r", encoding="utf-8") as f:
    sample_data = json.load(f)
print(f"sample_standards.json record count: {len(sample_data)}")

# Let's inspect how standards_importer imports them
# Let's check unique standard IDs in each file
from backend.app.core.normalizers import parse_standard_id

def get_parsed_key(raw_str):
    p = parse_standard_id(raw_str)
    if p:
        return p['canonical_id'], p['is_number']
    return raw_str.strip(), raw_str.strip()

bis_keys = set()
for r in bis_rows:
    raw = r.get("Standard_ID") or r.get("Standard Number") or r.get("Standard") or ""
    bis_keys.add(raw.strip())

std1_keys = set()
for r in std1_rows:
    raw = r.get("Standard_ID") or r.get("Standard Number") or r.get("Standard") or r.get("IS_Number") or ""
    # Check all fields
    for col in ["Standard Number", "Standard_ID", "IS_Number", "StandardNumber"]:
        if col in r and r[col]:
            raw = r[col]
            break
    std1_keys.add(raw.strip())

sample_keys = set()
for s in sample_data:
    raw = s.get("standard_number") or s.get("standard_id") or ""
    sample_keys.add(raw.strip())

print(f"Unique keys in bis_standards.csv: {len(bis_keys)}")
print(f"Unique keys in standards(1).csv: {len(std1_keys)}")
print(f"Unique keys in sample_standards.json: {len(sample_keys)}")

# Overlap between bis_standards and standards(1)
overlap_exact = bis_keys.intersection(std1_keys)
print(f"Exact key overlap between bis_standards and standards(1): {len(overlap_exact)}")

# Normalized overlap
bis_canon = {get_parsed_key(k)[0] for k in bis_keys if k}
std1_canon = {get_parsed_key(k)[0] for k in std1_keys if k}
sample_canon = {get_parsed_key(k)[0] for k in sample_keys if k}

print(f"Canonical IDs in bis_standards: {len(bis_canon)}")
print(f"Canonical IDs in standards(1): {len(std1_canon)}")
print(f"Canonical IDs in sample_standards: {len(sample_canon)}")

overlap_canon = bis_canon.intersection(std1_canon)
print(f"Canonical overlap between bis_standards and standards(1): {len(overlap_canon)}")
print(f"Union of bis_standards and standards(1) canonical IDs: {len(bis_canon.union(std1_canon))}")
print(f"Union of all three (bis + std1 + sample): {len(bis_canon.union(std1_canon).union(sample_canon))}")

