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
    with open("scratch/classification_result.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    print("=== EXAMINING CATEGORY C ITEMS ===")
    for item in data["C"]:
        rel = session.query(StandardRelationship).get(item["id"])
        print(f"ID {item['id']}: Source: {item['source']} -> Target: '{item['target']}' | Type: {item['type']} | Dataset: {item['dataset']}")
        print(f"   Provenance: {rel.source_provenance}")
        print(f"   Parts in DB: {item['parts_in_db']}")
        print()

finally:
    session.close()
