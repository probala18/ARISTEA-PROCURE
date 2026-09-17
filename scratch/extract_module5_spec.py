import json

transcript_path = r"C:\Users\BALASUNDAR M\.gemini\antigravity-ide\brain\19bbda88-3e1f-40ff-bd7a-7039d747026c\.system_generated\logs\transcript_full.jsonl"

with open(transcript_path, "r", encoding="utf-8") as f:
    first_line = f.readline()
    data = json.loads(first_line)
    content = data.get("content", "")
    
# Let's search for "Module 5" or "5." in content
lines = content.splitlines()
print(f"Total lines in master prompt: {len(lines)}")
for idx, line in enumerate(lines):
    if "module 5" in line.lower() or "module 6" in line.lower() or "module 7" in line.lower():
        print(f"Line {idx}: {line}")
        # print surrounding 15 lines
        for j in range(max(0, idx - 2), min(len(lines), idx + 25)):
            print(f"   [{j}] {lines[j]}")
        print("="*60)
