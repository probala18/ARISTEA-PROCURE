import json

transcript_path = r"C:\Users\BALASUNDAR M\.gemini\antigravity-ide\brain\19bbda88-3e1f-40ff-bd7a-7039d747026c\.system_generated\logs\transcript_full.jsonl"

with open(transcript_path, "r", encoding="utf-8") as f:
    first_line = f.readline()
    data = json.loads(first_line)
    content = data.get("content", "")

lines = content.splitlines()

# Search for section headers like "= 1" or "= 2" etc.
with open("scratch/all_sections.txt", "w", encoding="utf-8") as out:
    for idx, line in enumerate(lines):
        if line.startswith("=") and idx + 1 < len(lines) and lines[idx+1].strip():
            header = lines[idx+1].strip()
            out.write(f"Line {idx}: {header}\n")

print("Wrote sections to scratch/all_sections.txt")
